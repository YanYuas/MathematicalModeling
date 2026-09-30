function route = optimize_route(points, start_point)
%OPTIMIZE_ROUTE 对检测点集求访问顺序（开放路径：自 start_point 出发，不要求回到起点）。
%   route = OPTIMIZE_ROUTE(points, start_point)
%   points      N×2，每行一个点
%   start_point 1×2 或 2×1，起点坐标
%   route       访问顺序的索引向量（N×1）
%   从"单一贪心初始解 + 2-opt"改为"三个初始解各做 2-opt + Or-opt，取最优"。
%   依据（实机 7 局统计）：实走行程 / MST 下界 = 1.344（31 点档 1.292）。

    n = size(points, 1);
    if n == 0
        route = [];
        return;
    end
    if n == 1
        route = 1;
        return;
    end

    sp = start_point(:)';

    best_len = inf;
    route = (1:n)';
    styles = {'nn', 'sweep_ccw', 'sweep_cw'};
    for k = 1:numel(styles)
        r0 = initial_route(points, sp, styles{k});
        r1 = twoopt_optimize(points, r0, sp);
        r2 = or_opt(points, r1, sp);
        L = path_length(points, r2, sp);
        if L < best_len - 1e-9
            best_len = L;
            route = r2;
        end
    end
end


function route = initial_route(points, sp, style)
%INITIAL_ROUTE 三种初始巡游骨架
    n = size(points, 1);
    switch style
        case 'nn'
            route = nn_route(points, sp);
        otherwise
            % 极角扫描：以点集质心为极点排序（本点集是"环 + 内点"，
            % 质心 ~= 圆域中心 -> 按角序走天然沿着环）
            c = mean(points, 1);
            th = atan2(points(:, 2) - c(2), points(:, 1) - c(1));
            [~, ord] = sort(th);
            if strcmp(style, 'sweep_cw')
                ord = flipud(ord);
            end
            % 旋转到"离起点最近的那个点"开头（直道起步，不绕回原点）
            d = sum((points(ord, :) - sp).^2, 2);
            [~, k0] = min(d);
            route = [ord(k0:end); ord(1:k0 - 1)];
    end
end


function route = nn_route(points, sp)
%NN_ROUTE 贪心最近邻（原版初始解）
    n = size(points, 1);
    visited = false(n, 1);
    route = zeros(n, 1);
    cur = sp;
    for i = 1:n
        dd = inf(n, 1);
        for j = 1:n
            if ~visited(j)
                dd(j) = norm(points(j, :) - cur);
            end
        end
        [~, k] = min(dd);
        route(i) = k;
        visited(k) = true;
        cur = points(k, :);
    end
end


function route = twoopt_optimize(points, route, sp)
%TWOOPT_OPTIMIZE 2-opt 局部优化（开放路径，目标含"起点 -> 首点"那一段）。
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


function route = or_opt(points, route, sp)
%OR_OPT 片段插入局部优化（片段长 1~3，开放路径，目标含"起点 -> 首点"）。
%  2-opt 只能反转一段；Or-opt 能把一段整体搬到别处 -- 这是 2-opt 抓不到的动作。
%  片段长 1~3：早期版本只做片段长 1，扩展到 1~3 后是严格更强的邻域。
%  接受改进后整轮重来：插入会改变下标，
%  继续用旧 i 会造出重复点。
    n = numel(route);
    if n < 4
        return;
    end
    best = path_length(points, route, sp);
    improved = true;
    while improved
        improved = false;
        done = false;
        m = numel(route);
        for seglen = 1:3
            for i = 1:(m - seglen + 1)
                seg = route(i:i + seglen - 1);
                rest = route;  rest(i:i + seglen - 1) = [];
                for pos = 0:numel(rest)
                    cand = [rest(1:pos); seg(:); rest(pos + 1:end)];
                    lc = path_length(points, cand, sp);
                    if lc < best - 1e-9
                        route = cand;  best = lc;
                        improved = true;  done = true;  break;
                    end
                end
                if done, break; end
            end
            if done, break; end
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
