% test_SimulatorClient_logging -- SimulatorClient 的离线合规自测
% 在没有真模拟器的情况下验证三条赛题硬要求：
%   ① 自记录日志（附件1 / 附件2）：每次请求都落 JSONL
%   ② 双检查（附件2）：同时判 HTTP 状态与 accepted
%   ③ 重试口径：传输层失败可重试；业务/协议拒绝一律不重试
%

function ok = test_SimulatorClient_logging(mode, port)
    if nargin < 1 || isempty(mode), mode = 'ok'; end
    if nargin < 2 || isempty(port), port = 20259; end

    fprintf('\n[SimulatorClient 离线自测] mode = %s\n', mode);

    logdir = fullfile(tempdir, ['sclog_' mode]);
    if exist(logdir, 'dir'), rmdir(logdir, 's'); end

    base = sprintf('http://127.0.0.1:%d', port);
    results = {};

    err_id = '';
    enter_ok = false;
    logpath = '';
    c = [];
    try
        c = SimulatorClient(base, 'TESTTEAM', logdir);
        if strcmp(mode, 'hang')
            c.timeout = 2;                  % 缩短超时，让"可重试"验证跑得快
            c.enter_wait_s = 6;             % /enter 有等待窗口，测试里调短
            c.enter_retry_interval_s = 1;
        end
        r = c.enter;
        enter_ok = true;
        logpath = c.get_log_path;
        c.close_log;
    catch ME
        err_id = ME.identifier;
        try
            logpath = c.get_log_path;
            c.close_log;
        catch
        end
    end

    % 服务端请求计数（判断有没有重试的唯一可靠来源）
    server_count = -1;
    try
        st = webread([base, '/__stats']);
        server_count = st.count;
    catch
    end

    % 读回日志
    recs = read_jsonl(logpath);
    nreq = 0;
    first_req = struct;
    for i = 1:numel(recs)
        if isfield(recs{i}, 'kind') && strcmp(recs{i}.kind, 'request')
            nreq = nreq + 1;
            if nreq == 1, first_req = recs{i}; end
        end
    end

    fprintf('  server_count=%d  日志 request 条数=%d  err_id=%s\n', ...
        server_count, nreq, err_id);

    has = @(s, f) isstruct(s) && isfield(s, f);
    num_eq = @(s, f, v) isstruct(s) && isfield(s, f) && ~isempty(s.(f)) && ...
        abs(double(s.(f)) - v) < 1e-9;

    % 按模式断言
    switch mode
        case 'ok'
            results = chk(results, 'enter 成功且返回 struct', enter_ok && isstruct(r));
            results = chk(results, 'remaining_real_duration_s = 1200', ...
                enter_ok && num_eq(r, 'remaining_real_duration_s', 1200));
            results = chk(results, '未重试（server_count == 1）', server_count == 1, ...
                sprintf('实得 %d', server_count));
            results = chk(results, '日志有 request 记录且 accepted=true', ...
                nreq == 1 && has(first_req, 'accepted') && isequal(first_req.accepted, true));
            results = chk(results, '日志 http_status == 200', num_eq(first_req, 'http_status', 200));
            results = chk(results, '日志含 request_payload 与 response_payload', ...
                nreq == 1 && has(first_req, 'request_payload') && has(first_req, 'response_payload'));
            results = chk(results, '日志含 request_id 与 seq', ...
                nreq == 1 && has(first_req, 'request_id') && has(first_req, 'seq'));

        case 'accepted_false'
            results = chk(results, 'accepted=false 不重试（server_count == 1）', ...
                server_count == 1, ...
                sprintf('实得 %d（>1 = 在重试业务拒绝 -> 违反附件2）', server_count));
            results = chk(results, '抛 rejected 而非 transport', ...
                strcmp(err_id, 'SimulatorClient:rejected'), sprintf('实得 %s', err_id));
            results = chk(results, '日志仍记录这次请求（accepted=false）', ...
                nreq == 1 && has(first_req, 'accepted') && ~first_req.accepted);
            results = chk(results, '日志 virtual_time_s 记为 0', num_eq(first_req, 'virtual_time_s', 0));

        case 'http400'
            results = chk(results, 'HTTP 400 不重试（server_count == 1）', server_count == 1, ...
                sprintf('实得 %d', server_count));
            results = chk(results, '抛 rejected 而非 transport', ...
                strcmp(err_id, 'SimulatorClient:rejected'), sprintf('实得 %s', err_id));
            results = chk(results, '日志 http_status == 400', num_eq(first_req, 'http_status', 400));

        case 'http409'
            results = chk(results, 'HTTP 409 不重试（server_count == 1）', server_count == 1, ...
                sprintf('实得 %d', server_count));
            results = chk(results, '抛 rejected', strcmp(err_id, 'SimulatorClient:rejected'), ...
                sprintf('实得 %s', err_id));
            results = chk(results, '日志 http_status == 409', num_eq(first_req, 'http_status', 409));

        case 'hang'
            % enter 有等待窗口 -> 不再在 max_retries 次后抛
            % transport，而是在 enter_wait_s 预算内反复重试、最后抛 enterTimeout。
            % 因此把两件事分开验：
            %   (a) enter 的等待窗口：以 enterTimeout 收场，且重试次数 > max_retries
            %   (b) send_request 的传输层重试口径：改用 measure 验（它没有等待窗口），
            %       应当恰好重试 max_retries 次后抛 transport
            results = chk(results, 'enter 以 enterTimeout 收场（等待窗口生效）', ...
                strcmp(err_id, 'SimulatorClient:enterTimeout'), sprintf('实得 %s', err_id));
            results = chk(results, 'enter 重试次数 >= max_retries（重试确实发生了）', ...
                server_count >= 3, sprintf('实得 %d', server_count));
            results = chk(results, '每次尝试都落日志', nreq >= 3, sprintf('实得 %d', nreq));
            results = chk(results, '日志含 transport_error 文本', ...
                nreq >= 1 && has(first_req, 'transport_error') && ~isempty(first_req.transport_error));

            % (b) measure 的传输层重试：应恰好 3 次
            sc0 = server_count;
            m_err = '';
            if ~isempty(c)
                try
                    c.measure(0, 0, 1);
                catch ME2
                    m_err = ME2.identifier;
                end
            end
            sc1 = -1;
            try
                st2 = webread([base, '/__stats']);
                sc1 = st2.count;
            catch
            end
            delta = sc1 - sc0;
            results = chk(results, 'measure 传输层失败抛 transport', ...
                strcmp(m_err, 'SimulatorClient:transport'), sprintf('实得 %s', m_err));
            results = chk(results, 'measure 恰好重试 max_retries 次（delta == 3）', ...
                delta == 3, sprintf('实得 %d', delta));

        otherwise
            results = chk(results, sprintf('未知模式 %s', mode), false);
    end

    ok = true;
    fprintf('\n');
    for i = 1:numel(results)
        fprintf('  %s\n', results{i});
        if strncmp(results{i}, '[FAIL]', 6), ok = false; end
    end
    fprintf('  ---- %s: %s ----\n', mode, ternary(ok, '全部通过', '有失败'));
end

%% 局部函数

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
