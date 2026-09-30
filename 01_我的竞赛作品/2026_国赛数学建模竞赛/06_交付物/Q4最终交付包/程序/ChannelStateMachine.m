% ========================================================================
% ChannelStateMachine -- 频道状态管理
% 每个频道一个状态：undiscovered -> located -> cleared / confirmed_empty（单调推进）。
% "已确认空"的定义：该频道在全部检测点都测到 no_signal -- 这是定理 C 的判空依据。
% ========================================================================

classdef ChannelStateMachine < handle
    properties
        n_channels          % 频道总数 (20)
        n_positions         % 检测点总数
        state               % 频道状态
        no_signal_positions % 每频道已确认 no_signal 的检测点 id 集合（按 id 去重）
        observations        % 每频道的观测记录 (cell array)
    end

    methods
        %% 构造函数
        function obj = ChannelStateMachine(n_channels, n_positions)
            obj.n_channels = n_channels;
            obj.n_positions = n_positions;

            % 初始化状态
            obj.state = repmat({'undiscovered'}, n_channels, 1);
            obj.no_signal_positions = cell(n_channels, 1);
            obj.observations = cell(n_channels, 1);
            for i = 1:n_channels
                obj.observations{i} = [];
            end
        end

        %% 更新频道状态
        function update(obj, channel, position_id, measure_result, result_data, position)
            switch measure_result
                case 'no_signal'
                    % 按检测点 id 去重（同一点重复测量不再累加）
                    prev = obj.no_signal_positions{channel};
                    obj.no_signal_positions{channel} = unique([prev(:); position_id]);

                    % 全部不同的检测点都 no_signal -> 已确认空
                    if numel(obj.no_signal_positions{channel}) >= obj.n_positions
                        obj.state{channel} = 'confirmed_empty';
                    end

                case {'direction', 'near'}
                    % 发现信号
                    if strcmp(obj.state{channel}, 'undiscovered')
                        obj.state{channel} = 'located';
                    end

                    % 存储观测记录
                    if isfield(result_data, 'svd_deg')
                        obs = struct(...
                            'position_id', position_id, ...
                            'position', position, ...
                            'channel', channel, ...
                            'svd_deg', result_data.svd_deg);
                        obj.observations{channel} = [obj.observations{channel}; obs];
                    end
            end
        end

        %% 标记频道已清除
        function mark_cleared(obj, channel)
            obj.state{channel} = 'cleared';
        end

        %% 检查频道是否已清除
        function cleared = is_cleared(obj, channel)
            cleared = strcmp(obj.state{channel}, 'cleared');
        end

        %% 检查频道是否已确认空
        function empty = is_confirmed_empty(obj, channel)
            empty = strcmp(obj.state{channel}, 'confirmed_empty');
        end

        %% 检查是否有两个及以上观测（可交会定位）
        function has_two = has_two_observations(obj, channel)
            has_two = length(obj.observations{channel}) >= 2;
        end

        %% 获取频道的观测记录
        function obs = get_observations(obj, channel)
            obs = obj.observations{channel};
        end

        %% 检查完备性（定理 C）
        function [complete, stats] = check_completeness(obj)
            cleared = 0;
            confirmed_empty = 0;
            remaining = 0;

            for ch = 1:obj.n_channels
                if strcmp(obj.state{ch}, 'cleared')
                    cleared = cleared + 1;
                elseif strcmp(obj.state{ch}, 'confirmed_empty')
                    confirmed_empty = confirmed_empty + 1;
                else
                    remaining = remaining + 1;
                end
            end

            complete = (remaining == 0);
            stats = struct(...
                'cleared', cleared, ...
                'confirmed_empty', confirmed_empty, ...
                'remaining', remaining);
        end
    end
end
