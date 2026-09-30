% test_clear_source_homing —— clear_source 的 homing 路径回归
%
% 覆盖首次真机演练暴露的两处中止缺陷（事故复盘I-1）：
%   ① `pdist` 属 Statistics Toolbox、本机未装，未定义函数，程序中止；
%   ② `svd_deg` 无条件取值，no_signal 时报"无法识别的字段名"。
% 本测试用会返回 direction / near 的 mock 把这条路径真跑一遍。
%
% 用法（先起 mock，见 核验脚本/_run_client_selftest.py）：
%   test_clear_source_homing('homing', 20264)   % 走完全程：direction→near→clear
%   test_clear_source_homing('ok', 20259)       % 起点即 no_signal，应当安全放弃
%
% 返回：ok（true = 全部断言通过）

function ok = test_clear_source_homing(mode, port)
    if nargin < 1 || isempty(mode), mode = 'homing'; end
    if nargin < 2 || isempty(port), port = 20264; end

    fprintf('\n===== clear_source homing 回归：mode = %s =====\n', mode);

    logdir = fullfile(tempdir, ['sclog_clear_' mode]);
    if exist(logdir, 'dir'), rmdir(logdir, 's'); end

    results = {};
    threw = false;
    errmsg = '';
    success = false;
    logpath = '';

    try
        c = SimulatorClient(sprintf('http://127.0.0.1:%d', port), 'TESTTEAM', logdir);
        c.enter();

        % 合成源：R_MEC = 150 > R_star(84.0369)，必走 homing 分支
        L = [0 0; 400 0; 400 400; 0 400];
        source = struct('channel', 5, 'L', L, 'c_star', [200 200], ...
                        'R_MEC', 150, 'D', 565.685);
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
        threw = true;
        errmsg = sprintf('%s: %s', ME.identifier, ME.message);
        try
            logpath = c.get_log_path();
            c.close_log();
        catch
        end
    end

    recs = read_jsonl(logpath);
    nmeasure = 0; nclear = 0;
    for i = 1:numel(recs)
        if ~(isfield(recs{i}, 'kind') && strcmp(recs{i}.kind, 'request')), continue; end
        ep = '';
        if isfield(recs{i}, 'endpoint'), ep = recs{i}.endpoint; end
        if strcmp(ep, '/measure'), nmeasure = nmeasure + 1; end
        if strcmp(ep, '/clear'),   nclear   = nclear   + 1; end
    end

    fprintf('  未抛异常=%d  success=%d  /measure=%d  /clear=%d\n', ...
        ~threw, success, nmeasure, nclear);
    if threw
        fprintf('  异常：%s\n', errmsg);
    end

    switch mode
        case 'homing'
            % direction(2 次) → near → direct_clear → /clear success
            results = chk(results, '不抛异常（pdist 已替换）', ~threw, errmsg);
            results = chk(results, '发出了 homing 的起点 /measure', nmeasure >= 1, ...
                sprintf('实得 %d', nmeasure));
            results = chk(results, '走到了 /clear 且成功', ...
                nclear >= 1 && isequal(success, true), ...
                sprintf('nclear=%d success=%d', nclear, success));
        case 'ok'
            % 起点 measure 返回 no_signal，应安全放弃，不是崩
            results = chk(results, '不抛异常（svd_deg 守卫生效）', ~threw, errmsg);
            results = chk(results, '只试了一次 /measure 就放弃', nmeasure == 1, ...
                sprintf('实得 %d', nmeasure));
            results = chk(results, '未发出任何 /clear', nclear == 0, ...
                sprintf('实得 %d', nclear));
            results = chk(results, '如实返回 success=false', isequal(success, false));
        otherwise
            results = chk(results, sprintf('未知模式 %s', mode), false);
    end

    ok = true;
    fprintf('\n');
    for i = 1:numel(results)
        fprintf('  %s\n', results{i});
        if strncmp(results{i}, '[FAIL]', 6), ok = false; end
    end
    fprintf('  ---- clear_source/%s: %s ----\n', mode, ternary(ok, '全部通过', '有失败'));
end

%% ---------------- 局部函数 ----------------

function r = chk(r, name, cond, detail)
    if nargin < 4, detail = ''; end
    if cond
        r{end+1} = sprintf('[PASS] %s', name);
    else
        r{end+1} = sprintf('[FAIL] %s  %s', name, detail);
    end
end

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

function out = ternary(c, a, b)
    if c, out = a; else, out = b; end
end
