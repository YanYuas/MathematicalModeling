function route = optimize_route(points, start_point)
%OPTIMIZE_ROUTE 对检测点集求访问顺序（开放路径：自 start_point 出发，不要求回到起点）。
%   route = OPTIMIZE_ROUTE(points, start_point)
%   points      N×2，每行一个点
%   start_point 1×2 或 2×1，起点坐标
%   route       访问顺序的索引向量（N×1）
%
%   先贪心最近邻构造初始解，再做 2-opt 局部优化。
%
%   注意 twoopt_optimize 的外循环必须从 i = 1 起：主循环每步只消费 ord(1)，
%   若把 i 限制为 ≥ 2，index 1 永不参与反转，ord(1) 会退化成纯贪心最近邻。
%   详见《Q3 调优经验与补丁记录》P-2。

    n = size(points, 1);
    if n == 0
        route = [];
        return;
    end

    sp = start_point(:)';

    % 贪心最近邻
    visited = false(n, 1);
    route = zeros(n, 1);
    current_pos = sp;
    for i = 1:n
        distances = inf(n, 1);
        for j = 1:n
            if ~visited(j)
                distances(j) = norm(points(j, :) - current_pos);
            end
        end
        [~, nearest_idx] = min(distances);
        route(i) = nearest_idx;
        visited(nearest_idx) = true;
        current_pos = points(nearest_idx, :);
    end

    route = twoopt_optimize(points, route, sp);
end


function route = twoopt_optimize(points, route, sp)
%TWOOPT_OPTIMIZE 2-opt 局部优化（开放路径，目标含"起点 → 首点"那一段）。

    best = path_length(points, route, sp);
    improved = true;
    while improved
        improved = false;
        m = numel(route);
        for i = 1:m - 1
            for j = i + 1:m
                cand = route;
                cand(i:j) = route(j:-1:i);      % 反转 i..j（i = 1 即换首点，合法）
                lc = path_length(points, cand, sp);
                if lc < best - 1e-9
                    route = cand;
                    best = lc;
                    improved = true;
                end
            end
        end
    end
end


function dist = path_length(points, route, sp)
%PATH_LENGTH 开放路径长度：自 sp 出发依次走 route，不回到 sp。

    dist = 0;
    prev = sp;
    for i = 1:numel(route)
        cur = points(route(i), :);
        dist = dist + norm(cur - prev);
        prev = cur;
    end
end
