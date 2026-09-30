function cmp_twoopt_firststop()
% ========================================================================
% cmp_twoopt_firststop.m —— 2-opt 邻域对比：A（现状） vs B（编程手提案）
% ========================================================================
% 背景：编程手在 D:\QQ\QQ Files\optimize_route.m 把 twoopt_optimize 的外循环
%   由 i = 1:m-1 收紧为 i = 2:m-1（"固定首目标 route(1)"）。
%   —— 这是**收紧邻域**：整条巡游长度只可能变长或持平。
%
% 本仓库的真实用法（main_Q3Q4.m 阶段 A/B）：每步对「剩余格点 ∪ 待清源」跑一次
%   optimize_route，**只取 ord(1) 当下一站**，随后丢掉整条巡游、下一步重算。
%   ⇒ 决定性指标不是整条巡游长度，而是**递推取首站**下的总行程。
%
% 可证事实（本脚本实测钉死）：B 下 index 1 永不参与任何反转 ⇒ ord(1) 恒等于
%   纯贪心最近邻 ⇒ **B 的 2-opt 对"下一站"完全失效**，递推取首站 ≡ 纯 NN。
%
% 三组实验：
%   (1) 整条巡游长度（参考）
%   (2) 网格-only 递推巡游（每局开头的必经历程）
%   (3) 随机动态重放（合成 源位置 + 发现时序），给出 Δ = A − B 的分布
%
% 用法：cmp_twoopt_firststop()
% ========================================================================

    diary off; logf = fullfile(fileparts(mfilename('fullpath')), 'cmp_twoopt_out.txt');
    if exist(logf, 'file'), delete(logf); end
    diary(logf); diary on;

    fprintf('===== 2-opt 邻域对比：A(i=1:m-1, 现状) vs B(i=2:m-1, 编程手提案) =====\n');

    G13 = tri_grid(1000, 1800);
    S12 = [ -186.5, -269.5; -892.7, 978.7; -997.8, 908.0; -883.0, 1302.9;
            -1550.8,  425.7;  489.2,1409.8; -223.4, 1264.4; 1088.4, -494.1;
             -225.0, -770.3; -1507.4,-690.1; -1558.1, -807.5; -1576.1, -674.1];
    M25 = [G13; S12];
    fprintf('  格点 G13 = %d ｜ 真实源 S12 = %d ｜ 混合 M25 = %d ｜ 移动速度 5 m/s\n\n', ...
        size(G13,1), size(S12,1), size(M25,1));

    %% ---------- (0) 可证事实：B 的 ord(1) 恒等于纯 NN ----------
    fprintf('--- (0) B 的 ord(1) 是否恒等于纯贪心最近邻 ---\n');
    R = M25; cur = [0 0]; nbad = 0; nstep = 0;
    while ~isempty(R)
        oB = opt(R, cur, 'B'); oN = opt(R, cur, 'N');
        if oB(1) ~= oN(1), nbad = nbad + 1; end
        nstep = nstep + 1; cur = R(oB(1), :); R(oB(1), :) = [];
    end
    fprintf('  B vs 无2-opt：%d 步中 ord(1) 不同 %d 步  %s\n', nstep, nbad, ...
        tern(nbad==0, '【确认 B ≡ 纯 NN，2-opt 对首站无效】', '【有偏离(异常)】'));
    R = M25; cur = [0 0]; nchg = 0;
    while ~isempty(R)
        oA = opt(R, cur, 'A'); oN = opt(R, cur, 'N');
        if oA(1) ~= oN(1), nchg = nchg + 1; end
        cur = R(oA(1), :); R(oA(1), :) = [];
    end
    fprintf('  A vs 无2-opt：同 %d 步中 ord(1) 不同 %d 步（= 2-opt 真正改变"下一站"的次数）\n\n', nstep, nchg);

    %% ---------- (1) 整条巡游长度（参考） ----------
    fprintf('--- (1) 整条巡游长度（只有 ord(1) 被消费，仅供参考） ---\n');
    cases = { 'G13 (网格, sp=原点)',            G13, [0 0];
              'S12 (真实源, sp=(0,1732.1))',    S12, [0 1732.1];
              'M25 (G13∪S12, sp=原点)',         M25, [0 0];
              'M25 (G13∪S12, sp=(0,1732.1))',   M25, [0 1732.1] };
    fprintf('  %-30s %11s %11s %9s\n', '点集/起点', 'A 长度(m)', 'B 长度(m)', 'A-B');
    for c = 1:size(cases,1)
        P = cases{c,2}; sp = cases{c,3};
        rA = opt(P, sp, 'A'); rB = opt(P, sp, 'B');
        fprintf('  %-30s %11.0f %11.0f %9.0f\n', cases{c,1}, ...
            plen(P,rA,sp), plen(P,rB,sp), plen(P,rA,sp)-plen(P,rB,sp));
    end

    %% ---------- (2) 网格-only 递推巡游 ----------
    fprintf('\n--- (2) 网格-only 递推巡游（每局开头必经历程） ---\n');
    [tA, hA] = receding(G13, [0 0], 'A');
    [tB, hB] = receding(G13, [0 0], 'B');
    fprintf('  A 总行程 = %.0f m = %.1f s ｜ B 总行程 = %.0f m = %.1f s\n', tA, tA/5, tB, tB/5);
    fprintf('  Δ = A - B = %.0f m = %.1f s   （负 = A 更省；此处 A 省 %.0f s）\n', ...
        tA-tB, (tA-tB)/5, (tB-tA)/5);
    fprintf('  步数 = %d ｜ B 的 ord(1) 偏离 NN 次数 = %d\n', size(G13,1), hB);

    %% ---------- (3) 随机动态重放：Δ 分布 ----------
    fprintf('\n--- (3) 随机动态重放（合成源 + 就近发现），%d 局 ---\n', 120);
    rng(20260913);
    nTrial = 120; dA = zeros(nTrial,1); dB = zeros(nTrial,1);
    for t = 1:nTrial
        k = randi([10 16]);
        ang = 2*pi*rand(k,1); rad = 1800*sqrt(rand(k,1));
        S = [rad.*cos(ang), rad.*sin(ang)];
        [dA(t), ~] = replay(G13, S, [], 'A');
        [dB(t), ~] = replay(G13, S, [], 'B');
    end
    dd = dA - dB;      % dd > 0 ⇒ A 行程更长 ⇒ B 更省
    fprintf('  Δ = A - B（m，正 = A 更差）：均值 %.0f ｜ 最小 %.0f ｜ p05 %.0f ｜ 中位 %.0f ｜ p95 %.0f ｜ 最大 %.0f\n', ...
        mean(dd), min(dd), prctile(dd,5), median(dd), prctile(dd,95), max(dd));
    fprintf('  Δ（秒）：      均值 %.1f ｜ 最小 %.1f ｜ p95 %.1f ｜ 最大 %.1f\n', ...
        mean(dd)/5, min(dd)/5, prctile(dd,95)/5, max(dd)/5);
    fprintf('  ★ A 更省的局数 = %d / %d ｜ B 更省的局数 = %d ｜ 持平 = %d\n', ...
        sum(dd<0), nTrial, sum(dd>1e-6), sum(abs(dd)<=1e-6));
    fprintf('  A 总行程 均值 %.0f m ｜ B 总行程 均值 %.0f m（B 相对 A %+.2f%%）\n', ...
        mean(dA), mean(dB), 100*(mean(dB)-mean(dA))/mean(dA));
    fprintf('  B 的平均代价 = %+.1f s/局 ｜ A 的平均收益 = %+.1f s/局\n', ...
        mean(dd)/5, -mean(dd)/5);

    fprintf('\n');
    diary off;
end

%% ---------------- 局部函数 ----------------

function P = tri_grid(d, R)
    a1 = [d, 0]; a2 = [d/2, sqrt(3)*d/2];
    n_max = ceil(R/d) + 1; pts = [];
    for i = -n_max:n_max
        for j = -n_max:n_max
            p = i*a1 + j*a2;
            if norm(p) <= R, pts = [pts; p]; end
        end
    end
    P = unique(pts, 'rows', 'stable');
end

function len = plen(P, route, sp)
    len = 0; prev = sp(:)';
    for i = 1:numel(route)
        cur = P(route(i), :);
        len = len + norm(cur - prev); prev = cur;
    end
end

% mode: 'A' = i=1:m-1（现状）；'B' = i=2:m-1（编程手提案）；'N' = 不做 2-opt
function route = opt(P, sp, mode)
    n = size(P,1);
    if n == 0, route = []; return; end
    sp = sp(:)';
    visited = false(n,1); route = zeros(n,1); cur = sp;
    for i = 1:n
        dd = inf(n,1);
        for j = 1:n
            if ~visited(j), dd(j) = norm(P(j,:) - cur); end
        end
        [~, k] = min(dd); route(i) = k; visited(k) = true; cur = P(k,:);
    end
    if strcmp(mode,'N'), return; end
    if strcmp(mode,'A'), i0 = 1; else, i0 = 2; end
    best = plen(P, route, sp); improved = true;
    while improved
        improved = false; m = numel(route);
        for i = i0:m-1
            for j = i+1:m
                cand = route; cand(i:j) = route(j:-1:i);
                lc = plen(P, cand, sp);
                if lc < best - 1e-9
                    route = cand; best = lc; improved = true;
                end
            end
        end
    end
end

% 递推取首站：每步算完整巡游、只走 ord(1)，再重算。返回 [总行程, 偏离NN步数]
function [total, hits] = receding(P, sp, mode)
    R = P; cur = sp(:)'; total = 0; hits = 0;
    while ~isempty(R)
        ord = opt(R, cur, mode);
        oN  = opt(R, cur, 'N');
        if ord(1) ~= oN(1), hits = hits + 1; end
        p = R(ord(1), :);
        total = total + norm(p - cur); cur = p; R(ord(1), :) = [];
    end
end

% 动态重放：任务表 = 剩余格点 ∪ 已发现未清源。
%   发现规则贴近真机：机器狗在每个格点扫全部 20 个频道 ⇒ 任一未清除源只要
%   距当前格点 ≤ R_eff(=1000 m) 即在本步被发现（此后进任务表）。
%   源的"位置"用 c_star 代表；走到其 c_star 即视为清除（只比路由，不含测量/清除耗时）。
function [total, nstep] = replay(G, S, ~, mode)
    R_eff = 1000;
    k = size(S,1);
    cur = [0 0]; total = 0; nstep = 0;
    gRem = G; sRem = zeros(0,2); sIdx = [];
    found = false(k,1);
    [found, sRem, sIdx] = reveal(cur, S, found, sRem, sIdx, R_eff);
    while ~isempty(gRem) || ~isempty(sRem)
        tasks = [gRem; sRem];
        if isempty(tasks), break; end
        ord = opt(tasks, cur, mode);
        p = tasks(ord(1), :);
        total = total + norm(p - cur); cur = p; nstep = nstep + 1;
        if ord(1) <= size(gRem,1)
            gRem(ord(1), :) = [];
        else
            j = ord(1) - size(gRem,1);      % sRem 中的行号
            found(sIdx(j)) = true;          % 已清除 ⇒ 不再被发现
            sRem(j, :) = []; sIdx(j) = [];
        end
        [found, sRem, sIdx] = reveal(cur, S, found, sRem, sIdx, R_eff);
    end
end

function [found, sRem, sIdx] = reveal(cur, S, found, sRem, sIdx, R_eff)
    for i = 1:size(S,1)
        if ~found(i) && norm(S(i,:) - cur) <= R_eff
            found(i) = true;
            if ~any(sIdx == i)
                sRem(end+1,:) = S(i,:); sIdx(end+1) = i; %#ok<AGROW>
            end
        end
    end
end

function out = tern(c, a, b)
    if c, out = a; else, out = b; end
end
