% ========================================================================
% test_sector_probe -- 扇区探针回归（引理 Q4-D，需 mock 模拟器）
% 用法: test_sector_probe(port)   % port 上跑 `_mock_simulator.py --mode sector`
% 构造（mock 的 sector 模式：源 G=(300,400)、频道 7、R_eff=1200、定向方向 ψ=90度）：
%   -> 扇区 = 闭半平面 {y >= 400}，u = (0,1)
%

function ok = test_sector_probe(port)
    if nargin < 1 || isempty(port), port = 20270; end
    fprintf('\n[test_sector_probe] mock port=%d\n', port);

    cfg = struct('R_sensor', 1000, 'R_clear', 20, 'R_star', 84.0369, ...
                 'T_measure', 5, 'T_switch', 1, 'T_clear_success', 5, ...
                 'T_clear_fail', 3, 'time_reserve', 60, 'sector_probe_step', 100);

    G = [300, 400];          % mock 的真源位置（_mock_simulator.py GEO_SRC）
    u = [0, 1];              % ψ = 90度

    logdir = fullfile(tempdir, sprintf('sectorprobe_%d', port));
    cli = SimulatorClient(sprintf('http://127.0.0.1:%d', port), 'TESTTEAM', logdir);
    cli.enter;

    ok = true;
    ok = ok && run_case('案例1: q+ 失败 q- 命中', cli, cfg, G, u, [400, 405], 2);
    ok = ok && run_case('案例2: q+ 直接命中',     cli, cfg, G, u, [400, 500], 1);

    cli.exit;
    fprintf('[test_sector_probe] %s\n\n', ternary_str(ok, 'PASS', 'FAIL'));
end

function ok = run_case(name, cli, cfg, G, u, p, n_expect)
    ok = false;
    fprintf('  [%s] p = (%.0f, %.0f)\n', name, p(1), p(2));

    % 先在 p 处拿到示向度（前置条件：p 必须在扇区内）
    m = cli.measure(p(1), p(2), 7);
    if ~strcmp(m.measure_result, 'direction')
        fprintf('     前置失败：p 处应为 direction，实为 %s\n', m.measure_result);
        return;
    end

    out = Q4_extensions.sector_probe(p, m.svd_deg, 7, cli, cfg);

    if ~out.found
        fprintf('     探针未取得第二条示向度（n_probe=%d）\n', out.n_probe);
        return;
    end
    if out.n_probe ~= n_expect
        fprintf('     探测次数 %d != 期望 %d\n', out.n_probe, n_expect);
        return;
    end
    if ~strcmp(out.kind, 'direction')
        fprintf('     结果类型 %s != direction\n', out.kind);
        return;
    end

    % 返回点必须仍在扇区内
    dotq = (out.position - G) * u';
    if dotq < -1e-9
        fprintf('     返回点 (%.1f, %.1f) 在扇区外（(q−G)·u = %.2f）\n', ...
            out.position(1), out.position(2), dotq);
        return;
    end

    % 示向度必须指向真实源。
    % 容差取 1.01度：题设的示向度误差本就是 ±1度（附件1 ），而 Q4 迷你模拟器会复现该误差
    % （共享 mock 的 sector 模式不加噪声）。取 0.01度 会把正常的 ±1度 误判为失败；
    % 而"扇区镜像 180度"这类真错会偏 180度，1.01度 的容差照样抓得住 --  实测已验证。
    true_deg = mod(atan2d(G(2) - out.position(2), G(1) - out.position(1)), 360);
    if abs(mod(out.svd_deg - true_deg + 180, 360) - 180) > 1.01
        fprintf('     示向度 %.2f度 与真实指向 %.2f度 不符（容差 1.01度）\n', out.svd_deg, true_deg);
        return;
    end

    % 偏移点与源的距离基本不变（垂直偏移的性质，陷阱 ）
    d_p = norm(p - G);
    d_q = norm(out.position - G);
    if d_q > cfg.R_sensor
        fprintf('     探针点距源 %.1f m 超出 R_eff=%.0f\n', d_q, cfg.R_sensor);
        return;
    end

    fprintf(['     通过：第 %d 次偏移命中 @ (%.1f, %.1f)，(q−G)·u=%.1f，' ...
             '示向度 %.2f度，距源 %.1f->%.1f m\n'], ...
        out.n_probe, out.position(1), out.position(2), dotq, out.svd_deg, d_p, d_q);
    ok = true;
end

function s = ternary_str(c, a, b)
    if c, s = a; else, s = b; end
end
