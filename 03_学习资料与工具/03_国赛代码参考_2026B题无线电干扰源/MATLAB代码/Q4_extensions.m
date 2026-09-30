% Q4_extensions -- Q4 的三个核心机制
%   ① 外扩环带网格生成（宽度 = d，见下）
%   ② surrounding 全域自检 ＋ 死角反例正反两面
%   ③ 扇区探针（引理 Q4-D，把"只有 1 条示向度"补成 2 条 -> L 有界）

classdef Q4_extensions
    methods (Static)
        %% ① 检测点集（两种档）
        function [P_extended, info] = generate_extended_grid(d, R_domain, R_eff, mode)
            % 输入: d 网格间距（内层格距）；R_domain 圆域半径；R_eff 最坏有效接收半径
            %       mode 'ring'（默认，推荐）| 'lattice'（早期档，留作对照）
            % 输出: P_extended 检测点集 (N×2)；info 统计
            % 两档的定档依据（实机 6 局统计）
            % 实机 T_vir ~= 9.2k~10.8k s，移动占 74~78%；31 点规则格的 MST 恰 30 km，
            % 其中 12 km 挂在 12 个 r=2645.8 的点上（圆域外 846 m）。
            % 那些点是"规则格补边界三角"的产物，不是 surrounding 的本质需要。

            if nargin < 3 || isempty(R_eff), R_eff = 1000; end
            if nargin < 4 || isempty(mode), mode = 'ring'; end

            params = struct('d', d, 'R_domain', R_domain, 'extend_for_Q4', false);
            P_base = generate_triangular_grid(params);      % 圆内规则格

            switch lower(mode)
                case 'lattice'
                    margin = d;
                    R_outer = R_domain + margin;
                    a1 = [d, 0];
                    a2 = [d/2, sqrt(3)*d/2];
                    n_max = ceil(R_outer / d) + 1;
                    P_ring = zeros(0, 2);
                    for i = -n_max:n_max
                        for j = -n_max:n_max
                            p = i * a1 + j * a2;
                            r = norm(p);
                            if r > R_domain && r <= R_outer
                                P_ring(end+1, :) = p; %#ok<AGROW>
                            end
                        end
                    end
                    ring_kind = 'lattice_band';

                otherwise   % 'ring'
                    margin = 100;                    % 环半径 = R_domain + 100
                    R_outer = R_domain + margin;
                    n_ring = 12;
                    th = (0:n_ring-1)' * 2*pi/n_ring;   % 相位 0
                    P_ring = [R_outer * cos(th), R_outer * sin(th)];
                    ring_kind = 'regular_12gon';
            end

            P_extended = Q4_extensions.unique_rows([P_base; P_ring]);
            P_extended = P_extended(all(isfinite(P_extended), 2), :);

            % 硬守卫：环带必须真的存在，且不得被二次裁剪回圆域
            max_norm = max(vecnorm(P_extended, 2, 2));
            n_outside = sum(vecnorm(P_extended, 2, 2) > R_domain + 1e-9);
            if n_outside == 0
                error(['Q4_extensions:ringClipped ' ...
                       '环带被裁掉了（全部 |p| <= R_domain）--  头号坑：' ...
                       '不要对 P 再做圆域二次裁剪。']);
            end

            info = struct('n_base', size(P_base, 1), 'n_ring', size(P_ring, 1), ...
                          'n_total', size(P_extended, 1), 'n_outside', n_outside, ...
                          'R_outer', R_outer, 'margin', margin, 'max_norm', max_norm, ...
                          'd', d, 'R_eff', R_eff, 'mode', lower(mode), ...
                          'ring_kind', ring_kind);

            fprintf(['[网格] Q4 检测点集（%s / %s）：内层 %d 点 + 外层 %d 点 -> 合计 %d 点' ...
                     '（圆外 %d 点，最远 %.1f m）\n'], ...
                info.mode, ring_kind, info.n_base, info.n_ring, info.n_total, ...
                n_outside, max_norm);

            % 设计条件自检：只有 lattice 档依赖 d <= R_eff
            if strcmp(ring_kind, 'lattice_band') && d > R_eff + 1e-9
                warning(['Q4[设计条件]: d=%.1f > R_eff=%.1f -> surrounding 不成立' ...
                         '（离线统计 d=1200 失败率 35.5%%、d=1500 失败率 91.4%%）'], d, R_eff);
            end
        end

        %% ② surrounding 自检
        function Gs = sample_disk(R_domain, step, dense_boundary)
            % 在 D(0,R_domain) 上采样：极坐标网格 + 边界环带加密。
            % 列向量拼接（不是行向量），保证每行恰好 2 列。
            if nargin < 3, dense_boundary = true; end

            Gs = zeros(0, 2);
            for r = 0:step:R_domain
                nth = max(8, ceil(2*pi*r/step));
                th = linspace(0, 2*pi, nth + 1);
                th(end) = [];
                Gs = [Gs; r * cos(th)', r * sin(th)']; %#ok<AGROW>
            end

            if dense_boundary
                r0 = max(0, R_domain - 50);
                th = linspace(0, 2*pi, 361);
                th(end) = [];
                for r = r0:5:R_domain
                    Gs = [Gs; r * cos(th)', r * sin(th)']; %#ok<AGROW>
                end
            end
        end

        function [ok, fail_cnt, worst, stats] = check_surrounding_all(P, R_domain, R_eff, step, verbose)
            % 断言 任意G  in  D(0,R_domain): G  in  conv{p  in  P : ||p-G|| <= R_eff}
            % 边界环带（[R_domain-50, R_domain]）加密，因为失败集中在边界。
            if nargin < 4 || isempty(step), step = 25; end
            if nargin < 5 || isempty(verbose), verbose = true; end

            Gs = Q4_extensions.sample_disk(R_domain, step, true);
            n = size(Gs, 1);
            rc = vecnorm(Gs, 2, 2);
            in_band = rc > (R_domain - 50);

            ok_all = false(n, 1);
            d3 = zeros(n, 1);          % 第三近邻距离（surrounding 的实际余量指标）
            for i = 1:n
                ok_all(i) = Q4_extensions.is_surrounding(Gs(i, :), P, R_eff);
                dd = sort(sqrt(sum((P - Gs(i, :)).^2, 2)));
                if numel(dd) >= 3, d3(i) = dd(3); else, d3(i) = Inf; end
            end

            fail_cnt = sum(~ok_all);
            ok = (fail_cnt == 0);
            nb = sum(in_band);
            fail_band = sum(~ok_all & in_band);
            stats = struct('n_sample', n, 'n_band', nb, 'fail_total', fail_cnt, ...
                           'fail_band', fail_band, ...
                           'fail_rate', fail_cnt / max(n, 1), ...
                           'fail_rate_band', fail_band / max(nb, 1), ...
                           'third_nearest_max', max(d3), ...
                           'margin', R_eff - max(d3));

            worst = [];
            if fail_cnt > 0
                k = find(~ok_all, 1);
                worst = Gs(k, :);
            end

            if ok, verdict = ' 通过'; else, verdict = ' 失败'; end
            if verbose
                fprintf(['[覆盖自检] Q4 surrounding：采样 %d 点（边界带 %d），失败 %d ' ...
                         '(全域 %.2f%%，边界带 %.2f%%) -> %s\n'], ...
                    n, nb, fail_cnt, 100 * stats.fail_rate, 100 * stats.fail_rate_band, verdict);
                fprintf(['           第三近邻最大 %.2f m，对 R_eff=%.0f 的余量 %.2f m' ...
                         '（设计条件：三最近邻都须 <= R_eff）\n'], ...
                    stats.third_nearest_max, R_eff, stats.margin);
                if ~isempty(worst)
                    fprintf('           首例失败 G = (%.1f, %.1f)，||G|| = %.1f\n', ...
                        worst(1), worst(2), norm(worst));
                end
            end
        end

        function is_surr = is_surrounding(G, P, R_eff)
            % G  in  conv{ p  in  P : ||p-G|| <= R_eff } ？
            % 容差 1e-9 是必须的：d=1000 时格点顶点的第三近邻距离恰为 d=1000，
            % 与 R_eff 等值；浮点误差会把 1000.0000000000002 判成"超出" -> 自检在
            % 3 个格点上假性失败（实测）。物理上"距离 = R_eff"是可测的
            % （附件2 不超过有效接收半径），故按含边界处理。
            G = G(:)';
            d2 = sum((P - G).^2, 2);
            Q = P(d2 <= (R_eff + 1e-9)^2, :);

            if size(Q, 1) < 3
                % 三点是包围的下界；退化到"共线段"时另判
                is_surr = Q4_extensions.on_segment(G, Q);
                return;
            end

            try
                k = convhull(Q(:, 1), Q(:, 2));
                hull = Q(k, :);
                is_surr = inpolygon(G(1), G(2), hull(:, 1), hull(:, 2));
            catch
                % 共线 -> convhull 抛错；退化为"是否落在两端点连线上"
                is_surr = Q4_extensions.on_segment(G, Q);
            end
        end

        function tf = on_segment(G, Q)
            % 退化兜底：G 是否落在 Q 的凸包（单点 / 共线线段）上
            tf = false;
            if isempty(Q), return; end
            if size(Q, 1) == 1
                tf = norm(G - Q(1, :)) < 1e-6;
                return;
            end
            v = Q - G;                       % 各点相对 G 的向量
            a = v(1, :);
            if norm(a) < 1e-12
                tf = true;                   % G 与某点重合
                return;
            end
            cross_ok = all(abs(a(1) * v(:, 2) - a(2) * v(:, 1)) < 1e-3);   % 全部共线
            proj = v * a';
            tf = cross_ok && (min(proj) <= 1e-9) && (max(proj) >= -1e-9);
        end

        %% 死角反例：断言 2（正面）/ 断言 3（反面）
        function r = deadzone_case(P, R_domain, R_eff)
            % 断言 2（正面）：G=(R_domain,0)、u=(1,0)（圆外法向）
            %   -> 必须存在 p  in  P 满足 p_x >= R_domain ∧ ||p-G|| <= R_eff
            %   即"环带点落到了源的定向一侧"，该源可被看到。
            G = [R_domain, 0];
            u = [1, 0];
            v = P - G;
            dist = vecnorm(v, 2, 2);
            in_range = dist <= R_eff + 1e-9;
            in_sector = (v * u') >= -1e-9;          %   含边界 + 容差
            hit = in_range & in_sector;

            r = struct('G', G, 'u', u, 'passed', any(hit), ...
                       'n_hit', sum(hit), 'n_in_range', sum(in_range), ...
                       'witness', []);
            if any(hit)
                idx = find(hit, 1);
                r.witness = P(idx, :);
            end
        end

        function r = clipped_grid_fails(R_domain, R_eff, d)
            % 断言 3（反面）：圆内裁剪的网格在同一反例下必须失败
            %   （验证定理 Q4-F：死角源于"裁剪"，不是"定向"）
            if nargin < 3 || isempty(d), d = 1000; end
            P = generate_triangular_grid(struct('d', d, 'R_domain', R_domain, ...
                                                'extend_for_Q4', false));
            r = Q4_extensions.deadzone_case(P, R_domain, R_eff);
            r.passed = ~r.passed;    % 期望"失败"，取反后 passed=true 表示符合定理
            r.n_points = size(P, 1);
        end

        %% ③ 扇区探针（引理 Q4-D）
        function out = sector_probe(obs_pos, svd_deg, channel, sim_client, config)
            % 在已得示向度的观测点 p 附近，取垂直视线方向的偏移点补测第二条同扇区示向度。
            % 引理 Q4-D：n̂ 垂直 (p−G)、q_± = p ± b·n̂ -> (q_±−G)·u = (p−G)·u ± b(n̂·u)，
            %   两式之和 = 2(p−G)·u >= 0 -> 至少一个仍在扇区 H 内。
            %   垂直偏移同时使 ||q_±−G|| = sqrt(r^2+b^2) ~= r，故仍在 R_eff 内（取 b 足够小）。
            %   写成固定两次即可，不写成"循环重试"；
            %   b 过大或 p 恰在扇区边界时两次都可能 no_signal -> 减半再试一轮，共 <=2 轮 4 次。

            out = struct('found', false, 'kind', 'none', 'position', [], ...
                         'svd_deg', [], 'n_probe', 0, 'cost', 0);
            if nargin < 5 || ~isfield(config, 'sector_probe_step') || isempty(config.sector_probe_step)
                b_base = 100;
            else
                b_base = config.sector_probe_step;
            end

            p = obs_pos(:)';
            % n̂ 垂直 (p−G)：视线方位角 = svd_deg（p->G），垂直方向即 svd_deg+90度
            n_hat = [cosd(svd_deg + 90), sind(svd_deg + 90)];

            for round_i = 1:2
                b = b_base / (4 ^ (round_i - 1));      % 100 -> 25
                q = [p + b * n_hat; p - b * n_hat];
                for i = 1:2
                    m = sim_client.measure(q(i, 1), q(i, 2), channel);
                    out.n_probe = out.n_probe + 1;
                    out.cost = out.cost + config.T_measure;

                    if strcmp(m.measure_result, 'near')
                        out.found = true; out.kind = 'near';
                        out.position = q(i, :);
                        fprintf('    [扇区探针] 频道 %d：偏移点 %s 返回 near -> 可直接清除\n', ...
                            channel, mat2str(round(q(i, :), 1)));
                        return;
                    end
                    if strcmp(m.measure_result, 'direction') && isfield(m, 'svd_deg')
                        out.found = true; out.kind = 'direction';
                        out.position = q(i, :);
                        out.svd_deg = m.svd_deg;
                        fprintf(['    [扇区探针] 频道 %d：第 %d 次偏移(b=%.0f m)得示向度 ' ...
                                 '%.2f度 -> 已有第二条同扇区示向度\n'], ...
                            channel, out.n_probe, b, m.svd_deg);
                        return;
                    end
                end
            end

            fprintf(['    [扇区探针] 频道 %d：2 轮共 %d 次偏移均 no_signal' ...
                     '（p 贴近扇区边界或 b 仍偏大）-> 放弃本频道本轮\n'], channel, out.n_probe);
        end

        %% 声线过滤：这次测量有没有可能给出第 2 个观测？
        function tf = ray_can_see(from_pos, theta_deg, at_pos, config)
            % 判据与 Q3 程序里的 ray_can_see 一致。
            %   本文件自实现一份，理由：该文件在另一个目录（不在 MATLAB path 上），
            %   无法直接依赖；而把共享件搬过来会制造分叉。判据与常数保持一致，便于日后合并。
            % 问题：某频道只在格点 A 被听到过 1 次（示向度 θ）。交会定位要 2 个观测，
            %   所以只有"当前位置 p 能给出第 2 个观测"时，这一次测量才有价值。
            %
            u = [cosd(theta_deg), sind(theta_deg)];
            L = 2 * config.R_domain;
            d = Q4_extensions.point_seg_dist(at_pos, from_pos(:)', from_pos(:)' + L * u);
            spread = L * sind(config.epsilon_deg);
            tf = d <= config.R_sensor + spread;
        end

        function d = point_seg_dist(p, a, b)
            ab = b - a;
            L2 = ab * ab';
            if L2 < 1e-12, d = norm(p - a); return; end
            t = max(0, min(1, ((p(:)' - a) * ab') / L2));
            d = norm(p(:)' - (a + t * ab));
        end

        %% 辅助：按容差去重（向量化，替换原 O(n^2) 双重循环）
        function U = unique_rows(P)
            if isempty(P)
                U = zeros(0, 2);
                return;
            end
            P = round(P, 6);
            U = unique(P, 'rows', 'stable');
        end
    end
end
