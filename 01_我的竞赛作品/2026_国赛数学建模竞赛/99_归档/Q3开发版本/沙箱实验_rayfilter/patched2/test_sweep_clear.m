% ========================================================================
% test_sweep_clear.m —— `sweep_clear` 的**定向短走**回归（专打这条分支）
% ========================================================================
% 为什么单独测：离线 mini-sim 的 3 个种子里 `sweep_clear` **一次都没执行**（13 次清除全是
%   direct）⇒ 那个改动在离线基线里量不出效果；但**真实实跑里它明确发生过**：
%   `logs/robot_XX队号_20260912_221255.jsonl` 的 ch=13 以 20 m 网格螺旋外扩
%   **试了 19 次 no_target_in_range 才命中**（白走 ~1000 m + 57 s）。
%   所以必须有一条直接打这个分支的测试，否则改动等于没验。
%
% 手法：用 `核验脚本/_mock_simulator.py --mode geo`（按真实几何回答，真源固定在 (300,400)、频道 7）。
%   构造 `c_star` 距真源 **40 m**（> 20 m ⇒ 就地清必然失败，必须短走），R_MEC 取 60
%   （落在 sweep 分支 20 < R_MEC ≤ 84.0369）。
%   旧实现：按 c* 包围盒以 20 m 铺点、按距 c* 升序逐个试 ⇒ 需多次探点。
%   新实现：在 c* 测一次拿方位 → 沿方位走 20 m → 必中（1° 误差在 60 m 处横偏仅 ~1 m）。
%
% 用法：由 核验脚本/_run_client_selftest.py 驱动（geo mock 挂在 20267）
%   test_sweep_clear(20267)
% 断言：① 不抛异常 ② 清除成功 ③ `/clear` 次数 ≤ 4（旧实现更多）
%       ④ 总行程 ≤ 400 m（含起点到 c* 那一段；旧实现的包围盒螺旋可走数百米）
% ========================================================================

function ok = test_sweep_clear(port)
    if nargin < 1 || isempty(port), port = 20267; end

    fprintf('\n===== sweep_clear 定向短走回归（geo mock，真源 (300,400)）=====\n');

    logdir = fullfile(tempdir, 'sclog_sweep');
    if exist(logdir, 'dir'), rmdir(logdir, 's'); end

    results = {};
    threw = false; errmsg = ''; success = false; logpath = ''; mode_used = '';
    try
        c = SimulatorClient(sprintf('http://127.0.0.1:%d', port), 'TESTTEAM', logdir);
        c.enter();

        % c_star 距真源 40 m（必然超出 20 m 清除半径）⇒ 必须短走
        c_star = [260, 400];
        % L 随便给一个（sweep 分支不再用 L，仅保留签名兼容）
        L = [250 390; 270 390; 270 410; 250 410];
        cfg = struct('R_clear', 20, 'R_star', 84.0369, ...
                     'coverage_density', 2*pi/(3*sqrt(3)), ...
                     'T_measure', 5, 'T_clear_success', 5, 'T_clear_fail', 3, ...
                     'epsilon_deg', 1, 'R_domain', 1800);

        % `sweep_clear` 是 clear_source.m 里的**局部函数**，外部不可直接调用
        % ⇒ 经真正的入口 clear_source（同时验证分支派发到 sweep）
        source = struct('channel', 7, 'L', L, 'c_star', c_star, 'R_MEC', 60, 'D', 400);
        [success, ~, mode_used] = clear_source(source, c, cfg);
        logpath = c.get_log_path();
        c.close_log();
    catch ME
        threw = true; errmsg = sprintf('%s: %s', ME.identifier, ME.message);
        try
            logpath = c.get_log_path(); c.close_log();
        catch
        end
    end

    % 从日志量 /clear 次数与总行程
    recs = read_jsonl(logpath);
    nclear = 0; nmeas = 0; travel = 0; prev = [];
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
            if ~isempty(prev), travel = travel + norm(p - prev); end
            prev = p;
        end
    end

    fprintf('  未抛异常=%d  success=%d  mode=%s  /clear=%d  /measure=%d  总行程=%.0f m\n', ...
        ~threw, success, mode_used, nclear, nmeas, travel);

    results = chk(results, '不抛异常', ~threw, errmsg);
    results = chk(results, '分支确实派发到 sweep', strcmp(mode_used, 'sweep'), ...
        sprintf('实得 %s', mode_used));
    results = chk(results, '清除成功', isequal(success, true), sprintf('success=%d', success));
    results = chk(results, '/clear 次数 <= 4（旧实现螺旋外扩更多）', nclear <= 4, ...
        sprintf('实得 %d', nclear));
    results = chk(results, '总行程 <= 400 m（含起点到 c* 那一段；旧实现螺旋可走数百米）', travel <= 400, ...
        sprintf('实得 %.0f m', travel));

    ok = true;
    fprintf('\n');
    for i = 1:numel(results)
        fprintf('  %s\n', results{i});
        if strncmp(results{i}, '[FAIL]', 6), ok = false; end
    end
    fprintf('  ---- sweep_clear 定向短走: %s ----\n', ternary(ok, '全部通过', '有失败'));
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
