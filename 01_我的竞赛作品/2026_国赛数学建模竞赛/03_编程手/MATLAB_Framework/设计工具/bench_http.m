function bench_http(port)
% _bench_http —— 一次性基准：拆开每次请求的耗时构成（webwrite vs JSONL 落盘）
% 目的：Q4 的点数约 Q3 的 2.4 倍（31 vs 13），现实时间预算 1200 s 是否够，
%       取决于"每次请求多少毫秒"。这个基准把三块拆开量。

    url = sprintf('http://127.0.0.1:%d', port);
    N = 200;

    % (a) 完整 client（webwrite + JSONL 落盘 + 字段拼装）
    cli = SimulatorClient(url, 'BENCH', fullfile(tempdir, 'bench_withlog'));
    cli.enter();
    tic; for i = 1:N, cli.measure(0, 0, 1); end; t1 = toc;

    % (b) 裸 webwrite（同一 payload 形状，不落盘）
    opts = weboptions('RequestMethod', 'post', 'MediaType', 'application/json', 'Timeout', 10);
    pl = struct('arena_id', 'default', 'robot_id', 'BENCH', 'request_id', 'x', ...
                'position', struct('x', 0, 'y', 0), 'channel', 1);
    tic
    for i = 1:N
        pl.request_id = sprintf('bench-%d', i);
        webwrite([url '/measure'], pl, opts);
    end
    t2 = toc;

    % (c) 只落盘（不起 HTTP）
    cli3 = SimulatorClient(url, 'BENCH', fullfile(tempdir, 'bench_logonly'));
    extra = struct('endpoint', '/measure', 'attempt', 1, 'request_id', 'x', ...
        'request_payload', pl, ...
        'response_payload', struct('accepted', true, 'real_timestamp_ms', 1, ...
            'virtual_time_s', 1, 'measure_result', 'no_signal'), ...
        'http_status', 200, 'response_received', true, 'accepted', true, ...
        'virtual_time_s', 1, 'transport_error', '', 'error_identifier', '');
    tic; for i = 1:N, cli3.log_record('request', extra); end; t3 = toc;

    fprintf(['BENCH N=%d : client=%.2f ms/req | raw webwrite=%.2f ms/req | ' ...
             'log only=%.2f ms/req\n'], N, 1000*t1/N, 1000*t2/N, 1000*t3/N);
    cli.exit();
end
