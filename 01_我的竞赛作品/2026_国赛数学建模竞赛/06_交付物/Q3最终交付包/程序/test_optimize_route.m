% test_optimize_route —— 路径优化回归
%
% 用真实演练的几何数据钉住两处优化：阶段 A 的 NN+2-opt 取第一站、阶段 B 的就近重排。
% 谁把优化器改坏，这里立刻红。定档与实测
% 案例 C（递推取首站）专防"把 2-opt 外循环收紧成 i≥2"这类静默退化。
%
% 数据来源：`logs/robot_XX队号_20260912_204518.jsonl`（该局 12 源全 direct 清除，
%   故日志里的清除位置就是各源的 c_star）。
%
% 用法：test_optimize_route()   返回 ok

function ok = test_optimize_route()
    fprintf('\n===== 路径优化回归（真实演练几何）=====\n');
    results = {};

    %% 案例 A：13 个检测格点（d=1000），从原点出发
    P = generate_triangular_grid(struct('d', 1000, 'R_domain', 1800, 'extend_for_Q4', false));
    fprintf('  格点数 = %d\n', size(P, 1));

    route = optimize_route(P, [0; 0]);
    lenA = path_len(P, route, [0, 0]);
    % 改前实测（贪心）= 15464 m；改后应当 ≤ 12100 m
    results = chk(results, '案例A 2-opt 后行程 ≤ 12100 m（改前贪心 15464 m）', ...
        lenA <= 12100, sprintf('实得 %.0f m', lenA));
    results = chk(results, '案例A 是完整排列（每点恰访问一次）', ...
        is_perm(route, size(P, 1)), sprintf('route=%s', mat2str(route(:)')));

    %% 案例 B：12 个源（c_star，取自 2026-09-12 真实演练），从阶段 A 末点出发
    S = [ -186.5, -269.5; -892.7, 978.7; -997.8, 908.0; -883.0, 1302.9;
         -1550.8,  425.7;  489.2,1409.8; -223.4, 1264.4; 1088.4, -494.1;
          -225.0, -770.3; -1507.4,-690.1; -1558.1, -807.5; -1576.1, -674.1];
    from = [0, 1732.1];        % 阶段 A 的最后一个格点
    fprintf('  源点数 = %d，起点 = (%.1f, %.1f)\n', size(S, 1), from(1), from(2));

    % 原样（发现顺序）的行程 —— 复现"改前"的量级
    origB = 0; prev = from;
    for i = 1:size(S, 1)
        origB = origB + norm(S(i, :) - prev); prev = S(i, :);
    end

    routeB = optimize_route(S, from);
    lenB = path_len(S, routeB, from);
    fprintf('  案例B 原发现顺序 = %.0f m = %.0f s ｜ 重排后 = %.0f m = %.0f s\n', ...
        origB, origB/5, lenB, lenB/5);
    results = chk(results, '案例B 重排后行程 ≤ 8900 m（改前 13160 m）', ...
        lenB <= 8900, sprintf('实得 %.0f m', lenB));
    results = chk(results, '案例B 相对发现顺序确实更短', lenB < origB, ...
        sprintf('重排 %.0f vs 原样 %.0f', lenB, origB));
    results = chk(results, '案例B 是完整排列', is_perm(routeB, size(S, 1)), ...
        sprintf('route=%s', mat2str(routeB(:)')));

    results = chk(results, '两处合计省 ≥ 1500 s 虚拟时间', ...
        ((15464 - lenA) + (origB - lenB)) / 5 >= 1500, ...
        sprintf('实得 %.0f s', ((15464 - lenA) + (origB - lenB)) / 5));

    %% 案例 C：递推取首站（真实用法）—— 锁住 2-opt 邻域必须含 i=1
    %  main_Q3Q4.m 阶段 A/B 每步对「剩余格点 ∪ 待清源」跑一次 optimize_route，
    %  只取 ord(1) 当下一站，随后丢掉整条巡游、下一步重算。
    %  若把 twoopt_optimize 的外循环由 `i = 1:m-1` 收紧为 `i = 2:m-1`（"固定首目标"），
    %  则 index 1 永不参与任何反转，`ord(1)` 恒等于纯贪心最近邻，2-opt 对本用途完全失效:
    %  本案例的递推行程会从 12000 m 退化回 15464 m（+3464 m = +693 s）。
    % 案例 A/B 只断言整条巡游长度，而两种 2-opt 邻域下该长度相同
    % 只测全长的套件抓不到"把邻域收紧"的退化，故另设案例 C。
    rec = receding_len(P, [0 0]);
    fprintf('  案例C 递推取首站行程 = %.0f m = %.0f s（收紧邻域会退回 15464 m）\n', rec, rec / 5);
    results = chk(results, '案例C 递推取首站行程 ≤ 12100 m（锁 2-opt 邻域含 i=1）', ...
        rec <= 12100, sprintf('实得 %.0f m', rec));

    ok = true;
    fprintf('\n');
    for i = 1:numel(results)
        fprintf('  %s\n', results{i});
        if strncmp(results{i}, '[FAIL]', 6), ok = false; end
    end
    fprintf('  ---- optimize_route: %s ----\n', ternary(ok, '全部通过', '有失败'));
end

%% ---------------- 局部函数 ----------------

% 递推取首站：每步算完整巡游、只走 ord(1)，再重算 —— 复刻 main_Q3Q4.m 阶段 A/B 的用法
function total = receding_len(P, sp)
    cur = sp(:)'; total = 0; R = P;
    while ~isempty(R)
        ord = optimize_route(R, cur);
        p = R(ord(1), :);
        total = total + norm(p - cur); cur = p; R(ord(1), :) = [];
    end
end

function d = path_len(points, route, sp)
    d = 0; prev = sp(:)';
    for i = 1:numel(route)
        cur = points(route(i), :);
        d = d + norm(cur - prev);
        prev = cur;
    end
end

function tf = is_perm(route, n)
    r = route(:);
    tf = numel(r) == n && isequal(sort(r), (1:n)');
end

function r = chk(r, name, cond, detail)
    if nargin < 4, detail = ''; end
    if cond
        r{end+1} = sprintf('[PASS] %s', name);
    else
        r{end+1} = sprintf('[FAIL] %s  %s', name, detail);
    end
end

function out = ternary(c, a, b)
    if c, out = a; else, out = b; end
end
