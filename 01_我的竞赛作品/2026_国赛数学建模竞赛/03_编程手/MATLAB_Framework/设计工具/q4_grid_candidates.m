function q4_grid_candidates()
% q4_grid_candidates —— 测试若干**手工设计**的点集（比规则格更贴圆域，点数更少）
%
% 动机：规则三角格在圆域外一路铺到 r=2645.8（12 个点），只为补"边界切过的那几个三角"。
%   这些点是移动成本的主来源（31 点 MST 恰 30 km，其中 12 km 挂在这 12 个点上）。
%   改成"内层用格、外层用贴圆的多边形环"应当同时更少、更近。
%
% 每个候选都过同一份 surrounding oracle，并报点数 / 最远半径 / MST。

    R_domain = 1800;  R_eff = 1000;

    cands = {};
    % --- 内层：格（1 + 6@1000 + 6@1732.05）；外层：n 边形环（角度相移可选） ---
    inner = lattice_inner(R_domain);
    for Rr = [1900, 2000, 2100, 2200]
        for nr = [12, 16, 18]
            for ph = [0, pi/nr]
                P = [inner; ring(Rr, nr, ph)];
                cands{end+1} = struct('name', sprintf('格内%d + %d边形 r=%.0f 相移%.0f°', ...
                    size(inner,1), nr, Rr, ph*180/pi), 'P', P);
            end
        end
    end
    % --- 对照：只内层 ---
    cands{end+1} = struct('name', sprintf('只内层 %d 点', size(inner,1)), 'P', inner);
    % --- 对照：现行 31 点 ---
    P31 = Q4_extensions.generate_extended_grid(1000, R_domain, R_eff);
    cands{end+1} = struct('name', '现行 31 点（规则格）', 'P', P31);

    fprintf('\n%-34s %4s %9s %9s %6s %9s %9s\n', ...
        '候选', 'N', '最远r', 'MST(m)', 'surr', '全域失败%', '边界失败%');
    fprintf('%s\n', repmat('-', 1, 92));
    results = {};
    for i = 1:numel(cands)
        P = cands{i}.P;
        [ok, f, ~, st] = Q4_extensions.check_surrounding_all(P, R_domain, R_eff, 25, false);
        m = mst_len(P);
        fprintf('%-34s %4d %9.1f %9.0f %6s %9.3f %9.3f\n', cands{i}.name, ...
            size(P,1), max(vecnorm(P,2,2)), m, tern(ok,'OK','FAIL'), ...
            100*st.fail_rate, 100*st.fail_rate_band);
        results{end+1} = struct('name', cands{i}.name, 'P', P, 'n', size(P,1), ...
                                'mst', m, 'ok', ok, 'fail', f);
    end

    % 打印通过的候选里 MST 最小的那个的点集
    good = results(cellfun(@(r) r.ok, results));
    if isempty(good)
        fprintf('\n没有候选通过 surrounding。\n');
        return;
    end
    [~, k] = min(cellfun(@(r) r.mst, good));
    b = good{k};
    fprintf('\n=== 通过者中 MST 最小：%s（%d 点，MST %.0f m）===\n', b.name, b.n, b.mst);
    P = b.P;  th = atan2(P(:,2), P(:,1));  [~, kk] = sort(th);  P = P(kk,:);
    for i = 1:size(P,1)
        fprintf('    %10.4f, %10.4f; ...  %% r=%8.1f th=%7.2f\n', ...
            P(i,1), P(i,2), norm(P(i,:)), mod(th(kk(i)))*180/pi);
    end
end


function P = lattice_inner(R_domain)
% 圆域内的规则三角格（1 + 6@1000 + 6@1732.05）
    d = 1000;
    a1 = [d, 0];  a2 = [d/2, sqrt(3)*d/2];
    n = 3;  P = zeros(0, 2);
    for i = -n:n
        for j = -n:n
            p = i*a1 + j*a2;
            if norm(p) <= R_domain + 1e-9, P(end+1,:) = p; end %#ok<AGROW>
        end
    end
    P = unique(round(P, 6), 'rows', 'stable');
end


function P = ring(R, n, phase)
    th = phase + (0:n-1)' * 2*pi/n;
    P = [R*cos(th), R*sin(th)];
end


function L = mst_len(P)
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


function s = tern(c, a, b)
    if c, s = a; else, s = b; end
end
