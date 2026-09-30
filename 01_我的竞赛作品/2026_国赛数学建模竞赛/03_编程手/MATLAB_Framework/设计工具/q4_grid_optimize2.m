function out = q4_grid_optimize2()
% q4_grid_optimize2 —— 用"细格 + 贪心削减"求**更小的 surrounding 点集**（降 T̄ 主杠杆）
%
% 背景：31 点的规则三角格已是"格点意义下的极限"——Delaunay 边全 = 1000 = R_eff，
%   删任意一点都会让某些 G 的第三近邻 > 1000（`q4_grid_optimize` 实测 18 次删除全被拒）。
%   但它**不是点集意义下的最优**：12 个点落在 r=2645.8（圆域外 846 m），只为补
%   "圆盘边界切过的那几个三角"。
%
% 判据（与生产同一份 oracle）：∀G ∈ D(0,1800): G ∈ conv{p ∈ P : ‖p−G‖ ≤ 1000}
%   —— 抽样用 `Q4_extensions.check_surrounding_all`（25 m + 边界带加密）。
%   充分条件（Delaunay 视角）：D 的每个 Delaunay 三角形边长都 ≤ R_eff，
%   则三角形内任意 G 的三个顶点都在 1000 内且包围它。
%
% 做法：先用较细的三角格（d_fine < R_eff）在圆域附近铺出**冗余**点集，
%   再按"半径最大优先"逐点试删（每次删除都要 surrounding 仍然通过）。
%
% 用法: q4_grid_optimize2()   —— 打印最终点集（可直接抄进 MATLAB 常量表）

    R_domain = 1800;  R_eff = 1000;

    dfs = [820, 780, 740];          % 候选细格间距（越小冗余越多、初始点越多）
    best = struct('P', [], 'n', inf, 'mst', inf, 'd_fine', NaN, 'rmax', inf);

    for df = dfs
        P0 = fine_lattice(df, R_domain);
        fprintf('\n[d_fine=%.0f] 初始 %d 点，MST %.0f m，最远 %.1f m\n', ...
            df, size(P0,1), mst_len(P0), max(vecnorm(P0,2,2)));

        P1 = greedy_reduce(P0, R_domain, R_eff);
        m1 = mst_len(P1);
        rmax = max(vecnorm(P1, 2, 2));
        fprintf('[d_fine=%.0f] 削减后 %d 点，MST %.0f m，最远 %.1f m\n', ...
            df, size(P1,1), m1, rmax);

        % 二次洗牌（换个顺序再删，跳出贪心局部）
        for t = 1:2
            P2 = greedy_reduce(P1(randperm(size(P1,1)), :), R_domain, R_eff);
            if size(P2,1) < size(P1,1)
                P1 = P2;  m1 = mst_len(P1);  rmax = max(vecnorm(P1,2,2));
                fprintf('[d_fine=%.0f] 洗牌第%d轮后 %d 点，MST %.0f m，最远 %.1f m\n', ...
                    df, t, size(P1,1), m1, rmax);
            end
        end

        if size(P1,1) < best.n || (size(P1,1) == best.n && m1 < best.mst)
            best = struct('P', P1, 'n', size(P1,1), 'mst', m1, 'd_fine', df, 'rmax', rmax);
        end
    end

    fprintf('\n================ 最优 ================\n');
    fprintf('d_fine=%.0f ⇒ %d 点（原 31），MST %.0f m（原 30000），最远 %.1f m（原 2645.8）\n', ...
        best.d_fine, best.n, best.mst, best.rmax);
    [ok, f, w, st] = Q4_extensions.check_surrounding_all(best.P, R_domain, R_eff);
    fprintf('复检 surrounding: %s（失败 %d，全域 %.3f%%，边界带 %.3f%%，第三近邻最大 %.2f m）\n', ...
        tern(ok,'通过','失败'), f, 100*st.fail_rate, 100*st.fail_rate_band, st.third_nearest_max);

    % 按极角排序后打印，便于抄写与人工核对
    P = best.P;
    th = atan2(P(:,2), P(:,1));
    [~, k] = sort(th);
    P = P(k, :);
    fprintf('\n点集（按极角升序，N=%d）：\n', size(P,1));
    fprintf('Q4_GRID_OPT = [ ...\n');
    for i = 1:size(P,1)
        fprintf('    %9.4f, %9.4f; ...   %% r=%8.1f, theta=%7.2f deg\n', ...
            P(i,1), P(i,2), norm(P(i,:)), mod(th(k(i)))*180/pi);
    end
    fprintf('];\n');
    out = best;
end


function P = fine_lattice(df, R_domain)
% 细三角格，保留"到圆域距离 ≤ df"的点（= 覆盖圆域所需的最小三角格片）
    a1 = [df, 0];  a2 = [df/2, sqrt(3)*df/2];
    n = ceil((R_domain + 2*df) / df) + 2;
    P = zeros(0, 2);
    for i = -n:n
        for j = -n:n
            p = i*a1 + j*a2;
            r = norm(p);
            if r <= R_domain + df + 1e-9
                P(end+1, :) = p; %#ok<AGROW>
            end
        end
    end
    P = unique(round(P, 6), 'rows', 'stable');
end


function P = greedy_reduce(P0, R_domain, R_eff)
% 按"半径最大优先"逐点试删；删除后 surrounding 仍需通过
% （用 keep 掩码而不是就地删行 —— 就地删会让后面的索引全部串位）
    keep = true(size(P0, 1), 1);
    [~, order] = sort(vecnorm(P0, 2, 2), 'descend');
    for k = 1:numel(order)
        i = order(k);
        if sum(keep) <= 3, break; end
        cand = keep;  cand(i) = false;
        Pc = P0(cand, :);
        if cheap_ok(Pc, R_domain, R_eff) && full_ok(Pc, R_domain, R_eff)
            keep = cand;
        end
    end
    P = P0(keep, :);
end


function ok = cheap_ok(P, R_domain, R_eff)
% 粗筛（步长 100 m，不加密边界）：通过才做昂贵的全检
    Gs = Q4_extensions.sample_disk(R_domain, 100, false);
    ok = all(arrayfun(@(i) Q4_extensions.is_surrounding(Gs(i,:), P, R_eff), ...
                      1:size(Gs,1)));
end


function ok = full_ok(P, R_domain, R_eff)
    [ok, ~, ~, ~] = Q4_extensions.check_surrounding_all(P, R_domain, R_eff, 25, false);
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
