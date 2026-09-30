% ========================================================================
% test_homing_convergence —— homing 收敛回归
%
% 守门测试：homing 必须**有限步内抵达并清除**。原实现步长恒定且过冲后回退半步
% ⇒ A→B→A 永久乒乓、原地转圈不收敛（d=1500 试跑被它拖垮）。
% 修法与事故复盘见《Q3 调优经验与补丁记录》I-2。
%
% 本测试用**按真实几何回答的 mock**（`核验脚本/_mock_simulator.py --mode geo`，真源固定在
%   (300,400)、频道 7、有效接收半径 1200）：一个收敛的 homing 必须**有限步内抵达并清除**。
%
% 用法（先起 mock：`py -3.11 核验脚本/_mock_simulator.py --mode geo --port 20266`，见一键脚本）：
%   test_homing_convergence(20266)
%
% 断言：① 不抛异常 ② 清除成功 ③ 检测次数有界（≤15）④ 总移动有界（≤2500 m）
%       ⑤ 最后一步的检测点确实落在真源 20 m 内
% ========================================================================

function ok = test_homing_convergence(port)
    if nargin < 1 || isempty(port), port = 20266; end

    fprintf('\n===== homing 收敛回归（geo mock，真源 (300,400)）=====\n');

    logdir = fullfile(tempdir, 'sclog_homingconv');
    if exist(logdir, 'dir'), rmdir(logdir, 's'); end

    results = {};
    threw = false; errmsg = ''; success = false; logpath = '';
    try
        c = SimulatorClient(sprintf('http://127.0.0.1:%d', port), 'TESTTEAM', logdir);
        c.enter();

        % 合成源：等边三角形绕 (-500,400)，外接半径 250 ⇒ R_MEC≈250 > R_star(84.04) ⇒ 走 homing
        % 其形心 = (-500,400)，到真源 (300,400) 的距离恰为 **800 m**
        R = 250; cx = -500; cy = 400;
        L = [cx + R,            cy;
             cx - R/2,          cy + R*sqrt(3)/2;
             cx - R/2,          cy - R*sqrt(3)/2];
        source = struct('channel', 7, 'L', L, 'c_star', [mean(L(:,1)), mean(L(:,2))], ...
                        'R_MEC', 250, 'D', R*sqrt(3));
        cfg = struct('R_clear', 20, 'R_star', 84.0369, ...
                     'coverage_density', 2*pi/(3*sqrt(3)), ...
                     'T_measure', 5, 'T_clear_success', 5, 'T_clear_fail', 3, ...
                     'epsilon_deg', 1, 'R_domain', 1800, ...
                     'R_homing_step_max', 300, 'homing_max_iter', 12, ...
                     'homing_max_move', 2500);

        [success, ~, ~] = clear_source(source, c, cfg);
        logpath = c.get_log_path();
        c.close_log();
    catch ME
        threw = true; errmsg = sprintf('%s: %s', ME.identifier, ME.message);
        try
            logpath = c.get_log_path(); c.close_log();
        catch
        end
    end

    % ---- 从日志里量：检测次数、总移动、最后落点 ----
    recs = read_jsonl(logpath);
    nmeas = 0; nclear = 0; travel = 0; prev = []; lastpos = [];
    for i = 1:numel(recs)
        if ~(isfield(recs{i}, 'kind') && strcmp(recs{i}.kind, 'request')), continue; end
        ep = ''; if isfield(recs{i}, 'endpoint'), ep = recs{i}.endpoint; end
        if strcmp(ep, '/measure'), nmeas = nmeas + 1; end
        if strcmp(ep, '/clear'),   nclear = nclear + 1; end
        p = [];
        if isfield(recs{i}, 'request_payload')
            rp = recs{i}.request_payload;
            if isstruct(rp) && isfield(rp, 'position') && isstruct(rp.position)
                p = [rp.position.x, rp.position.y];
            end
        end
        if ~isempty(p)
            if ~isempty(prev), travel = travel + norm(p - prev); end
            prev = p; lastpos = p;
        end
    end
    dsrc = NaN;
    if ~isempty(lastpos), dsrc = norm(lastpos - [300, 400]); end

    fprintf('  未抛异常=%d  success=%d  /measure=%d  /clear=%d  总移动=%.0f m  末点距真源=%.1f m\n', ...
        ~threw, success, nmeas, nclear, travel, dsrc);

    results = chk(results, '不抛异常', ~threw, errmsg);
    results = chk(results, '清除成功', isequal(success, true), sprintf('success=%d', success));
    results = chk(results, '检测次数有界（<= 15，旧版 10 次全废仍不成功）', nmeas <= 15, ...
        sprintf('实得 %d', nmeas));
    results = chk(results, '总移动有界（<= 2500 m，旧版单频道可烧 15 km+）', travel <= 2500, ...
        sprintf('实得 %.0f m', travel));
    results = chk(results, '收敛到真源 20 m 内（清除半径内）', ~isnan(dsrc) && dsrc <= 20, ...
        sprintf('实得 %.1f m', dsrc));

    ok = true;
    fprintf('\n');
    for i = 1:numel(results)
        fprintf('  %s\n', results{i});
        if strncmp(results{i}, '[FAIL]', 6), ok = false; end
    end
    fprintf('  ---- homing 收敛: %s ----\n', ternary(ok, '全部通过', '有失败'));
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
