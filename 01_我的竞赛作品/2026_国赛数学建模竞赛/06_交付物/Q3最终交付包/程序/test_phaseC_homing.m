% test_phaseC_homing —— 阶段 C「单方位 homing」回归
%
% 阶段 C 对"未清除但有示向度"的频道直接从该观测点 homing，而不是盲目重扫全部格点
% （旧做法实测一局白花 9 次检测 + 1427 m = 285 s 且不保证清掉）
%
% 本测试走真正的入口 `clear_source`（`homing_clear` 是局部函数，外部调不到）：
%   R_MEC = Inf，必走 homing 分支；start_pos/start_theta 透传，从指定点与方位启动。
%   geo mock 真源固定在 (300,400)、频道 7；我们从 (260,400) 沿 0°（正东）启动，40 m 外。
%
% 用法：由 核验脚本/_run_client_selftest.py 驱动（geo mock 挂在 20268）
% 断言：① 不抛异常 ② mode='homing' ③ 清除成功 ④ 检测次数有界(<=15) ⑤ 总行程有界(<=1200 m)

function ok = test_phaseC_homing(port)
    if nargin < 1 || isempty(port), port = 20268; end

    fprintf('\n===== 阶段 C 单方位 homing 回归（geo mock，真源 (300,400)）=====\n');

    logdir = fullfile(tempdir, 'sclog_phaseC');
    if exist(logdir, 'dir'), rmdir(logdir, 's'); end

    results = {};
    threw = false; errmsg = ''; success = false; logpath = ''; mode_used = '';
    try
        c = SimulatorClient(sprintf('http://127.0.0.1:%d', port), 'TESTTEAM', logdir);
        c.enter();

        cfg = struct('R_clear', 20, 'R_star', 84.0369, ...
                     'coverage_density', 2*pi/(3*sqrt(3)), ...
                     'T_measure', 5, 'T_clear_success', 5, 'T_clear_fail', 3, ...
                     'epsilon_deg', 1, 'R_domain', 1800, ...
                     'R_homing_step_max', 300, 'homing_max_iter', 12, ...
                     'homing_max_move', 2500);

        % 模拟阶段 C 的调用：频道已有示向度但无 L（交会定位失败）
        start_pos = [260, 400];      % 距真源 40 m
        start_theta = 0.0;           % 指向正东（真源方向）
        src = struct('channel', 7, 'L', [], 'c_star', start_pos, ...
                     'R_MEC', Inf, 'D', 0);
        [success, ~, mode_used] = clear_source(src, c, cfg, start_pos, start_theta);
        logpath = c.get_log_path();
        c.close_log();
    catch ME
        threw = true; errmsg = sprintf('%s: %s', ME.identifier, ME.message);
        try
            logpath = c.get_log_path(); c.close_log();
        catch
        end
    end

    recs = read_jsonl(logpath);
    nmeas = 0; travel = 0; prev = [];
    for i = 1:numel(recs)
        if ~(isfield(recs{i}, 'kind') && strcmp(recs{i}.kind, 'request')), continue; end
        ep = ''; if isfield(recs{i}, 'endpoint'), ep = recs{i}.endpoint; end
        if strcmp(ep, '/measure'), nmeas = nmeas + 1; end
        p = [];
        if isfield(recs{i}, 'request_payload')
            rp = recs{i}.request_payload;
            if isstruct(rp) && isfield(rp, 'position') && isstruct(rp.position)
                p = [rp.position.x, rp.position.y];
            end
        end
        if ~isempty(p)
            if ~isempty(prev), travel = travel + norm(p - prev); end
            prev = p;
        end
    end

    fprintf('  未抛异常=%d  success=%d  mode=%s  /measure=%d  总行程=%.0f m\n', ...
        ~threw, success, mode_used, nmeas, travel);

    results = chk(results, '不抛异常', ~threw, errmsg);
    results = chk(results, '分支派发到 homing（R_MEC=Inf）', strcmp(mode_used, 'homing'), ...
        sprintf('实得 %s', mode_used));
    results = chk(results, '沿单方位 homing 清除成功', isequal(success, true), ...
        sprintf('success=%d', success));
    results = chk(results, '检测次数有界（<= 15）', nmeas <= 15, sprintf('实得 %d', nmeas));
    results = chk(results, '总行程有界（<= 1200 m；旧版重扫 13 格点可达数千米）', ...
        travel <= 1200, sprintf('实得 %.0f m', travel));

    ok = true;
    fprintf('\n');
    for i = 1:numel(results)
        fprintf('  %s\n', results{i});
        if strncmp(results{i}, '[FAIL]', 6), ok = false; end
    end
    fprintf('  ---- 阶段 C 单方位 homing: %s ----\n', ternary(ok, '全部通过', '有失败'));
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
