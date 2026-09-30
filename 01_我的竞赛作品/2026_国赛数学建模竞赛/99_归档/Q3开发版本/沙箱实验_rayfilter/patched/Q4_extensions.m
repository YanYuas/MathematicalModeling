% ========================================================================
% Q4_extensions —— Q4 的三个核心扩展
%
% 外扩环带网格生成、surrounding 全域自检、no_signal 三义处置（含扇区探针）。
% 设计条件的定档与被推翻的旧值见《Q3 调优经验与补丁记录》P-6 与权威数字表 §6.4。
% ========================================================================

classdef Q4_extensions
    methods (Static)
        %% 外扩环带生成
        function P_extended = generate_extended_grid(d, R_domain, R_eff)
            % 输入: d 网格间距；R_domain 圆域半径；R_eff 有效接收半径
            % 输出: P_extended 含外扩环带的检测点集
            %
            % 外扩宽度是 d（不是 d/√3）：surrounding 需要 G ∈ conv{三最近格点}，
            % 而**第三近邻的距离可达 d**（d/√3 只是最近邻的覆盖半径）。
            % 实测：外扩 d/√3 失败 2.47%（边界带 42%）；外扩 d 失败 0.00%。
            % 设计条件是 d ≤ R_eff（三最近邻都须 ≤ R_eff 才能进 Q(G)）。

            if nargin < 3, R_eff = 1000; end

            % 基础三角格（圆域内）
            params = struct('d', d, 'R_domain', R_domain, 'extend_for_Q4', false);
            P_base = generate_triangular_grid(params);

            % 外扩环带（R < ||p|| <= R + d）—— 宽度 = d，见上方更正
            margin = d;
            R_outer = R_domain + margin;

            % 三角格基矢
            a1 = [d, 0];
            a2 = [d/2, sqrt(3)*d/2];

            % 生成范围
            n_max = ceil(R_outer / d) + 1;

            % 生成环带格点
            P_ring = [];
            for i = -n_max:n_max
                for j = -n_max:n_max
                    p = i * a1 + j * a2;
                    r = norm(p);

                    % 环带条件：R < r <= R + d
                    if r > R_domain && r <= R_outer
                        P_ring = [P_ring; p];
                    end
                end
            end

            % 合并去重
            P_extended = [P_base; P_ring];
            P_extended = Q4_extensions.unique_points(P_extended, 1e-6);

            fprintf('[Q4外扩] d=%.0f, 外扩宽度=%0.1f(=d), 基础=%d点, 环带=%d点, 总计=%d点\n', ...
                d, margin, size(P_base,1), size(P_ring,1), size(P_extended,1));

            % 设计条件自检
            if d > R_eff + 1e-9
                warning('Q4[设计条件]: d=%.1f > R_eff=%.1f ⇒ surrounding 不成立（实测 d=1500 失败率 91%%）', d, R_eff);
            end
        end

        %% 1b. 全域零漏点自检（P0-3 要求）
        function [ok, fail_cnt, worst] = check_surrounding_all(P, R_domain, R_eff, step)
            % 在 D(0,R_domain) 上采样，断言 ∀G: G ∈ conv{p ∈ P : ||p-G|| <= R_eff}
            % 边界环带（[R_domain-50, R_domain]）加密，因为失败集中在边界
            if nargin < 4, step = 25; end
            ok = true; fail_cnt = 0; worst = [];
            Gs = [];
            for r = 0:step:R_domain
                nth = max(8, ceil(2*pi*r/step));
                for th = linspace(0, 2*pi, nth+1); th(end) = []; Gs = [Gs; r*cos(th), r*sin(th)]; end
            end
            for r = (R_domain-50):5:R_domain      % 边界加密
                for th = linspace(0, 2*pi, 361); th(end) = []; Gs = [Gs; r*cos(th), r*sin(th)]; end
            end
            for i = 1:size(Gs,1)
                if ~Q4_extensions.is_surrounding(Gs(i,:), P, R_eff)
                    fail_cnt = fail_cnt + 1;
                    if isempty(worst), worst = Gs(i,:); end
                end
            end
            ok = (fail_cnt == 0);
            if ok, verdict = '✅ 通过'; else, verdict = '❌ 失败'; end
            fprintf('[Q4自检] 全域零漏点：采样 %d 点，失败 %d (%.2f%%) → %s\n', ...
                size(Gs,1), fail_cnt, 100*fail_cnt/size(Gs,1), verdict);
            if ~isempty(worst)
                fprintf('         首例失败 G = (%.1f, %.1f)，||G|| = %.1f\n', worst(1), worst(2), norm(worst));
            end
        end

        %% 2. Surrounding 判定
        function is_surr = is_surrounding(G, P, R_eff)
            % 输入: G - 干扰源估计位置 [x, y]
            %       P - 检测点集 (Nx2)
            %       R_eff - 有效接收半径
            % 输出: is_surr - 是否被 surrounding

            % 筛选有效邻域内的点
            distances = sqrt(sum((P - G).^2, 2));
            P_nearby = P(distances <= R_eff, :);

            if size(P_nearby, 1) < 3
                is_surr = false;
                return;
            end

            % 计算凸包
            try
                k = convhull(P_nearby(:,1), P_nearby(:,2));
                hull_points = P_nearby(k, :);

                % 判定 G 是否在凸包内
                in = inpolygon(G(1), G(2), hull_points(:,1), hull_points(:,2));
                is_surr = in;

            catch
                % 凸包失败（点共线等）
                is_surr = false;
            end
        end

        %% 3. 扇区探针（三点判别法）
        function result = sector_probe(G, channel, sim_client, config)
            % 输入: G - 干扰源估计位置
            %       channel - 频道
            %       sim_client - 模拟器客户端
            %       config - 配置参数
            % 输出: result - 探针结果 ('no_source', 'directional', 'omnidirectional')

            % 在 G 周围取 3 个检测点（相位 120°）
            r_probe = 50;  % 探针半径 [m]
            angles = [0, 120, 240];  % 三个方向

            n_obs = 0;  % 观测次数

            for i = 1:3
                angle_rad = deg2rad(angles(i));
                probe_pos = G + r_probe * [cos(angle_rad), sin(angle_rad)];

                % 检测
                try
                    resp = sim_client.measure(probe_pos(1), probe_pos(2), channel);

                    if strcmp(resp.measure_result, 'direction') || strcmp(resp.measure_result, 'near')
                        n_obs = n_obs + 1;
                    end
                catch
                    % 检测失败，跳过
                end
            end

            % 判别
            if n_obs == 0
                result = 'no_source';
            elseif n_obs == 3
                result = 'omnidirectional';
            else
                result = 'directional';
            end

            fprintf('    [扇区探针] 位置(%.0f,%.0f), 观测=%d/3, 判定=%s\n', ...
                G(1), G(2), n_obs, result);
        end

        %% 4. Q4 增强型 no_signal 处理
        function action = handle_no_signal_Q4(position, channel, P_extended, sim_client, config)
            % 输入: position - 当前检测点
            %       channel - 频道
            %       P_extended - 外扩检测点集
            %       sim_client - 模拟器客户端
            %       config - 配置
            % 输出: action - 'skip' (无源) 或 'probe' (需探针)

            G = position;  % 用当前位置作为估计

            % 判断是否 surrounding
            if Q4_extensions.is_surrounding(G, P_extended, config.R_sensor)
                % Surrounding 确认无源
                fprintf('    [Q4增强] surrounding 确认，跳过频道 %d\n', channel);
                action = 'skip';
            else
                % 非 surrounding，使用扇区探针
                fprintf('    [Q4增强] 非 surrounding，启动扇区探针\n');
                probe_result = Q4_extensions.sector_probe(G, channel, sim_client, config);

                if strcmp(probe_result, 'no_source')
                    action = 'skip';
                else
                    action = 'probe';
                end
            end
        end

        %% 辅助函数
        function unique_pts = unique_points(points, tol)
            if size(points, 1) <= 1
                unique_pts = points;
                return;
            end

            unique_pts = points(1, :);
            for i = 2:size(points, 1)
                p = points(i, :);
                is_duplicate = false;
                for j = 1:size(unique_pts, 1)
                    if norm(p - unique_pts(j, :)) < tol
                        is_duplicate = true;
                        break;
                    end
                end
                if ~is_duplicate
                    unique_pts = [unique_pts; p];
                end
            end
        end
    end
end
