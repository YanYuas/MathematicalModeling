function C = sweep_centers(L, dil)
%SWEEP_CENTERS 生成覆盖多边形 L 的半径 dil 圆盘中心集。
%   C = SWEEP_CENTERS(L, dil)
%   用途：扫掠清除（命题 Q4-C）。要在 L 上依次 /clear 并保证必有一次成功，
%   前提是 {cᵢ} 的 dil-圆盘覆盖整个 L（只盖 MEC 圆是不够的）。
%   构造：三角格间距 s = dil·sqrt(3) -> 外接圆半径 = s/sqrt(3) = dil（覆盖半径恰为一个清除半径）。
%   保留 dist(p, L) <= dil 的格点（含 L 内部与边界外一环）；再补 L 的顶点与边中点，

    if nargin < 2 || isempty(dil), dil = 20; end
    if isempty(L) || size(L, 1) < 3
        C = zeros(0, 2);
        return;
    end

    s = dil * sqrt(3);

    x0 = min(L(:, 1)); x1 = max(L(:, 1));
    y0 = min(L(:, 2)); y1 = max(L(:, 2));

    a1 = [s, 0];
    a2 = [s / 2, s * sqrt(3) / 2];
    n_i = ceil((x1 - x0) / s) + 2;
    n_j = ceil((y1 - y0) / s) + 2;

    C = zeros(0, 2);
    for i = -1:n_i
        for j = -1:n_j
            p = [x0, y0] + i * a1 + j * a2;
            if dist_point_poly(p, L) <= dil
                C(end + 1, :) = p; %#ok<AGROW>
            end
        end
    end

    % 顶点与边中点补强（盖住 L 的角）
    extra = L;
    n = size(L, 1);
    for k = 1:n
        k2 = mod(k, n) + 1;
        extra(end + 1, :) = (L(k, :) + L(k2, :)) / 2; %#ok<AGROW>
    end
    C = [C; extra];
    C = unique(round(C, 6), 'rows', 'stable');

    % 覆盖自检 + 贪心补点
    % 上面的"最近格点"论证只在 L 凸时成立；多边形有凹口时边界附近可能留缝
    % （实测：非凸 L 上留 118.5 m 的空隙）。生产 L 是两角域∩ 圆域
    % -> 凸，但这里不依赖该前提：直接沿边界密集采样验一遍，有缝就把该点补成中心。
    for pass = 1:2
        S = boundary_samples(L);
        gap = zeros(size(S, 1), 1);
        for k = 1:size(S, 1)
            gap(k) = min(vecnorm(C - S(k, :), 2, 2));
        end
        bad = S(gap > dil, :);
        if isempty(bad), break; end
        C = unique(round([C; bad], 6), 'rows', 'stable');
    end
end


function S = boundary_samples(L)
%BOUNDARY_SAMPLES 沿 L 的每条边按 ~=2 m 步长采样（含顶点），用于覆盖自检。
    n = size(L, 1);
    S = zeros(0, 2);
    for k = 1:n
        k2 = mod(k, n) + 1;
        a = L(k, :); b = L(k2, :);
        m = max(2, ceil(norm(b - a) / 2));
        t = linspace(0, 1, m + 1); t(end) = [];
        S = [S; a + t' * (b - a)]; %#ok<AGROW>
    end
end


function d = dist_point_poly(p, V)
%DIST_POINT_POLY 点到多边形（含内部）的距离；内部返回 0。
%  内部判定用射线法（不假设凸）-- 生产 L 是凸的，但这里不依赖该前提。
    n = size(V, 1);
    d = inf;
    for k = 1:n
        k2 = mod(k, n) + 1;
        d = min(d, dist_point_seg(p, V(k, :), V(k2, :)));
    end
    if d > 0 && inpoly_local(p, V)
        d = 0;
    end
end


function tf = inpoly_local(p, V)
%INPOLY_LOCAL 射线法判点在多边形内（含边界由调用方的 d>0 短路处理）。
    tf = false;
    n = size(V, 1);
    x = p(1); y = p(2);
    j = n;
    for i = 1:n
        xi = V(i, 1); yi = V(i, 2);
        xj = V(j, 1); yj = V(j, 2);
        if ((yi > y) ~= (yj > y)) && ...
                (x < (xj - xi) * (y - yi) / (yj - yi) + xi)
            tf = ~tf;
        end
        j = i;
    end
end


function d = dist_point_seg(p, a, b)
%DIST_POINT_SEG 点到线段距离。
    ab = b - a;
    L2 = ab * ab';
    if L2 < 1e-12
        d = norm(p - a);
        return;
    end
    t = max(0, min(1, ((p - a) * ab') / L2));
    d = norm(p - (a + t * ab));
end
