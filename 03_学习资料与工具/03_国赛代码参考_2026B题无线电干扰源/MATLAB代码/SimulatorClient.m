% SimulatorClient -- 模拟器 HTTP 客户端
% 封装与模拟器的全部 HTTP 通信（4 条指令的唯一咽喉），负责三件事：
%   1. 自记录日志（JSONL）：附件1 / 附件2 要求机器狗程序自留指令序列与响应；
%      在此统一落盘，任何调用方自动全覆盖。
%   2. 双检查：附件2 要求同时检查 HTTP 状态码与 accepted，不能只判其一。
%   3. 重试口径：只有网络超时/连接中断才复用原 request_id 与原内容重试；

classdef SimulatorClient < handle
    properties
        base_url            % 模拟器基础URL
        robot_id            % 机器狗ID（队号）
        request_counter     % 请求计数器
        virtual_time        % 当前虚拟时间 [s]
        remaining_time      % 剩余现实时间 [s]
        timeout             % 单次请求超时 [s]
        max_retries         % 最大重试次数（仅用于传输层失败）
        enter_wait_s        % /enter 等待接口开放的预算 [s]
        enter_retry_interval_s  % 两次 /enter 尝试之间的间隔 [s]
        t_enter_wall        % /enter 的墙钟计时器句柄
        elapsed_wall        % /enter -> 现在 的墙钟秒数（表 1 第 4 列用）
        log_dir             % 日志目录（由本文件位置推导，不用 cwd 相对路径）
        log_path            % 本次会话的日志文件全路径（JSONL）
        log_seq             % 日志记录序号
        last_pos            % 机器狗上一次合法动作的落点 [x y]（初始 (0,0)，附件2）
        n_measure           % /measure 成功次数（本地计数，供 Q4 指标导出）
        n_clear             % /clear 成功次数
        n_switch            % 频道切换次数（相邻两次合法 /measure 频道不同）
        cur_channel         % 测向机当前频道（初始 1）
        clear_action_s      % /clear 动作本身累计耗时（未发现 3 / 成功 5；供 T_vir 四分解）
        web_opts            % 缓存的 weboptions（每次请求新建它是纯开销）
    end

    methods
        %% 构造函数
        % 第三个参数可选：覆盖日志目录（仅供离线自测重定向用；正式运行不要传）
        function obj = SimulatorClient(base_url, robot_id, log_dir_override)
            obj.base_url = base_url;
            obj.robot_id = robot_id;
            obj.request_counter = 0;
            obj.virtual_time = 0;
            obj.remaining_time = 1200;  % 初始化为最大值（/enter 成功后会以模拟器返回值为准）
            obj.timeout = 10;
            obj.max_retries = 3;
            obj.enter_wait_s = 90;              % /enter 最多等 90 s（足够覆盖 5 s 倒计时 + 抖动）
            obj.enter_retry_interval_s = 2;     % 每 2 s 试一次
            obj.t_enter_wall = [];
            obj.elapsed_wall = 0;
            % 位置与请求计数（附件2：初始位置 (0,0)、测向机初始频道 1）
            obj.last_pos = [0, 0];
            obj.cur_channel = 1;
            obj.n_measure = 0;
            obj.n_clear = 0;
            obj.n_switch = 0;
            obj.clear_action_s = 0;
            % 缓存的请求选项：Q4 一局约 700~900 次请求，每次新建 weboptions 是纯开销
            obj.web_opts = weboptions(...
                'RequestMethod', 'post', ...
                'MediaType', 'application/json', ...
                'Timeout', obj.timeout);

            % 日志目录由本文件所在目录推导，不依赖当前工作目录
            if nargin >= 3 && ~isempty(log_dir_override)
                obj.log_dir = log_dir_override;
            else
                this_dir = fileparts(mfilename('fullpath'));
                obj.log_dir = fullfile(this_dir, 'logs');
            end
            if ~exist(obj.log_dir, 'dir')
                mkdir(obj.log_dir);
            end
            obj.log_seq = 0;
            stamp = datestr(now, 'yyyymmdd_HHMMSS');
            obj.log_path = fullfile(obj.log_dir, sprintf('robot_%s_%s.jsonl', ...
                regexprep(obj.robot_id, '[^\w\-]', '_'), stamp));
            obj.log_record('session_start', struct(...
                'base_url', obj.base_url, ...
                'robot_id', obj.robot_id, ...
                'note', 'robot-side self log (附件1 / 附件2)'));
            fprintf('[日志] 本局自记录日志: %s\n', obj.log_path);
        end

        %% /enter - 进入测试
        %  接口只在倒计时结束后开放（附件1），而 MATLAB 启动约 40 s、倒计时只 5 s
        %  -> 按附件2：payload 只构造一次，在 enter_wait_s 预算内反复重试直到被接受
        %  （复用同一 request_id 与原内容）。业务/协议拒绝不等待，立刻抛。
        function resp = enter(obj)
            payload = struct(...
                'arena_id', 'default', ...
                'robot_id', obj.robot_id, ...
                'request_id', obj.new_request_id);   % <- 只生成一次，全程复用

            t_start = tic;
            t_last_report = 0;      % 限流打印：每 15 s 报一次，避免批量连跑刷屏
            while true
                try
                    resp = obj.send_request('/enter', payload);   % 内部已含传输层重试
                    obj.update_time(resp);
                    % 记录墙钟起点：表 1 第 4 列程序运行时间= /enter -> 结束
                    obj.t_enter_wall = tic;
                    obj.elapsed_wall = 0;
                    if toc(t_start) > 1
                        fprintf('[SimulatorClient] /enter 等待 %.1f s 后成功\n', toc(t_start));
                    end
                    return;

                catch ME
                    if ~strcmp(ME.identifier, 'SimulatorClient:transport')
                        rethrow(ME);   % 业务/协议拒绝 -> 配置问题，等下去没有意义
                    end
                    el = toc(t_start);
                    if el >= obj.enter_wait_s
                        error('SimulatorClient:enterTimeout', ...
                            ['/enter 等待 %.0f s 仍失败 -- 模拟器接口未开放或未启动。\n' ...
                             '  请确认：① 模拟器已启动并联网登录；② 已点开始测试且 5 秒倒计时已结束；\n' ...
                             '  ③ 端口未被占用（默认 2026）。\n  最后错误: %s'], ...
                            obj.enter_wait_s, ME.message);
                    end
                    if el - t_last_report >= 15
                        t_last_report = el;
                        fprintf(['[SimulatorClient] 等待接口开放… 已等 %.0f s / %.0f s' ...
                                 '（复用同一 request_id 重试）\n'], el, obj.enter_wait_s);
                    end
                    pause(obj.enter_retry_interval_s);
                end
            end
        end

        %% 墙钟耗时（现实时间）
        function s = wall_clock_s(obj)
            if isempty(obj.t_enter_wall)
                s = 0;
            else
                s = toc(obj.t_enter_wall);
                obj.elapsed_wall = s;
            end
        end

        %% /measure - 检测
        function resp = measure(obj, x, y, channel)
            % 输入检查
            if ~isfinite(x) || ~isfinite(y) || abs(x) > 2e6 || abs(y) > 2e6
                error('坐标无效: (%.2f, %.2f)', x, y);
            end
            if channel < 1 || channel > 20 || mod(channel, 1) ~= 0
                error('频道无效: %d', channel);
            end

            payload = struct(...
                'arena_id', 'default', ...
                'robot_id', obj.robot_id, ...
                'request_id', obj.new_request_id, ...
                'position', struct('x', x, 'y', y), ...
                'channel', channel);

            resp = obj.send_request('/measure', payload);
            obj.update_time(resp);
            % 合法动作才更新落点/频道（附件2）；send_request 已保证 accepted=true
            obj.n_measure = obj.n_measure + 1;
            if channel ~= obj.cur_channel
                obj.n_switch = obj.n_switch + 1;
                obj.cur_channel = channel;
            end
            obj.last_pos = [x, y];
        end

        %% /clear - 清除
        function resp = clear(obj, x, y, channel)
            % 输入检查
            if ~isfinite(x) || ~isfinite(y) || abs(x) > 2e6 || abs(y) > 2e6
                error('坐标无效: (%.2f, %.2f)', x, y);
            end
            if channel < 1 || channel > 20 || mod(channel, 1) ~= 0
                error('频道无效: %d', channel);
            end

            payload = struct(...
                'arena_id', 'default', ...
                'robot_id', obj.robot_id, ...
                'request_id', obj.new_request_id, ...
                'position', struct('x', x, 'y', y), ...
                'channel', channel);

            resp = obj.send_request('/clear', payload);
            obj.update_time(resp);
            obj.n_clear = obj.n_clear + 1;      % /clear 不切换频道（附件2）
            obj.last_pos = [x, y];
            % 清除动作本身的耗时（附件2）：未发现 3 s / 成功 5 s。
            % 有了它，主程序才能把 T_vir 拆成 移动 / 检测 / 切频 / 清除 四项。
            if isstruct(resp) && isfield(resp, 'clear_result') && ...
                    strcmp(resp.clear_result, 'success')
                obj.clear_action_s = obj.clear_action_s + 5;
            else
                obj.clear_action_s = obj.clear_action_s + 3;
            end
        end

        %% /exit - 退出测试
        function resp = exit(obj)
            payload = struct(...
                'arena_id', 'default', ...
                'robot_id', obj.robot_id, ...
                'request_id', obj.new_request_id);

            resp = obj.send_request('/exit', payload);
        end

        %% 生成新的请求ID
        function req_id = new_request_id(obj)
            obj.request_counter = obj.request_counter + 1;
            req_id = sprintf('req_%d_%s', obj.request_counter, ...
                char(java.util.UUID.randomUUID.toString));
        end

        %% 发送 HTTP 请求（含传输层重试、双检查、逐次落盘）
        %  重试口径（附件2）：传输层失败 -> 复用原 payload 与原 request_id 重试；
        %  已收到 HTTP 响应（200 或 4xx/5xx）-> 一律不重试。
        function resp = send_request(obj, endpoint, payload)
            url = [obj.base_url, endpoint];
            last_msg = '';

            for attempt = 1:obj.max_retries
                http_status = [];
                resp = [];
                transport_err = '';
                err_id = '';
                try
                    resp = webwrite(url, payload, obj.web_opts);
                    http_status = 200;   % webwrite 不抛即 2xx；赛题只定义 200 为成功

                catch ME
                    err_id = obj.ident_of(ME);
                    code = obj.status_of(ME);
                    if ~isempty(code)
                        % 已收到 HTTP 响应（400/404/405/409/413/415/429/500）
                        http_status = code;
                        resp = obj.body_of(ME);
                        transport_err = '';
                    else
                        % 传输层失败：可复用原 ID 重试
                        transport_err = ME.message;
                    end
                    last_msg = ME.message;
                end

                accepted = isstruct(resp) && isfield(resp, 'accepted') && isequal(resp.accepted, true);
                obj.log_record('request', struct(...
                    'endpoint', endpoint, ...
                    'attempt', attempt, ...
                    'request_id', obj.get_field(payload, 'request_id'), ...
                    'request_payload', payload, ...
                    'response_payload', resp, ...
                    'http_status', http_status, ...
                    'response_received', obj.is_http_status(http_status), ...
                    'accepted', accepted, ...
                    'virtual_time_s', obj.get_field(resp, 'virtual_time_s'), ...
                    'transport_error', transport_err, ...
                    'error_identifier', err_id));

                if accepted
                    return;                       % 成功
                end

                if ~isempty(transport_err)
                    % 传输层失败 -> 允许重试（同 payload 同 request_id）
                    warning('[SimulatorClient] 传输失败 (第 %d/%d 次): %s', ...
                        attempt, obj.max_retries, transport_err);
                    if attempt < obj.max_retries
                        pause(0.5);
                        continue;
                    end
                    error('SimulatorClient:transport', ...
                        '传输层失败 %d 次，已放弃: [%s] %s', ...
                        obj.max_retries, err_id, transport_err);
                end

                % 收到响应但未被接受 -> 不重试，立刻报清楚（配置/协议错，重试无益）
                % 注：经 webwrite 拿不到 4xx 的 JSON 体（它抛的是普通 MException），
                %     故此处报告状态码 + 标识符 + 服务端消息；body 若拿到则一并给出。
                error('SimulatorClient:rejected', ...
                    '请求未被接受 (HTTP %s, accepted=%s)\n  标识符: %s\n  消息: %s\n  响应体: %s', ...
                    obj.fmt_status(http_status), ...
                    obj.fmt_status(obj.get_field(resp, 'accepted')), ...
                    err_id, last_msg, jsonencode(obj.safe(resp)));
            end

            error('SimulatorClient:exhausted', '重试 %d 次后仍未成功: %s', ...
                obj.max_retries, last_msg);
        end

        %% 追加一条记录到 JSONL（每条 open/append/close -- 崩溃也不丢已记录内容）
        function log_record(obj, kind, extra)
            obj.log_seq = obj.log_seq + 1;
            % 实时刷新墙钟，否则中途记录的 elapsed_wall_s 恒为 0
            if ~isempty(obj.t_enter_wall)
                obj.elapsed_wall = toc(obj.t_enter_wall);
            end
            rec = struct;
            rec.seq = obj.log_seq;
            rec.kind = kind;
            rec.wall_clock_ms = posixtime(datetime('now', 'TimeZone', 'local')) * 1000;
            rec.time_local = datestr(now, 'yyyy-mm-dd HH:MM:SS.FFF');
            if isfield(extra, 'virtual_time_s')
                rec.virtual_time_s = extra.virtual_time_s;
            end
            rec.robot_id = obj.robot_id;
            rec.elapsed_wall_s = obj.elapsed_wall;
            f = fieldnames(extra);
            for i = 1:numel(f)
                rec.(f{i}) = extra.(f{i});
            end
            try
                fid = fopen(obj.log_path, 'a');
                if fid > 0
                    fprintf(fid, '%s\n', jsonencode(rec));
                    fclose(fid);
                end
            catch ME
                warning('[SimulatorClient] 日志写入失败: %s', ME.message);
            end
        end

        %% 收尾：写一条 session_end（表 1 第 4 列程序运行时间= /enter -> 结束）
        function close_log(obj)
            obj.log_record('session_end', struct(...
                'program_run_time_s', obj.wall_clock_s, ...
                'virtual_time_s', obj.virtual_time, ...
                'log_path', obj.log_path));
        end

        function p = get_log_path(obj)
            p = obj.log_path;
        end

        %% 自记录日志的体积 [MB]（用于核对是否存在异常高频循环）
        function mb = log_size_mb(obj)
            d = dir(obj.log_path);
            if isempty(d), mb = 0; else, mb = d.bytes / 1024 / 1024; end
        end

        %% 更新时间跟踪
        %  走到这里的响应必为 accepted=true（send_request 已保证），直接采用其时钟值。
        %  注意 accepted=false 时给的 virtual_time_s=0 不是当前虚拟时刻（附件2）。
        function update_time(obj, resp)
            if isfield(resp, 'virtual_time_s') && ~isempty(resp.virtual_time_s)
                obj.virtual_time = resp.virtual_time_s;
            end

            if isfield(resp, 'remaining_real_duration_s')
                obj.remaining_time = resp.remaining_real_duration_s;
            end
        end

        %% 检查时间安全性
        function safe = is_time_safe(obj, time_reserve)
            safe = obj.remaining_time > time_reserve;
        end

        %% 小工具
        function v = get_field(obj, s, name)
            if isstruct(s) && isfield(s, name)
                v = s.(name);
            else
                v = [];
            end
        end

        function s = fmt_status(obj, v)
            if isempty(v)
                s = 'n/a';
            elseif islogical(v)
                if v, s = 'true'; else, s = 'false'; end
            elseif isnumeric(v)
                s = sprintf('%g', v);
            else
                s = char(string(v));
            end
        end

        function out = safe(obj, v)
            if isempty(v)
                out = struct('empty', true);
            else
                out = v;
            end
        end

        %% 是否"确实收到了 HTTP 响应"（2xx/4xx）
        %  必须防御空值：传输层失败时 http_status 为 []，而 `[] >= 200 && ...`
        %  会抛 MATLAB:nonLogicalConditional。
        function tf = is_http_status(obj, c)
            tf = ~isempty(c) && isnumeric(c) && isscalar(c) && isfinite(c) && ...
                 c >= 200 && c < 500;
        end

        %% 从异常里取出 HTTP 状态码；取不到返回 []（= 判为传输层失败，可重试）
        %  webwrite 在 4xx/5xx 时抛的是普通 MException（无 Response 属性），状态码编码在
        %  标识符里（MATLAB:webservices:HTTP400StatusCodeError）；连不上则是
        %  ...:ConnectionRefused。故按标识符分类，比"有没有 Response"可靠。
        function code = status_of(obj, ME)
            code = [];
            e = ME;
            while ~isempty(e)
                try
                    if isprop(e, 'Response') && ~isempty(e.Response)
                        code = double(e.Response.StatusCode);
                        return;
                    end
                catch
                end
                tok = regexp(e.identifier, ...
                    '^MATLAB:webservices:HTTP(\d{3})StatusCodeError$', 'tokens', 'once');
                if ~isempty(tok)
                    code = str2double(tok{1});
                    return;
                end
                try
                    e = e.cause{1};
                catch
                    e = [];
                end
            end
        end

        %% 取异常标识符（用于日志诊断；沿 cause 链取第一个非空）
        function id = ident_of(obj, ME)
            id = '';
            e = ME;
            while ~isempty(e)
                if ~isempty(e.identifier)
                    id = e.identifier;
                    return;
                end
                try
                    e = e.cause{1};
                catch
                    e = [];
                end
            end
        end

        %% 从 HTTP 异常里尽力取到响应体（沿 cause 链找带 Response 的那一层）
        function body = body_of(obj, ME)
            body = struct('unparsable_body', true);
            e = ME;
            while ~isempty(e)
                try
                    if isprop(e, 'Response') && ~isempty(e.Response)
                        body = obj.try_parse_body(e.Response);
                        return;
                    end
                catch
                    % 继续找
                end
                try
                    e = e.cause{1};
                catch
                    e = [];
                end
            end
        end

        %% 从 HTTP 异常里尽力取到响应体（可能是 struct / 字符串 / 取不到）
        function body = try_parse_body(obj, response)
            body = struct('unparsable_body', true);
            if isempty(response)
                return;
            end
            try
                data = response.Body.Data;
                if isstruct(data)
                    body = data;
                elseif ischar(data) || isstring(data)
                    body = jsondecode(char(data));
                end
            catch
                % 保持 unparsable 标记
            end
        end
    end
end
