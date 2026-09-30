function out = q4_grid_optimize()
% q4_grid_optimize —— 在不破坏 surrounding 的前提下**削减检测点集**（降 T̄ 的主杠杆）
%
% 动机（2026-09-13 真机 6 局实测）：T_vir ≈ 9.2k~10.8k s，其中**移动占 74~78%**；
%   总移动 36.4 km，而 31 个点的 MST 就是 30 km（三角格每个邻边恰 1000 m）。
%   31 点里有 **12 个在 r=2645.8**（圆域外 846 m）—— 若它们并非 surrounding 所必需，
%   删掉就能同时砍掉移动（MST 30→18 km）与检测（(20−k)·N·5）。
%
% 判据只能是 surrounding 本身（P 不再是规则格，`d ≤ R_eff` 那条件不再适用）：
%   ∀G ∈ D(0,1800): G ∈ conv{p ∈ P : ‖p−G‖ ≤ 1000}
% 用与生产同一份 `Q4_extensions.check_surrounding_all`（边界带加密）当 oracle。
%
% 用法: q4_grid_optimize()   —— 打印每一步削减与最终点集，并报告 MST / 理论巡游长度

    R_domain = 1800;  R_eff = 1000;  d = 1000;

    [P0, ~] = Q4_extensions.generate_extended_grid(d, R_domain, R_eff);
    fprintf('\n初始 P: %d 点，MST = %.0f m\n', size(P0, 1), mst_len(P0));

    % ---- 贪心削减：优先删"半径最大"的点（外环最贵） ----
    radius = vecnorm(P0, 2, 2);
    [~, order] = sort(radius, 'descend');
    keep = true(size(P0, 1), 1);
    n_check = 0;
    for k = 1:numel(order)
        i = order(k);
        if radius(i) <= R_domain + 1e-9
            continue;     % 圆内点先不动（它们是源附近唯一的三角包围）
        end
        cand = keep;  cand(i) = false;
        Pc = P0(cand, :);
        n_check = n_check + 1;
        [ok, ~, ~, ~] = Q4_extensions.check_surrounding_all(Pc, R_domain, R_eff);
        if ok
            keep = cand;
            fprintf('  删除 #%2d (r=%7.1f) ⇒ 剩 %2d 点，MST %5.0f m\n', ...
                i, radius(i), sum(keep), mst_len(P0(keep, :)));
        end
    end
    P1 = P0(keep, :);
    fprintf('外环贪心削减后: %d 点（检查 %d 次），MST %.0f m\n', ...
        size(P1, 1), n_check, mst_len(P1));

    % ---- 第二轮：对剩余点做一遍完整扫掠（含圆内点） ----
    changed = true;  pass = 0;
    while changed && pass < 3
        changed = false;  pass = pass + 1;
        for i = 1:size(P1, 1)
            cand = true(size(P1, 1), 1);  cand(i) = false;
            Pc = P1(cand, :);
            [ok, ~, ~, ~] = Q4_extensions.check_surrounding_all(Pc, R_domain, R_eff);
            if ok
                P1 = Pc;  changed = true;
                fprintf('  第%d轮再删一点 ⇒ 剩 %d 点，MST %.0f m\n', pass, size(P1,1), mst_len(P1));
                break;
            end
        end
    end

    fprintf('\n=== 结果 ===\n');
    fprintf('P* : %d 点（原 31）｜ MST %.0f m（原 30000）\n', size(P1, 1), mst_len(P1));
    fprintf('半径分布: %s\n', mat2str(round(sort(vecnorm(P1, 2, 2))')));
    fprintf('点集（按半径降序）:\n');
    rr = vecnorm(P1, 2, 2);
    [~, kk] = sort(rr, 'descend');
    for i = kk'
        fprintf('   (%8.1f, %8.1f)  r=%7.1f\n', P1(i,1), P1(i,2), rr(i));
    end

    % ---- 与"只留圆内 13 点"对照（应当失败，说明外环确实必需） ----
    P_in = P0(radius <= R_domain + 1e-9, :);
    [ok_in, f_in, w_in, ~] = Q4_extensions.check_surrounding_all(P_in, R_domain, R_eff);
    fprintf('\n对照：只留圆内 %d 点 ⇒ surrounding %s（失败 %d，首例 %s）\n', ...
        size(P_in,1), tern(ok_in,'通过','失败'), f_in, mat2str(round(w_in)));

    out = struct('P', P1, 'n0', size(P0,1), 'n1', size(P1,1), ...
                 'mst0', mst_len(P0), 'mst1', mst_len(P1));
end


function L = mst_len(P)
    n = size(P, 1);
    if n <= 1, L = 0; return; end
    inTree = false(n, 1);  best = inf(n, 1);
    inTree(1) = true;
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


function s = tern(c, a, b)
    if c, s = a; else, s = b; end
end
