% ========================================================================
% test_Q4_extensions -- Q4 扩展回归（离线，不需要模拟器）
% 覆盖 V2.0 工作说明 §四 缺口 #2/#3 与建模手 E.3 的几何类断言：
%   T1 外扩环带生成 +  守卫（环带真的存在、没被裁回圆域）
%   T2 surrounding 全域自检（验收线 ①）
%   T3 is_surrounding 正反例
%   T4 死角反例：环带有可见点、圆内裁剪必无（验收线 ② / 定理 Q4-F）

function ok = test_Q4_extensions
    fprintf('\n');
    fprintf('========================================================================\n');
    fprintf(' Q4 扩展回归（离线）\n');
    fprintf('========================================================================\n\n');

    d = 1000;  R_domain = 1800;  R_eff = 1000;
    ok = true;

    %% T1 检测点集生成 +  守卫（两档都测）
    fprintf('[T1] 检测点集生成（ring 档 = 主；lattice 档 = 对照）...\n');
    [P, info] = Q4_extensions.generate_extended_grid(d, R_domain, R_eff, 'ring');
    ok = ok && expect(strcmp(info.ring_kind, 'regular_12gon'), 'ring 档应为正 12 边形环');
    ok = ok && expect(info.R_outer == R_domain + 100, '环半径应为 R_domain + 100 = 1900');
    ok = ok && expect(info.n_total == 25, sprintf('ring 档应为 25 点，实得 %d', info.n_total));
    ok = ok && expect(info.n_outside == 12, '圆外点应为 12（整圈环）');
    ok = ok && expect(info.max_norm > R_domain, '：最远点必须出圆域');
    fprintf(' ring: N=%d（内层 %d + 外层 %d），最远 %.1f m\n', ...
        info.n_total, info.n_base, info.n_ring, info.max_norm);

    [P31, info31] = Q4_extensions.generate_extended_grid(d, R_domain, R_eff, 'lattice');
    ok = ok && expect(info31.n_total == 31, 'lattice 档应为 31 点');
    ok = ok && expect(info31.margin == d, 'lattice 档外扩宽度应 = d');
    fprintf(' lattice: N=%d，最远 %.1f m（对照档）\n\n', info31.n_total, info31.max_norm);

    % MST 是移动成本的代理量 -- 本次优化的直接目标
    m_ring = mst_of(P);  m_lat = mst_of(P31);
    ok = ok && expect(m_ring < 0.7 * m_lat, ...
        sprintf('ring 档 MST 应显著小于 lattice 档：(%.0f vs %.0f)', m_ring, m_lat));
    fprintf(' MST: ring %.0f m | lattice %.0f m（降 %.0f%%）\n\n', ...
        m_ring, m_lat, 100 * (1 - m_ring / m_lat));

    %% T2 surrounding 全域自检
    fprintf('[T2] surrounding 自检（任意G  in  D: G  in  conv Q(G)）...\n');
    [s_ok, s_fail, ~, st] = Q4_extensions.check_surrounding_all(P, R_domain, R_eff);
    ok = ok && expect(s_ok, sprintf('surrounding 失败 %d 点（%.3f%%）', s_fail, 100*st.fail_rate));
    ok = ok && expect(st.fail_rate_band < 1e-12, '边界带必须 0 失败');
    fprintf(' 第三近邻最大 %.2f m，余量 %.2f m\n\n', st.third_nearest_max, st.margin);

    %% T3 is_surrounding 正反例
    fprintf('[T3] is_surrounding 正反例...\n');
    a = Q4_extensions.is_surrounding([0, 0], P, R_eff);
    b = Q4_extensions.is_surrounding([1790, 0], P, R_eff);
    c = Q4_extensions.is_surrounding([2600, 0], P, R_eff);      % 环带之外
    ok = ok && expect(a, 'G=(0,0) 应被 surrounding');
    ok = ok && expect(b, 'G=(1790,0) 边界带内应被 surrounding');
    ok = ok && expect(~c, 'G=(2600,0) 环带外不应被 surrounding');
    fprintf('\n');

    %% T4 死角反例（正面 / 反面）
    fprintf('[T4] 死角反例 G=(1800,0)、u=(1,0)...\n');
    dz = Q4_extensions.deadzone_case(P, R_domain, R_eff);
    ok = ok && expect(dz.passed, '环带网格必须能找到可见点');
    cc = Q4_extensions.clipped_grid_fails(R_domain, R_eff, d);
    ok = ok && expect(cc.passed, '圆内裁剪网格必须看不到该源（定理 Q4-F）');
    fprintf(' 环带可见点 %s（%d 个）；圆内 %d 点网格 0 个\n\n', ...
        mat2str(dz.witness), dz.n_hit, cc.n_points);

    %% T5 扇区探针引理（几何版）
    fprintf('[T5] 扇区探针引理：q± = p ± b·n̂ 至少一个仍在扇区...\n');
    rng(2026);
    b = 100;  n_bad = 0;  n_trial = 3000;
    for t = 1:n_trial
        psi = 2*pi*rand;
        u = [cos(psi), sin(psi)];
        r_p = 100 + (R_eff - 100) * rand;
        dth = (rand - 0.5) * pi;                  % 相对 u 的夹角  in  (−90度, 90度)
        p = r_p * [cos(psi + dth), sin(psi + dth)];
        th = atan2d(-p(2), -p(1));                % p 指向源 G=(0,0) 的方位角
        n_hat = [cosd(th + 90), sind(th + 90)];
        q = [p + b*n_hat; p - b*n_hat];
        if ~any((q * u') >= -1e-9), n_bad = n_bad + 1; end
    end
    ok = ok && expect(n_bad == 0, sprintf('引理被违反 %d/%d 次', n_bad, n_trial));
    fprintf(' %d 次随机试验全成立\n\n', n_trial);

    %% T6 扫掠中心集覆盖 L
    fprintf('[T6] 扫掠中心集覆盖 L（含顶点与边）...\n');
    rng(7);
    worst = 0;  n_bad6 = 0;
    for t = 1:40
        % 随机凸多边形（生产 L = 两角域 交 圆域 -> 必凸）；每 8 个夹一个非凸用例
        nv = 4 + randi(5);
        ang = sort(2*pi*rand(1, nv));
        rad = 25 + 60*rand(1, nv);
        Pv = [rad .* cos(ang); rad .* sin(ang)]';
        k = convhull(Pv(:, 1), Pv(:, 2));
        L = Pv(k(1:end - 1), :);
        if mod(t, 8) == 0
            c = mean(L, 1);
            [~, im] = max(vecnorm(L - c, 2, 2));
            L(im, :) = c + 0.35 * (L(im, :) - c);     % 凹口
        end
        C = sweep_centers(L, 20);
        S = sample_poly_local(L, 200);
        S = [S; edge_samples_local(L, 2)];
        g = 0;
        for kk = 1:size(S, 1)
            g = max(g, min(vecnorm(C - S(kk, :), 2, 2)));
        end
        worst = max(worst, g);
        if g > 20 + 1e-6, n_bad6 = n_bad6 + 1; end
    end
    ok = ok && expect(n_bad6 == 0, sprintf('%d/40 个 L 未被覆盖（最大空隙 %.2f m）', n_bad6, worst));
    fprintf(' 40 个随机 L 全被覆盖，最大空隙 %.2f m <= 20\n\n', worst);

    fprintf('========================================================================\n');
    if ok
        fprintf(' Q4 扩展回归全部通过\n');
    else
        fprintf(' Q4 扩展回归有失败项（见上）\n');
    end
    fprintf('========================================================================\n\n');
end

function tf = expect(cond, msg)
    if cond
        tf = true;
    else
        tf = false;
        fprintf(' %s\n', msg);
    end
end

function S = sample_poly_local(L, n_target)
    % 拒绝采样（包围盒撒点 + inpolygon）。旧的"质心射线法"会把点射到 L 外
    % （ 实测 200 点里 27~49 个在外）-> 断言假性失败。
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
    if size(S, 1) > n_target, S = S(1:n_target, :); end
end

function S = edge_samples_local(L, step)
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

function L = mst_of(P)
    n = size(P, 1);
    if n <= 1, L = 0; return; end
    inTree = false(n,1);  best = inf(n,1);  inTree(1) = true;
    for i = 2:n, best(i) = norm(P(i,:) - P(1,:)); end
    L = 0;
    for k = 2:n
        m = inf;  j = 0;
        for i = 1:n
            if ~inTree(i) && best(i) < m, m = best(i); j = i; end
        end
        if j == 0, break; end
        inTree(j) = true;  L = L + m;
        for i = 1:n
            if ~inTree(i)
                dd = norm(P(i,:) - P(j,:));
                if dd < best(i), best(i) = dd; end
            end
        end
    end
end
