function q4_grid_search()
% q4_grid_search —— 细扫"内层格 + 外层正 n 边形环"的两个关键量：**余量**与 MST
%
% 现行 31 点设计的致命弱点之一是**余量为 0**（第三近邻最大恰 = R_eff = 1000）。
% 外层环换成正多边形后，环点之间/环点与内层点的距离都可调 ⇒ 余量可以做正。
%
% 输出：对每个 (r_ring, n_ring, phase) 报 N / 最远半径 / MST / surrounding 失败数 / **余量**
%   —— 选型标准：先要 surrounding 0 失败且余量 > 0，再取 MST 最小。

    R_domain = 1800;  R_eff = 1000;
    inner = lattice_inner(R_domain);      % 13 点

    rs = 1840:30:1960;
    ns = 11:14;
    phases = (0:5:29) * pi/180;

    rows = {};
    fprintf('\n%6s %4s %7s %4s %9s %7s %8s %8s\n', ...
        'r', 'n', 'phase°', 'N', 'MST(m)', 'surr', 'max3rd', 'margin');
    fprintf('%s\n', repmat('-', 1, 64));
    for r = rs
        for n = ns
            for ph = phases
                P = [inner; ring(r, n, ph)];
                [ok, f, ~, st] = Q4_extensions.check_surrounding_all(P, R_domain, R_eff, 25, false);
                rows{end+1} = struct('r', r, 'n', n, 'ph', ph, 'N', size(P,1), ...
                    'mst', mst_len(P), 'ok', ok, 'fail', f, ...
                    'max3', st.third_nearest_max, 'margin', st.margin, 'P', P);
            end
        end
    end

    good = rows(cellfun(@(x) x.ok, rows));
    fprintf('共 %d 个候选，surrounding 通过 %d 个\n', numel(rows), numel(good));
    if isempty(good)
        fprintf('无通过者\n'); return;
    end
    mg = cellfun(@(x) x.margin, good);
    ms = cellfun(@(x) x.mst, good);
    fprintf('通过者：余量 %.2f ~ %.2f m；MST %.0f ~ %.0f m\n', min(mg), max(mg), min(ms), max(ms));

    % 选型：余量 ≥ 10 m 里 MST 最小者
    idx = find(mg >= 10);
    if isempty(idx)
        fprintf('没有余量 ≥10 m 的候选，放宽到余量最大者\n');
        [~, kk] = max(mg);
    else
        [~, t] = min(ms(idx));  kk = idx(t);
    end
    b = good{kk};
    fprintf(['\n=== 选型：r_ring=%.0f, n_ring=%d, phase=%.1f° ⇒ %d 点，' ...
             'MST %.0f m，余量 %.2f m ===\n'], b.r, b.n, b.ph*180/pi, b.N, b.mst, b.margin);

    % 打印前 10 个（按余量≥10 后 MST 升序）
    if ~isempty(idx)
        [~, ord] = sort(ms(idx));
        idx = idx(ord);
        fprintf('\n余量 ≥ 10 m 的候选（按 MST 升序，前 10）：\n');
        fprintf('%6s %4s %7s %4s %9s %9s\n', 'r', 'n', 'phase°', 'N', 'MST(m)', 'margin');
        for i = 1:min(10, numel(idx))
            x = good{idx(i)};
            fprintf('%6.0f %4d %7.1f %4d %9.0f %9.2f\n', x.r, x.n, x.ph*180/pi, x.N, x.mst, x.margin);
        end
    end

    % 输出选型的点集源码
    P = b.P;  th = atan2(P(:,2), P(:,1));  [~, kk2] = sort(th);  P = P(kk2, :);
    fprintf('\n点集（按极角升序，N=%d）:\n', size(P,1));
    for i = 1:size(P,1)
        fprintf('    %10.4f, %10.4f; ...  %% r=%8.1f th=%7.2f\n', ...
            P(i,1), P(i,2), norm(P(i,:)), mod(th(kk2(i)), 2*pi)*180/pi);
    end
end


function P = lattice_inner(R_domain)
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
