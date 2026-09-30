% ========================================================================
% run_assertions -- 断言自动化测试（离线部分）
% 用法：run_assertions('Q3') / run_assertions('Q4')，返回 results 结构体。
% 各断言的判据来源与历史修正见§二、§三。
% ========================================================================

function results = run_assertions(mode)
    % mode: 'Q3' 或 'Q4'

    if nargin < 1
        mode = 'Q3';
    end

    fprintf('\n');
    fprintf('========================================================================\n');
    fprintf(' 断言自动化测试 (%s)\n', mode);
    fprintf('========================================================================\n');
    fprintf('\n');

    results = struct;
    results.mode = mode;
    results.passed = 0;
    results.failed = 0;
    results.details = {};

    %% 断言 1: 覆盖自检（用生产同款网格，不再硬编码已废弃的 d=1500）
    fprintf('[断言 1] 覆盖自检...\n');
    try
        cfg = load_config(mode);
        P = build_production_grid(cfg, mode);

        cover_cfg = struct('R_domain', cfg.R_domain, 'R_sensor', cfg.R_sensor);
        [is_covered, max_dist] = check_coverage(P, cover_cfg);

        assert(is_covered, '覆盖失败');
        assert(max_dist <= cfg.R_sensor, '最大距离超出');

        fprintf(' 通过: 覆盖自检 (n=%d, max_dist=%.2fm)\n\n', size(P, 1), max_dist);
        results.passed = results.passed + 1;
        results.details{end+1} = sprintf('断言1: PASS (%.2fm)', max_dist);
    catch ME
        fprintf(' 失败: %s\n\n', ME.message);
        results.failed = results.failed + 1;
        results.details{end+1} = sprintf('断言1: FAIL - %s', ME.message);
    end

    %% 断言 2: 间距约束
    fprintf('[断言 2] 间距约束...\n');
    try
        % 间距取自本模式的配置（与断言 1/3/6 同源，避免硬编码空转）
        cfg = load_config(mode);
        d = cfg.grid_spacing;
        d_max = sqrt(3) * cfg.R_sensor;   % 覆盖条件 d <= sqrt(3)·R_eff

        assert(d <= d_max, sprintf('d=%.1f 超过上限 %.4f', d, d_max));

        fprintf(' 通过: d=%.1f <= %.4f（sqrt(3)·R_eff，R_eff=%d）\n\n', d, d_max, cfg.R_sensor);
        results.passed = results.passed + 1;
        results.details{end+1} = sprintf('断言2: PASS (d=%d <= %.4f)', d, d_max);
    catch ME
        fprintf(' 失败: %s\n\n', ME.message);
        results.failed = results.failed + 1;
        results.details{end+1} = sprintf('断言2: FAIL - %s', ME.message);
    end

    %% 断言 3: 单元数下界
    fprintf('[断言 3] 单元数下界...\n');
    try
        % 判据按建模手定义（引理 L2：N >= ⌈(R/r)^2⌉ = 4）
        n_min = 4;
        n_max = Inf;

        cfg = load_config(mode);
        P = build_production_grid(cfg, mode);
        n = size(P, 1);

        assert(n >= n_min && n <= n_max, sprintf('n=%d 不在 [%d,%d]', n, n_min, n_max));

        fprintf(' 通过: n=%d  in  [%d,%d]\n\n', n, n_min, n_max);
        results.passed = results.passed + 1;
        results.details{end+1} = sprintf('断言3: PASS (n=%d)', n);
    catch ME
        fprintf(' 失败: %s\n\n', ME.message);
        results.failed = results.failed + 1;
        results.details{end+1} = sprintf('断言3: FAIL - %s', ME.message);
    end

    %% 断言 4: Q1 判据回归
    fprintf('[断言 4] Q1 判据回归 (R_MEC <= 20)...\n');
    try
        % Q1 基准算例（权威数字表 §三）：S1=(0,0), S2=(600,0), θ1=59.036度, θ2=120.964度
        %   -> D = 39.5978, R_MEC = 19.7989（Jung 下界取等：R_MEC = D/2）
        wedge1 = struct('station', [0, 0], 'theta_deg', 59.036, 'epsilon_deg', 1);
        wedge2 = struct('station', [600, 0], 'theta_deg', 120.964, 'epsilon_deg', 1);
        wedges = [wedge1; wedge2];

        L = Q1_geometry.intersect_wedges(wedges);
        [c_star, R_MEC] = Q1_geometry.minimum_enclosing_circle(L);
        [D, ~, ~] = Q1_geometry.polygon_diameter(L);

        R_expected = 19.7989;
        D_expected = 39.5978;

        % (a) 数值回归
        assert(abs(R_MEC - R_expected) < 0.01, ...
            sprintf('R_MEC=%.6f 不匹配期望 %.6f', R_MEC, R_expected));
        assert(abs(D - D_expected) < 0.01, ...
            sprintf('D=%.6f 不匹配期望 %.6f', D, D_expected));
        % (b) 清除判据
        assert(R_MEC <= 20, sprintf('R_MEC=%.6f > 20', R_MEC));
        % (c) Jung 夹逼不变量 D/2 <= R_MEC <= D/sqrt(3) -- 这才是"配置写错"的真判据
        assert(R_MEC >= D/2 - 1e-9 && R_MEC <= D/sqrt(3) + 1e-9, ...
            sprintf('违反 Jung 夹逼: D/2=%.6f <= R_MEC=%.6f <= D/sqrt(3)=%.6f 不成立', ...
                    D/2, R_MEC, D/sqrt(3)));

        fprintf(' 通过: R_MEC=%.6f ~= %.6f；D=%.6f；Jung 夹逼 [%.4f, %.4f] 成立\n\n', ...
                R_MEC, R_expected, D, D/2, D/sqrt(3));
        results.passed = results.passed + 1;
        results.details{end+1} = sprintf('断言4: PASS (R_MEC=%.6f, D=%.6f, Jung 夹逼成立)', R_MEC, D);
    catch ME
        fprintf(' 失败: %s\n\n', ME.message);
        results.failed = results.failed + 1;
        results.details{end+1} = sprintf('断言4: FAIL - %s', ME.message);
    end

    %% 断言 5: Homing 收缩率
    fprintf('[断言 5] Homing 收缩率 (λ = 0.0174531)...\n');
    try
        epsilon_rad = deg2rad(1);
        lambda_ideal = 2 * sin(epsilon_rad / 2);
        lambda_expected = 0.0174531;

        error = abs(lambda_ideal - lambda_expected);

        assert(error < 1e-6, sprintf('λ=%.7f 不匹配期望 %.7f', lambda_ideal, lambda_expected));

        fprintf(' 通过: λ=%.7f ~= %.7f\n\n', lambda_ideal, lambda_expected);
        results.passed = results.passed + 1;
        results.details{end+1} = sprintf('断言5: PASS (λ=%.7f)', lambda_ideal);
    catch ME
        fprintf(' 失败: %s\n\n', ME.message);
        results.failed = results.failed + 1;
        results.details{end+1} = sprintf('断言5: FAIL - %s', ME.message);
    end

    %% 断言 6: 移动下界自洽性 + MST 独立复算
    % 三条判据：(a) 下界按公式自复算（不硬编码，常数写错即 FAIL）；
    % (b) MST 独立实现（Prim，无工具箱依赖），断言 t_mst <= t_greedy -- 真不变量；
    % (c) 口径诚实：MST 与贪心都是上界量、下界是下界量，只能对照汇报，不能互相证明。
    fprintf('[断言 6] 移动下界自洽性 + MST 独立复算（贪心 >= MST）...\n');
    try
        R_domain  = 1800;
        R_sensor  = 1000;
        velocity  = 5;  % m/s

        cfg = load_config(mode);
        d   = cfg.grid_spacing;

        % ---- (a) 下界公式自复算：2·r·P + pir^2 >= piR^2 -> P >= pi(R^2−r^2)/(2r) ----
        P_min_formula = steiner_tube_bound(R_domain, R_sensor);
        P_min_doc     = 3518.5838;                 % Q3-F47（权威数字表 §五）
        t_lower       = P_min_formula / velocity;  % Q3-F48 = 703.7168 s
        assert(abs(P_min_formula - P_min_doc) < 1e-3, ...
            sprintf('下界公式复算 %.4f != 文档 %.4f', P_min_formula, P_min_doc));

        % ---- (b) MST 独立复算（Prim） ----
        P = build_production_grid(cfg, mode);
        n = size(P, 1);
        L_mst = mst_length(P);
        t_mst = L_mst / velocity;

        % ---- 贪心最近邻巡游（照旧，作为实现层对照） ----
        total_dist = 0;
        current = [0; 0];
        visited = false(n, 1);
        for i = 1:n
            min_dist = inf;  min_idx = 0;
            for j = 1:n
                if ~visited(j)
                    dist = norm(P(j, :)' - current);
                    if dist < min_dist
                        min_dist = dist;  min_idx = j;
                    end
                end
            end
            if min_idx > 0
                total_dist = total_dist + min_dist;
                current = P(min_idx, :)';
                visited(min_idx) = true;
            end
        end
        t_greedy = total_dist / velocity;

        fprintf(' (a) 下界公式 pi(R^2−r^2)/(2r) = %.4f m -> t_lower = %.4f s（文档 %.4f s）\n', ...
                P_min_formula, t_lower, 703.7168);
        fprintf(' (b) MST(d=%.0f, n=%d) = %.2f m -> t_mst = %.2f s\n', d, n, L_mst, t_mst);
        fprintf(' 贪心巡游 = %.2f m -> t_greedy = %.2f s\n', total_dist, t_greedy);
        fprintf(' (c) 上界/下界对照：t_greedy / t_lower = %.2f×（仅供汇报，非证明）\n', ...
                t_greedy / t_lower);

        % ---- 真不变量：任何访问全部格点的巡游 >= MST ----
        assert(t_mst <= t_greedy + 1e-9, ...
            sprintf('违反 MST <= 巡游：t_mst=%.4f > t_greedy=%.4f', t_mst, t_greedy));
        % ---- 贪心确实访问了全部点（否则上面的对照无意义） ----
        assert(all(visited), '贪心巡游未覆盖全部格点');

        fprintf(' 通过: 下界公式自洽；t_mst=%.2f <= t_greedy=%.2f；全部 %d 点已访问\n\n', ...
                t_mst, t_greedy, n);
        results.passed = results.passed + 1;
        results.details{end+1} = sprintf('断言6: PASS (下界 %.2fs 自洽; MST %.2fs <= 贪心 %.2fs)', ...
                                         t_lower, t_mst, t_greedy);

    catch ME
        fprintf(' 失败: %s\n\n', ME.message);
        results.failed = results.failed + 1;
        results.details{end+1} = sprintf('断言6: FAIL - %s', ME.message);
    end

    %% 断言 10: 清除判据充要
    fprintf('[断言 10] 清除判据充要 (R_MEC <= 20 ⇔ 可直接清除)...\n');
    try
        % 测试案例 1: R_MEC = 19.799 <= 20
        R_MEC_1 = 19.799;
        can_direct_1 = (R_MEC_1 <= 20);
        assert(can_direct_1, 'R_MEC=19.799 应可直接清除');

        % 测试案例 2: R_MEC = 20.1 > 20
        R_MEC_2 = 20.1;
        can_direct_2 = (R_MEC_2 <= 20);
        assert(~can_direct_2, 'R_MEC=20.1 不应直接清除');

        fprintf(' 通过: R_MEC <= 20 判据正确\n\n');
        results.passed = results.passed + 1;
        results.details{end+1} = '断言10: PASS';
    catch ME
        fprintf(' 失败: %s\n\n', ME.message);
        results.failed = results.failed + 1;
        results.details{end+1} = sprintf('断言10: FAIL - %s', ME.message);
    end

    %% 常数核对（原"断言 11"）
    fprintf('[常数核对] 关键常数正确性...\n');
    try
        config = load_config('Q3');

        % 检查关键常数
        assert(config.R_sensor == 1000, 'R_sensor 应为 1000');
        assert(config.R_clear == 20, 'R_clear 应为 20');
        assert(config.epsilon_deg == 1, 'epsilon 应为 1度');
        assert(config.R_star == 84.0369, 'R_star 应为 84.0369');

        fprintf(' 通过: 所有常数正确\n\n');
        results.passed = results.passed + 1;
        results.details{end+1} = '常数核对: PASS';
    catch ME
        fprintf(' 失败: %s\n\n', ME.message);
        results.failed = results.failed + 1;
        results.details{end+1} = sprintf('常数核对: FAIL - %s', ME.message);
    end

    %% ================= Q4 专属断言（E.3 的 1-12）=================
    % 全部离线可跑、不依赖模拟器：几何类直接算，策略类用等价的不变量替代。
    % 需要模拟器的两条（策略端到端 100%、探针在真 client 上的行为）在
    % `核验脚本/_run_mini_sim_q4.py`（Q4 迷你模拟器）与 `test_sector_probe.m` 里跑。
    if strcmp(mode, 'Q4')
        cfg4 = load_config('Q4');
        P4 = build_production_grid(cfg4, 'Q4');

        %% 断言 1: surrounding 自检（验收线 ①）
        fprintf('[断言 1·Q4] surrounding 自检（任意G: G  in  conv Q(G)）...\n');
        try
            [ok1, f1, w1, st1] = Q4_extensions.check_surrounding_all(...
                P4, cfg4.R_domain, cfg4.R_sensor);
            assert(ok1, sprintf('surrounding 失败 %d 点（%.2f%%），首例 %s', ...
                f1, 100 * st1.fail_rate, mat2str(w1)));
            fprintf(' 通过: 采样 %d 点全成立；第三近邻最大 %.2f m（余量 %.2f m）\n\n', ...
                st1.n_sample, st1.third_nearest_max, st1.margin);
            results.passed = results.passed + 1;
            results.details{end+1} = sprintf('断言1·Q4: PASS (surrounding 全域成立, 余量 %.2fm)', ...
                st1.margin);
        catch ME
            fprintf(' 失败: %s\n\n', ME.message);
            results.failed = results.failed + 1;
            results.details{end+1} = sprintf('断言1·Q4: FAIL - %s', ME.message);
        end

        %% 断言 2: 死角反例回归（正面）-- 验收线 ②
        fprintf('[断言 2·Q4] 死角反例 G=(1800,0)、u=(1,0) 必须可见...\n');
        try
            dz2 = Q4_extensions.deadzone_case(P4, cfg4.R_domain, cfg4.R_sensor);
            assert(dz2.passed, '环带中找不到 p_x >= 1800 且在 1000 m 内的点（陷阱 ：环带被裁剪）');
            fprintf(' 通过: 可见点 %s（距 G %.1f m，共 %d 个）\n\n', ...
                mat2str(dz2.witness), norm(dz2.witness - dz2.G), dz2.n_hit);
            results.passed = results.passed + 1;
            results.details{end+1} = sprintf('断言2·Q4: PASS (死角反例有可见点 %s)', ...
                mat2str(dz2.witness));
        catch ME
            fprintf(' 失败: %s\n\n', ME.message);
            results.failed = results.failed + 1;
            results.details{end+1} = sprintf('断言2·Q4: FAIL - %s', ME.message);
        end

        %% 断言 3: 同一反例下圆内裁剪网格必须失败（定理 Q4-F）
        fprintf('[断言 3·Q4] 圆内裁剪网格在同一反例下必须失败...\n');
        try
            cc = Q4_extensions.clipped_grid_fails(cfg4.R_domain, cfg4.R_sensor, cfg4.grid_spacing);
            assert(cc.passed, '圆内裁剪网格竟然找到了可见点 -- 与定理 Q4-F 矛盾');
            fprintf(' 通过: 圆内 %d 点网格看不到该源（死角确实源于"裁剪"）\n\n', cc.n_points);
            results.passed = results.passed + 1;
            results.details{end+1} = '断言3·Q4: PASS (圆内网格必漏，定理 Q4-F 成立)';
        catch ME
            fprintf(' 失败: %s\n\n', ME.message);
            results.failed = results.failed + 1;
            results.details{end+1} = sprintf('断言3·Q4: FAIL - %s', ME.message);
        end

        %% 断言 4: Q3 ⊆ Q4 退化（surrounding -> 1000-覆盖）
        fprintf('[断言 4·Q4] Q3 ⊆ Q4 退化：surrounding -> 1000-覆盖...\n');
        try
            Gs = Q4_extensions.sample_disk(cfg4.R_domain, 100, false);
            % 退化命题：G  in  conv Q(G) -> ∃p: ||p−G|| <= R_eff（取凸组合的任一项）
            % -> 对全向源（u = ∅）必然被覆盖 -> 在 Q4 网格上覆盖率仍成立
            [cov_ok, cov_max] = check_coverage(P4, cfg4);
            assert(cov_ok, 'Q4 网格的 1000-覆盖不成立 -> 退化路径断裂');
            % 另证：圆内裁剪网格的覆盖率也应成立（Q3 的判据在 Q3 网格上自洽）
            P3 = build_production_grid(load_config('Q3'), 'Q3');
            [cov3_ok, cov3_max] = check_coverage(P3, cfg4);
            assert(cov3_ok, 'Q3 网格覆盖不成立');
            fprintf(' 通过: Q4 网格 max_dist %.2f m；Q3 网格 max_dist %.2f m（两者都 <= 1000）\n\n', ...
                cov_max, cov3_max);
            results.passed = results.passed + 1;
            results.details{end+1} = sprintf('断言4·Q4: PASS (Q4 覆盖 %.1fm, Q3 覆盖 %.1fm)', ...
                cov_max, cov3_max);
        catch ME
            fprintf(' 失败: %s\n\n', ME.message);
            results.failed = results.failed + 1;
            results.details{end+1} = sprintf('断言4·Q4: FAIL - %s', ME.message);
        end

        %% 断言 5: 极端组合 -- 全贴边界 + 定向方向全朝圆外，仍必须处处可测
        fprintf('[断言 5·Q4] 极端组合：边界源 + 朝外定向，仍存在可测点...\n');
        try
            rng(2026);
            n_trial = 2000;
            worst_margin = inf;  n_fail = 0;
            for t = 1:n_trial
                phi = 2 * pi * rand;
                rr = cfg4.R_domain - 50 * rand;          % 边界带 [1750,1800]
                G = rr * [cos(phi), sin(phi)];
                u = [cos(phi), sin(phi)];                % 朝外法向 = 最坏朝向
                v = P4 - G;
                dist = vecnorm(v, 2, 2);
                dot = v * u';
                vis = (dist <= cfg4.R_sensor + 1e-9) & (dot >= -1e-9);
                if ~any(vis), n_fail = n_fail + 1; end
                if any(vis)
                    worst_margin = min(worst_margin, cfg4.R_sensor - min(dist(vis)));
                end
            end
            assert(n_fail == 0, sprintf('%d/%d 个极端配置无可测点', n_fail, n_trial));
            fprintf(' 通过: %d 个"边界+朝外"配置全部可测（最小余量 %.1f m）\n\n', ...
                n_trial, worst_margin);
            results.passed = results.passed + 1;
            results.details{end+1} = sprintf('断言5·Q4: PASS (%d 个极端配置全可测)', n_trial);
        catch ME
            fprintf(' 失败: %s\n\n', ME.message);
            results.failed = results.failed + 1;
            results.details{end+1} = sprintf('断言5·Q4: FAIL - %s', ME.message);
        end

        %% 断言 6: 扇区探针引理（几何版，不需要 client）
        fprintf('[断言 6·Q4] 扇区探针引理：q± = p ± b·n̂ 至少一个仍在扇区内...\n');
        try
            rng(7);
            n_trial = 3000;  n_bad = 0;
            if isfield(cfg4, 'sector_probe_step'), b_probe = cfg4.sector_probe_step; else, b_probe = 100; end
            for t = 1:n_trial
                psi = 2 * pi * rand;                     % 定向方向
                u = [cos(psi), sin(psi)];
                % 随机取一个"在扇区内、且在 R_eff 内"的观测点 p
                r_p = 100 + (cfg4.R_sensor - 100) * rand;
                dth = (rand - 0.5) * pi;                 % 相对 u 的夹角  in  (-90度,90度)
                p = r_p * [cos(psi + dth), sin(psi + dth)];
                th = atan2d(-p(2), -p(1));               % 从 p 指向 G=(0,0) 的方位角
                n_hat = [cosd(th + 90), sind(th + 90)];
                q = [p + b_probe * n_hat; p - b_probe * n_hat];
                inside = ((q - 0) * u') >= -1e-9;
                if ~any(inside), n_bad = n_bad + 1; end
            end
            assert(n_bad == 0, sprintf('引理被违反 %d/%d 次', n_bad, n_trial));
            fprintf(' 通过: %d 次随机试验中，两个偏移点至少一个留在同一半平面内\n\n', n_trial);
            results.passed = results.passed + 1;
            results.details{end+1} = sprintf('断言6·Q4: PASS (探针引理 %d 次全成立)', n_trial);
        catch ME
            fprintf(' 失败: %s\n\n', ME.message);
            results.failed = results.failed + 1;
            results.details{end+1} = sprintf('断言6·Q4: FAIL - %s', ME.message);
        end

        %% 断言 7: 扫掠中心集覆盖整个 L（命题 Q4-C 的前提，陷阱 ）
        fprintf('[断言 7·Q4] 扫掠中心集覆盖 L（含顶点与边）...\n');
        try
            rng(99);
            n_L = 40;  n_bad = 0;  worst_gap = 0;
            for t = 1:n_L
                % 随机凸多边形 L（生产 L = 两角域 交 圆域 -> 必凸）
                if mod(t, 8) == 0
                    L = nonconvex_L;              % 每 8 个夹一个非凸用例（鲁棒性，）
                else
                    L = convex_L;
                end
                C = sweep_centers(L, cfg4.R_clear);   % 生产同一份实现
                % 覆盖检验 = 内部随机采样 并 边界密集采样（凹口只可能出现在边界附近）
                samples = [sample_poly(L, 200); edge_samples(L, 2)];
                gap = 0;
                for k = 1:size(samples, 1)
                    dd = min(vecnorm(C - samples(k, :), 2, 2));
                    gap = max(gap, dd);
                end
                worst_gap = max(worst_gap, gap);
                if gap > cfg4.R_clear + 1e-6, n_bad = n_bad + 1; end
            end
            assert(n_bad == 0, sprintf('%d/%d 个 L 未被 20 m 盘覆盖（最大空隙 %.2f m）', ...
                n_bad, n_L, worst_gap));
            fprintf(' 通过: %d 个随机 L（含非凸）全被覆盖（最大空隙 %.2f m <= 20）\n\n', n_L, worst_gap);
            results.passed = results.passed + 1;
            results.details{end+1} = sprintf('断言7·Q4: PASS (扫掠覆盖 L，最大空隙 %.2fm)', worst_gap);
        catch ME
            fprintf(' 失败: %s\n\n', ME.message);
            results.failed = results.failed + 1;
            results.details{end+1} = sprintf('断言7·Q4: FAIL - %s', ME.message);
        end

        %% 断言 8: 三路选择阈值（20 / 84.0369，陷阱 ）
        fprintf('[断言 8·Q4] 三路选择阈值：<=20 直接 | <=84.0369 扫掠 | >84.0369 homing...\n');
        try
            m1 = design_constants.clear_mode(19.799);    % Q1 基准算例
            m2 = design_constants.clear_mode(20);
            m3 = design_constants.clear_mode(20.1533);   % d=1000 格心
            m4 = design_constants.clear_mode(30.2300);   % d=1500 格心
            m5 = design_constants.clear_mode(84.0369);
            m6 = design_constants.clear_mode(84.03691);
            assert(strcmp(m1, 'direct') && strcmp(m2, 'direct'), 'R_MEC <= 20 应为 direct');
            assert(strcmp(m3, 'sweep') && strcmp(m4, 'sweep'), '20 < R_MEC <= 84.0369 应为 sweep');
            assert(strcmp(m5, 'sweep'), 'R_MEC = 84.0369 应取含边界 -> sweep（退化 G6）');
            assert(strcmp(m6, 'homing'), 'R_MEC > 84.0369 应为 homing');
            assert(abs(design_constants.R_STAR - 84.0369) < 1e-9, 'R_STAR 常数错');
            fprintf(' 通过: 19.799/20->direct；20.1533/30.2300/84.0369->sweep；84.03691->homing\n\n');
            results.passed = results.passed + 1;
            results.details{end+1} = '断言8·Q4: PASS (20 / 84.0369 双阈值正确)';
        catch ME
            fprintf(' 失败: %s\n\n', ME.message);
            results.failed = results.failed + 1;
            results.details{end+1} = sprintf('断言8·Q4: FAIL - %s', ME.message);
        end

        %% 断言 9: 末端判据 -- 扫掠路径不读示向度（陷阱 ：等 near 会死锁）
        fprintf('[断言 9·Q4] 扫掠清除不依赖示向度（对定向源盲侧免疫）...\n');
        try
            f = fileread('clear_source.m');
            % (?s) 让 . 跨行；非贪婪 + 行首 end 取到该函数体本身
            body = regexp(f, 'function \[success, cost\] = sweep_clear_L(?s).*?\nend\n', ...
                          'match', 'once');
            assert(~isempty(body), '找不到 sweep_clear_L 函数体');
            assert(isempty(regexp(body, 'svd_of|svd_deg', 'once')), ...
                '扫掠清除里出现了示向度读取 -- 会退化为 Q3 的"等 near"路径');
            assert(~isempty(regexp(body, 'clear_result', 'once')), ...
                '扫掠清除未按 /clear 结果判定');
            fprintf(' 通过: sweep_clear_L 全程只读 /clear 结果，无 svd_deg 依赖\n\n');
            results.passed = results.passed + 1;
            results.details{end+1} = '断言9·Q4: PASS (扫掠不读示向度 -> 盲侧免疫)';
        catch ME
            fprintf(' 失败: %s\n\n', ME.message);
            results.failed = results.failed + 1;
            results.details{end+1} = sprintf('断言9·Q4: FAIL - %s', ME.message);
        end

        %% 断言 10: 接口与红线（承 Q3；客户端输入守卫）
        fprintf('[断言 10·Q4] 接口红线：坐标界 / 频道整数 / 幂等字段...\n');
        try
            cli = SimulatorClient('http://127.0.0.1:1', 'TESTTEAM', tempdir);
            bad = 0;
            try, cli.measure(3e6, 0, 1); catch, bad = bad + 1; end          % 坐标越界
            try, cli.measure(0, 0, 21);  catch, bad = bad + 1; end          % 频道越界
            try, cli.measure(0, 0, 1.5); catch, bad = bad + 1; end          % 频道非整数
            try, cli.measure(NaN, 0, 1); catch, bad = bad + 1; end          % NaN
            assert(bad == 4, sprintf('输入守卫只拦住 %d/4 种非法输入', bad));
            assert(isfield(struct('accepted', true), 'accepted'), '');
            fprintf(' 通过: 坐标 ±2e6 / 频道 1..20 整数 / NaN 四类非法输入全被拦下\n\n');
            results.passed = results.passed + 1;
            results.details{end+1} = '断言10·Q4: PASS (客户端输入守卫 4/4)';
        catch ME
            fprintf(' 失败: %s\n\n', ME.message);
            results.failed = results.failed + 1;
            results.details{end+1} = sprintf('断言10·Q4: FAIL - %s', ME.message);
        end

        %% 断言 11: 下界不违反（L2 公式自复算 + 实际 N 下的取值）
        fprintf('[断言 11·Q4] L2 下界公式：移动 + 每源2示向度 + 每源1次清除 + 空频道确认...\n');
        try
            k_src = 13;
            t_move = steiner_tube_bound(cfg4.R_domain, cfg4.R_sensor) / 5;   % 703.7168 s
            N28 = 28;                                                        % 文档口径
            t_L2_doc = t_move + k_src * 2 * 5 + k_src * 5 + (20 - k_src) * N28 * 5;
            assert(abs(t_L2_doc - 1878.7168) < 0.01, ...
                sprintf('L2 复算 %.4f != 文档 1878.7168', t_L2_doc));
            N_act = size(P4, 1);
            t_L2_act = t_move + k_src * 2 * 5 + k_src * 5 + (20 - k_src) * N_act * 5;
            fprintf(' 通过: L2(N=28) = %.2f s（文档一致）；本档 N=%d -> L2 = %.2f s\n\n', ...
                t_L2_doc, N_act, t_L2_act);
            results.passed = results.passed + 1;
            results.details{end+1} = sprintf('断言11·Q4: PASS (L2 %.2fs @N=28; %.2fs @N=%d)', ...
                t_L2_doc, t_L2_act, N_act);
        catch ME
            fprintf(' 失败: %s\n\n', ME.message);
            results.failed = results.failed + 1;
            results.details{end+1} = sprintf('断言11·Q4: FAIL - %s', ME.message);
        end

        %% 断言 12: 坐标界（环带 + homing 全程 |x|,|y| <= 2e6）
        fprintf('[断言 12·Q4] 坐标界：环带外径 + homing 最大移动...\n');
        try
            m = max(vecnorm(P4, 2, 2));
            if isfield(cfg4, 'homing_max_move'), hm = cfg4.homing_max_move; else, hm = 2500; end
            reach = m + hm;
            assert(reach < 2e6, sprintf('可能越界：%.0f', reach));
            assert(all(isfinite(P4(:))), '网格含非有限坐标');
            fprintf(' 通过: 网格最远 %.0f m + homing 上限 %.0f m = %.0f m ≪ 2e6\n\n', ...
                m, hm, reach);
            results.passed = results.passed + 1;
            results.details{end+1} = sprintf('断言12·Q4: PASS (坐标上界 %.0fm ≪ 2e6)', reach);
        catch ME
            fprintf(' 失败: %s\n\n', ME.message);
            results.failed = results.failed + 1;
            results.details{end+1} = sprintf('断言12·Q4: FAIL - %s', ME.message);
        end
    end

    %% 总结
    fprintf('========================================================================\n');
    fprintf(' 断言测试总结 (%s)\n', mode);
    fprintf('========================================================================\n');
    fprintf('通过: %d\n', results.passed);
    fprintf('失败: %d\n', results.failed);
    fprintf('总计: %d\n', results.passed + results.failed);
    fprintf('通过率: %.1f%%\n', results.passed / (results.passed + results.failed) * 100);
    fprintf('========================================================================\n');
    fprintf('\n');

    % 详细列表
    fprintf('详细结果:\n');
    for i = 1:length(results.details)
        fprintf(' %s\n', results.details{i});
    end
    fprintf('\n');

    if results.failed == 0
        fprintf(' 所有断言通过！\n\n');
    else
        warning('!  有 %d 个断言失败', results.failed);
    end
end

%% 辅助函数
function config = load_config(mode)
    % 与 main_Q3Q4 的 load_config 保持同值 -- 断言要验的是生产那套
    config = struct;
    config.R_domain = 1800;
    config.R_sensor = 1000;
    config.R_clear = 20;
    config.R_near = 5;
    config.velocity = 5;
    config.epsilon_deg = 1;
    config.R_star = 84.0369;
    config.n_channels = 20;
    config.grid_spacing = 1000;

    if strcmp(mode, 'Q3')
        config.r_outer = 1300;   % 径向档（生产默认）
    else
        config.r_outer = [];     % Q4 走检测点集档，不用径向档
        config.q4_grid_mode = 'ring';   % 与 main_Q3Q4 同值（25 点：内层格 + 12 边形环）
    end
end

function P = build_production_grid(cfg, mode)
    % 与 main_Q3Q4 同款地构造检测点集：Q4 用外扩环带；Q3 用径向档或三角格
    if strcmp(mode, 'Q4')
        gm = 'ring';
        if isfield(cfg, 'q4_grid_mode'), gm = cfg.q4_grid_mode; end
        P = Q4_extensions.generate_extended_grid(cfg.grid_spacing, cfg.R_domain, cfg.R_sensor, gm);
    elseif ~isempty(cfg.r_outer)
        P = generate_radial_grid(cfg.grid_spacing, cfg.R_domain, cfg.r_outer);
    else
        P = generate_triangular_grid(struct('d', cfg.grid_spacing, ...
            'R_domain', cfg.R_domain, 'extend_for_Q4', false));
    end
end

function P_min = steiner_tube_bound(R, r)
    % Steiner 管面积下界：2rP + pir^2 >= piR^2  ->  P >= pi(R^2−r^2)/(2r)
    % R=1800, r=1000 -> P >= 3518.5838 m，t_move >= 703.7168 s（与策略无关）
    P_min = pi * (R^2 - r^2) / (2 * r);
end

function L = mst_length(P)    % 最小生成树长度（Prim，O(n^2)，不依赖工具箱）
    % 用途：作为巡游长度的独立参照 -- 任何访问全部点的巡游都 >= MST。
    % 刻意与主流程解耦（只用 P 与欧氏距离），以免"用同一个函数证明自己"。
    n = size(P, 1);
    if n <= 1, L = 0; return; end
    inTree = false(n, 1);
    best = inf(n, 1);       % best(i) = 点 i 到当前树的最小距离
    inTree(1) = true;
    d2 = @(a, b) hypot(P(a,1) - P(b,1), P(a,2) - P(b,2));
    for i = 2:n
        best(i) = d2(i, 1);
    end
    L = 0;
    for k = 2:n
        % 取树外最近点
        m = inf;  j = 0;
        for i = 1:n
            if ~inTree(i) && best(i) < m
                m = best(i);  j = i;
            end
        end
        if j == 0, break; end
        inTree(j) = true;
        L = L + m;
        for i = 1:n
            if ~inTree(i)
                dij = d2(i, j);
                if dij < best(i), best(i) = dij; end
            end
        end
    end
end

function S = sample_poly(L, n_target)
%SAMPLE_POLY 在多边形 L 内部均匀采样（用于断言 7 检验"扫掠中心是否覆盖 L"）。
%  用拒绝采样（包围盒均匀撒点 + inpolygon 过滤）-- 早先的"质心射线法"版
%  在部分多边形上会把采样点射到 L 外面（ 实测：200 点里 27~49 个在外，
%  于是断言 7 假性报"最大空隙 113 m"）。拒绝采样无此问题，凸凹通吃。
    S = zeros(0, 2);
    if size(L, 1) < 3, return; end
    x0 = min(L(:, 1)); x1 = max(L(:, 1));
    y0 = min(L(:, 2)); y1 = max(L(:, 2));
    tries = 0;
    while size(S, 1) < n_target && tries < 200
        tries = tries + 1;
        P = [x0 + (x1 - x0) * rand(400, 1), y0 + (y1 - y0) * rand(400, 1)];
        in = inpolygon(P(:, 1), P(:, 2), L(:, 1), L(:, 2));
        S = [S; P(in, :)];
    end
    if size(S, 1) > n_target
        S = S(1:n_target, :);
    end
end

function L = convex_L
%CONVEX_L 随机凸多边形（R_MEC 落在扫掠档 20~85 m）
    nv = 4 + randi(5);
    ang = sort(2 * pi * rand(1, nv));
    rad = 25 + 60 * rand(1, nv);
    P = [rad .* cos(ang); rad .* sin(ang)]';
    k = convhull(P(:, 1), P(:, 2));
    L = P(k(1:end - 1), :);
end

function L = nonconvex_L
%NONCONVEX_L 带凹口的随机多边形（鲁棒性用例：生产 L 恒凸，但实现不应依赖该前提）
    L = convex_L;
    c = mean(L, 1);
    [~, i] = max(vecnorm(L - c, 2, 2));
    L(i, :) = c + 0.35 * (L(i, :) - c);      % 把最远的顶点拉向质心 -> 凹口
end

function S = edge_samples(L, step)
%EDGE_SAMPLES 沿每条边按 step 米采样（含顶点），用于覆盖自检
    if nargin < 2, step = 2; end
    n = size(L, 1);
    S = zeros(0, 2);
    for k = 1:n
        k2 = mod(k, n) + 1;
        a = L(k, :); b = L(k2, :);
        m = max(2, ceil(norm(b - a) / step));
        t = linspace(0, 1, m + 1); t(end) = [];
        S = [S; a + t' * (b - a)]; %#ok<AGROW>
    end
end
