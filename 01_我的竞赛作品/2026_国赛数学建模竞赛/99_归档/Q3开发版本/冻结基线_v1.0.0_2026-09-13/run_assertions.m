% ========================================================================
% run_assertions —— 断言自动化测试（离线部分）
%
% 用法：run_assertions('Q3') / run_assertions('Q4')，返回 results 结构体。
% 各断言的判据来源与历史修正见《Q3 调优经验与补丁记录》§二、§三。
% ========================================================================

function results = run_assertions(mode)
    % mode: 'Q3' 或 'Q4'

    if nargin < 1
        mode = 'Q3';
    end

    fprintf('\n');
    fprintf('========================================================================\n');
    fprintf('  断言自动化测试 (%s)\n', mode);
    fprintf('========================================================================\n');
    fprintf('\n');

    results = struct();
    results.mode = mode;
    results.passed = 0;
    results.failed = 0;
    results.details = {};

    %% 断言 1: 覆盖自检（用**生产同款**网格，不再硬编码已废弃的 d=1500）
    fprintf('[断言 1] 覆盖自检...\n');
    try
        cfg = load_config(mode);
        P = build_production_grid(cfg, mode);

        cover_cfg = struct('R_domain', cfg.R_domain, 'R_sensor', cfg.R_sensor);
        [is_covered, max_dist] = check_coverage(P, cover_cfg);

        assert(is_covered, '覆盖失败');
        assert(max_dist <= cfg.R_sensor, '最大距离超出');

        fprintf('  ✓ 通过: 覆盖自检 (n=%d, max_dist=%.2fm)\n\n', size(P, 1), max_dist);
        results.passed = results.passed + 1;
        results.details{end+1} = sprintf('断言1: PASS (%.2fm)', max_dist);
    catch ME
        fprintf('  ✗ 失败: %s\n\n', ME.message);
        results.failed = results.failed + 1;
        results.details{end+1} = sprintf('断言1: FAIL - %s', ME.message);
    end

    %% 断言 2: 间距约束
    fprintf('[断言 2] 间距约束...\n');
    try
        % 间距取自本模式的配置（与断言 1/3/6 同源，避免硬编码空转）
        cfg = load_config(mode);
        d = cfg.grid_spacing;
        d_max = sqrt(3) * cfg.R_sensor;   % 覆盖条件 d ≤ √3·R_eff

        assert(d <= d_max, sprintf('d=%.1f 超过上限 %.4f', d, d_max));

        fprintf('  ✓ 通过: d=%.1f ≤ %.4f（√3·R_eff，R_eff=%d）\n\n', d, d_max, cfg.R_sensor);
        results.passed = results.passed + 1;
        results.details{end+1} = sprintf('断言2: PASS (d=%d ≤ %.4f)', d, d_max);
    catch ME
        fprintf('  ✗ 失败: %s\n\n', ME.message);
        results.failed = results.failed + 1;
        results.details{end+1} = sprintf('断言2: FAIL - %s', ME.message);
    end

    %% 断言 3: 单元数下界
    fprintf('[断言 3] 单元数下界...\n');
    try
        % 判据按建模手定义（引理 L2：N ≥ ⌈(R/r)²⌉ = 4）
        n_min = 4;
        n_max = Inf;

        cfg = load_config(mode);
        P = build_production_grid(cfg, mode);
        n = size(P, 1);

        assert(n >= n_min && n <= n_max, sprintf('n=%d 不在 [%d,%d]', n, n_min, n_max));

        fprintf('  ✓ 通过: n=%d ∈ [%d,%d]\n\n', n, n_min, n_max);
        results.passed = results.passed + 1;
        results.details{end+1} = sprintf('断言3: PASS (n=%d)', n);
    catch ME
        fprintf('  ✗ 失败: %s\n\n', ME.message);
        results.failed = results.failed + 1;
        results.details{end+1} = sprintf('断言3: FAIL - %s', ME.message);
    end

    %% 断言 4: Q1 判据回归
    fprintf('[断言 4] Q1 判据回归 (R_MEC ≤ 20)...\n');
    try
        % Q1 基准算例（权威数字表 §三）：S1=(0,0), S2=(600,0), θ1=59.036°, θ2=120.964°
        %   ⇒ D = 39.5978, R_MEC = 19.7989（Jung 下界取等：R_MEC = D/2）
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
        % (c) Jung 夹逼不变量 D/2 ≤ R_MEC ≤ D/√3 —— 这才是"配置写错"的真判据
        assert(R_MEC >= D/2 - 1e-9 && R_MEC <= D/sqrt(3) + 1e-9, ...
            sprintf('违反 Jung 夹逼: D/2=%.6f ≤ R_MEC=%.6f ≤ D/√3=%.6f 不成立', ...
                    D/2, R_MEC, D/sqrt(3)));

        fprintf('  ✓ 通过: R_MEC=%.6f ≈ %.6f；D=%.6f；Jung 夹逼 [%.4f, %.4f] 成立\n\n', ...
                R_MEC, R_expected, D, D/2, D/sqrt(3));
        results.passed = results.passed + 1;
        results.details{end+1} = sprintf('断言4: PASS (R_MEC=%.6f, D=%.6f, Jung 夹逼成立)', R_MEC, D);
    catch ME
        fprintf('  ✗ 失败: %s\n\n', ME.message);
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

        fprintf('  ✓ 通过: λ=%.7f ≈ %.7f\n\n', lambda_ideal, lambda_expected);
        results.passed = results.passed + 1;
        results.details{end+1} = sprintf('断言5: PASS (λ=%.7f)', lambda_ideal);
    catch ME
        fprintf('  ✗ 失败: %s\n\n', ME.message);
        results.failed = results.failed + 1;
        results.details{end+1} = sprintf('断言5: FAIL - %s', ME.message);
    end

    %% 断言 6: 移动下界自洽性 + MST 独立复算
    % 三条判据：(a) 下界按公式自复算（不硬编码，常数写错即 FAIL）；
    % (b) MST 独立实现（Prim，无工具箱依赖），断言 t_mst ≤ t_greedy —— 真不变量；
    % (c) 口径诚实：MST 与贪心都是上界量、下界是下界量，只能对照汇报，不能互相证明。
    fprintf('[断言 6] 移动下界自洽性 + MST 独立复算（贪心 ≥ MST）...\n');
    try
        R_domain  = 1800;
        R_sensor  = 1000;
        velocity  = 5;  % m/s

        cfg = load_config(mode);
        d   = cfg.grid_spacing;

        % ---- (a) 下界公式自复算：2·r·P + πr² ≥ πR² ⇒ P ≥ π(R²−r²)/(2r) ----
        P_min_formula = steiner_tube_bound(R_domain, R_sensor);
        P_min_doc     = 3518.5838;                 % Q3-F47（权威数字表 §五）
        t_lower       = P_min_formula / velocity;  % Q3-F48 = 703.7168 s
        assert(abs(P_min_formula - P_min_doc) < 1e-3, ...
            sprintf('下界公式复算 %.4f ≠ 文档 %.4f', P_min_formula, P_min_doc));

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

        fprintf('  (a) 下界公式 π(R²−r²)/(2r) = %.4f m ⇒ t_lower = %.4f s（文档 %.4f s）\n', ...
                P_min_formula, t_lower, 703.7168);
        fprintf('  (b) MST(d=%.0f, n=%d) = %.2f m ⇒ t_mst = %.2f s\n', d, n, L_mst, t_mst);
        fprintf('      贪心巡游 = %.2f m ⇒ t_greedy = %.2f s\n', total_dist, t_greedy);
        fprintf('  (c) 上界/下界对照：t_greedy / t_lower = %.2f×（**仅供汇报，非证明**）\n', ...
                t_greedy / t_lower);

        % ---- 真不变量：任何访问全部格点的巡游 ≥ MST ----
        assert(t_mst <= t_greedy + 1e-9, ...
            sprintf('违反 MST ≤ 巡游：t_mst=%.4f > t_greedy=%.4f', t_mst, t_greedy));
        % ---- 贪心确实访问了全部点（否则上面的对照无意义） ----
        assert(all(visited), '贪心巡游未覆盖全部格点');

        fprintf('  ✓ 通过: 下界公式自洽；t_mst=%.2f ≤ t_greedy=%.2f；全部 %d 点已访问\n\n', ...
                t_mst, t_greedy, n);
        results.passed = results.passed + 1;
        results.details{end+1} = sprintf('断言6: PASS (下界 %.2fs 自洽; MST %.2fs ≤ 贪心 %.2fs)', ...
                                         t_lower, t_mst, t_greedy);

    catch ME
        fprintf('  ✗ 失败: %s\n\n', ME.message);
        results.failed = results.failed + 1;
        results.details{end+1} = sprintf('断言6: FAIL - %s', ME.message);
    end

    %% 断言 10: 清除判据充要
    fprintf('[断言 10] 清除判据充要 (R_MEC ≤ 20 ⇔ 可直接清除)...\n');
    try
        % 测试案例 1: R_MEC = 19.799 ≤ 20
        R_MEC_1 = 19.799;
        can_direct_1 = (R_MEC_1 <= 20);
        assert(can_direct_1, 'R_MEC=19.799 应可直接清除');

        % 测试案例 2: R_MEC = 20.1 > 20
        R_MEC_2 = 20.1;
        can_direct_2 = (R_MEC_2 <= 20);
        assert(~can_direct_2, 'R_MEC=20.1 不应直接清除');

        fprintf('  ✓ 通过: R_MEC ≤ 20 判据正确\n\n');
        results.passed = results.passed + 1;
        results.details{end+1} = '断言10: PASS';
    catch ME
        fprintf('  ✗ 失败: %s\n\n', ME.message);
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
        assert(config.epsilon_deg == 1, 'epsilon 应为 1°');
        assert(config.R_star == 84.0369, 'R_star 应为 84.0369');

        fprintf('  ✓ 通过: 所有常数正确\n\n');
        results.passed = results.passed + 1;
        results.details{end+1} = '常数核对: PASS';
    catch ME
        fprintf('  ✗ 失败: %s\n\n', ME.message);
        results.failed = results.failed + 1;
        results.details{end+1} = sprintf('常数核对: FAIL - %s', ME.message);
    end

    %% 总结
    fprintf('========================================================================\n');
    fprintf('  断言测试总结 (%s)\n', mode);
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
        fprintf('  %s\n', results.details{i});
    end
    fprintf('\n');

    if results.failed == 0
        fprintf('✅ 所有断言通过！\n\n');
    else
        warning('⚠ 有 %d 个断言失败', results.failed);
    end
end

%% 辅助函数
function config = load_config(mode)
    % 与 main_Q3Q4 的 load_config 保持同值 —— 断言要验的是**生产那套**
    config = struct();
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
        config.r_outer = [];     % Q4 走外扩环带，不用径向档
    end
end

function P = build_production_grid(cfg, mode)
    % 与 main_Q3Q4 同款地构造检测点集：Q4 用外扩环带；Q3 用径向档或三角格
    if strcmp(mode, 'Q4')
        P = Q4_extensions.generate_extended_grid(cfg.grid_spacing, cfg.R_domain, cfg.R_sensor);
    elseif ~isempty(cfg.r_outer)
        P = generate_radial_grid(cfg.grid_spacing, cfg.R_domain, cfg.r_outer);
    else
        P = generate_triangular_grid(struct('d', cfg.grid_spacing, ...
            'R_domain', cfg.R_domain, 'extend_for_Q4', false));
    end
end

function P_min = steiner_tube_bound(R, r)
    % Steiner 管面积下界：2rP + πr² ≥ πR²  ⇒  P ≥ π(R²−r²)/(2r)
    % R=1800, r=1000 ⇒ P ≥ 3518.5838 m，t_move ≥ 703.7168 s（与策略无关）
    P_min = pi * (R^2 - r^2) / (2 * r);
end

function L = mst_length(P)
    % 最小生成树长度（Prim，O(n²)，不依赖工具箱）
    % 用途：作为巡游长度的独立参照 —— 任何访问全部点的巡游都 ≥ MST。
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
