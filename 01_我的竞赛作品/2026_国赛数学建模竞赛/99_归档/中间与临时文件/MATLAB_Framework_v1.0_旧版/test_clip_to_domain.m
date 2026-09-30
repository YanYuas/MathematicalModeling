% test_clip_to_domain —— 圆域截断回归
%
% 钉死一类静默缺陷：细长交会区被"截断"成退化多边形，R_MEC 假性偏小，清除误派发。
% 用真机事故（20260913_084008 频道 5）的真实输入：两个观测夹角仅 2.2°。
% 断言：L 不得退化成 2 点、真源必须在 L 内、R_MEC ≥ 真源到 c* 的距离、档位应为 homing。
% 另附正交观测对照组，防止截断被改坏。事故复盘
%
% 用法：test_clip_to_domain()   返回 ok

function ok = test_clip_to_domain()
    fprintf('\n===== 圆域截断回归（退化交会事故）=====\n');
    results = {};

    cfg = struct('R_domain', 1800, 'epsilon_deg', 1);

    % 真机事故的真实输入（角度、位置逐字取自日志）
    obs = struct('position_id', 1, 'position', [-1000, 0],    'channel', 5, 'svd_deg', 98.92);
    obs(2) = struct('position_id', 7, 'position', [-1125.8, 650], 'channel', 5, 'svd_deg', 96.72);

    % 真源位置：由事后"清除成功点" (-1186.4, 1166.5) 反推（±20 m 清除半径内）
    G = [-1186.4, 1166.5];

    s = triangulate_source(obs, cfg);
    results = chk(results, '交会不为空', ~isempty(s), '（返回空 ⇒ 该对观测无法定位）');

    if ~isempty(s)
        nv = size(s.L, 1);
        fprintf('  L 顶点数 = %d ｜ c* = (%.2f, %.2f) ｜ R_MEC = %.4f m\n', ...
            nv, s.c_star(1), s.c_star(2), s.R_MEC);

        % ① 不得退化
        results = chk(results, 'L 顶点数 ≥ 3（旧版退化成 2 ⇒ R_MEC 假性偏小）', ...
            nv >= 3, sprintf('实得 %d', nv));

        % ② 真源必须在 L 内（旧版为 0 = 否）
        inside = inpolygon(G(1), G(2), s.L(:, 1), s.L(:, 2));
        results = chk(results, '真源在 L 内（旧版 否）', inside, ...
            sprintf('实得 %d', inside));

        % ③ R_MEC ≥ 真源到 c* 的距离（L 含源，必成立）
        dc = norm(G - s.c_star(:)');
        results = chk(results, sprintf('R_MEC(%.2f) ≥ 真源到 c*(%.2f)', s.R_MEC, dc), ...
            s.R_MEC >= dc - 1e-6, sprintf('差 %.2f m', dc - s.R_MEC));

        % ④ 派发档位：R_MEC 必须 > R_star，走 homing（旧版 74.12，误判为 sweep）
        results = chk(results, 'R_MEC > R_star=84.0369 ⇒ 清除走 homing（旧版误走 sweep）', ...
            s.R_MEC > 84.0369, sprintf('实得 R_MEC=%.2f', s.R_MEC));
    end

    % ⑤ 正常情形不得被改坏：两个近乎正交的观测，L 应含真源、R_MEC 合理
    %   射线1：从 (-1000,0) 沿 0°，直线 y=0
    %   射线2：从 (0,1000) 沿 270°，直线 x=0，交点 (0,0)
    obsA = struct('position_id', 1, 'position', [-1000, 0], 'channel', 3, 'svd_deg', 0);
    obsA(2) = struct('position_id', 5, 'position', [0, 1000], 'channel', 3, 'svd_deg', 270);
    sA = triangulate_source(obsA, cfg);
    gA = [0, 0];
    if ~isempty(sA)
        fprintf('  [对照] 正交观测：L 顶点 %d ｜ c* = (%.2f, %.2f) ｜ R_MEC = %.4f m\n', ...
            size(sA.L, 1), sA.c_star(1), sA.c_star(2), sA.R_MEC);
        results = chk(results, '对照：正交观测下真源 (0,0) 仍在 L 内', ...
            inpolygon(gA(1), gA(2), sA.L(:, 1), sA.L(:, 2)), '');
    else
        results = chk(results, '对照：正交观测应能定位', false, '返回空');
    end

    ok = true;
    fprintf('\n');
    for i = 1:numel(results)
        fprintf('  %s\n', results{i});
        if strncmp(results{i}, '[FAIL]', 6), ok = false; end
    end
    fprintf('  ---- clip_to_domain: %s ----\n', tern(ok, '全部通过', '有失败'));
end

%% ---------------- 局部函数 ----------------
function r = chk(r, name, cond, detail)
    if cond
        r{end+1} = sprintf('[PASS] %s', name);
    else
        r{end+1} = sprintf('[FAIL] %s  %s', name, detail);
    end
end

function out = tern(c, a, b)
    if c, out = a; else, out = b; end
end
