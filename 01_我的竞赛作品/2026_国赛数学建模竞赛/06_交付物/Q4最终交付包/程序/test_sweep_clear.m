% ========================================================================
% test_sweep_clear.m -- 扫掠清除（扇区无关 · 覆盖 L）回归
% ========================================================================
% 为什么单独测：离线基线里 sweep 曾经"一次都没执行"（13 次清除全是 direct），
%   而真机里它明确发生过（q3 真机日志 ch=13 以 20 m 网格螺旋外扩，试了 19 次才命中）。
% 扫掠从"沿示向度定向短走"改为用 20 m 圆盘覆盖整个 L。
%   理由：定向源盲侧永不返回 near（附录2(9)），依赖示向度的短走会断线；

function ok = test_sweep_clear(port)
    if nargin < 1 || isempty(port), port = 20267; end

    fprintf('\n===== sweep_clear 覆盖 L 回归（geo mock，真源 (300,400)）=====\n');

    logdir = fullfile(tempdir, 'sclog_sweep');
    if exist(logdir, 'dir'), rmdir(logdir, 's'); end

    G = [300, 400];
    L = [G(1) - 30, G(2) - 30; G(1) + 30, G(2) - 30; ...
         G(1) + 30, G(2) + 30; G(1) - 30, G(2) + 30];
    [c_star, R_MEC] = Q1_geometry.minimum_enclosing_circle(L);
    fprintf('  构造 L：以真源为中心的 60×60 方块 -> c*=(%.1f,%.1f), R_MEC=%.2f m\n', ...
        c_star(1), c_star(2), R_MEC);

    cfg = struct('R_clear', 20, 'R_star', 84.0369, 'R_sweep_fallback_max', 250, ...
                 'coverage_density', 2*pi/(3*sqrt(3)), ...
                 'T_measure', 5, 'T_switch', 1, 'T_clear_success', 5, 'T_clear_fail', 3, ...
                 'epsilon_deg', 1, 'R_domain', 1800, 'time_reserve', 60, ...
                 'R_homing_step_max', 300, 'homing_max_iter', 12, 'homing_max_move', 2500);

    threw = false; errmsg = ''; success = false; logpath = ''; mode_used = ''; c = [];
    try
        c = SimulatorClient(sprintf('http://127.0.0.1:%d', port), 'TESTTEAM', logdir);
        c.enter;
        source = struct('channel', 7, 'L', L, 'c_star', c_star, 'R_MEC', R_MEC, 'D', 60);
        [success, ~, mode_used] = clear_source(source, c, cfg);
        logpath = c.get_log_path;
        c.close_log;
    catch ME
        threw = true; errmsg = sprintf('%s: %s', ME.identifier, ME.message);
        try, logpath = c.get_log_path; c.close_log; catch, end
    end

    % ---- 从日志量 /clear 次数、落点 ----
    recs = read_jsonl(logpath);
    nclear = 0; nmeas = 0; travel = 0; prev = [];
    clear_pos = zeros(0, 2);
    for i = 1:numel(recs)
        if ~(isfield(recs{i}, 'kind') && strcmp(recs{i}.kind, 'request')), continue; end
        ep = ''; if isfield(recs{i}, 'endpoint'), ep = recs{i}.endpoint; end
        if strcmp(ep, '/clear'), nclear = nclear + 1; end
        if strcmp(ep, '/measure'), nmeas = nmeas + 1; end
        p = [];
        if isfield(recs{i}, 'request_payload')
            rp = recs{i}.request_payload;
            if isstruct(rp) && isfield(rp, 'position') && isstruct(rp.position)
                p = [rp.position.x, rp.position.y];
            end
        end
        if ~isempty(p)
            if strcmp(ep, '/clear'), clear_pos(end + 1, :) = p; end %#ok<AGROW>
            if ~isempty(prev), travel = travel + norm(p - prev); end
            prev = p;
        end
    end

    % 命中点（最后一次 /clear 的落点）与真源的距离
    hit_dist = NaN;
    if ~isempty(clear_pos), hit_dist = norm(clear_pos(end, :) - G); end
    % 全部 /clear 落点是否都在 L 包围盒外扩 20 m 内
    x0 = min(L(:, 1)) - 20; x1 = max(L(:, 1)) + 20;
    y0 = min(L(:, 2)) - 20; y1 = max(L(:, 2)) + 20;
    in_box = all(clear_pos(:, 1) >= x0 - 1e-6 & clear_pos(:, 1) <= x1 + 1e-6 & ...
                 clear_pos(:, 2) >= y0 - 1e-6 & clear_pos(:, 2) <= y1 + 1e-6);

    fprintf('  未抛异常=%d  success=%d  mode=%s  /clear=%d  /measure=%d  总行程=%.0f m\n', ...
        ~threw, success, mode_used, nclear, nmeas, travel);
    fprintf('  命中点距真源 %.2f m；落点全在 L 外扩盒内=%d\n', hit_dist, in_box);

    results = {};
    results = chk(results, '不抛异常', ~threw, errmsg);
    results = chk(results, '分支确实派发到 sweep', strcmp(mode_used, 'sweep'), ...
        sprintf('实得 %s', mode_used));
    results = chk(results, '清除成功', isequal(success, true), sprintf('success=%d', success));
    results = chk(results, 'R_MEC 落在扫掠档 (20, 84.0369]', ...
        R_MEC > 20 && R_MEC <= 84.0369, sprintf('R_MEC=%.2f', R_MEC));
    results = chk(results, '/clear 次数 <= 30（覆盖中心集规模 ~24；真机旧版曾螺旋外扩到 19 次）', ...
        nclear <= 30, sprintf('实得 %d', nclear));
    results = chk(results, '最后一次 /clear 命中在真源 20 m 内（命题 Q4-B）', ...
        ~isnan(hit_dist) && hit_dist <= 20, sprintf('实得 %.2f m', hit_dist));
    results = chk(results, '所有 /clear 落点都在 L 外扩 20 m 的盒内（走的是"覆盖 L"中心集）', ...
        in_box, sprintf('nclear=%d', nclear));
    results = chk(results, '扫掠不读示向度 -> /measure 次数应为 0', nmeas == 0, ...
        sprintf('实得 %d 次', nmeas));

    ok = true;
    fprintf('\n');
    for i = 1:numel(results)
        fprintf('  %s\n', results{i});
        if strncmp(results{i}, '[FAIL]', 6), ok = false; end
    end
    fprintf('  ---- sweep_clear 覆盖 L: %s ----\n', ternary(ok, '全部通过', '有失败'));
end

%% ---------------- 局部函数 ----------------

function recs = read_jsonl(p)
    recs = {};
    if isempty(p) || ~exist(p, 'file'), return; end
    fid = fopen(p, 'r', 'n', 'UTF-8');
    if fid <= 0, return; end
    while ~feof(fid)
        line = fgetl(fid);
        if ~ischar(line) || isempty(strtrim(line)), continue; end
        try
            recs{end+1} = jsondecode(line); %#ok<AGROW>
        catch
        end
    end
    fclose(fid);
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
