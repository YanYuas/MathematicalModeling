% main_batch_Q3Q4 —— 批量连跑驱动
%
% 在一次 MATLAB 会话里连续跑 N 局，逐局收集结果并汇总，用于需要多局样本的统计。
% 相对"每局重启 bat"：省掉每局约 40 s 的 MATLAB 启动，也消掉"启动晚于 5 s 倒计时"
% 这条红线（程序已醒着，接口一开就 /enter）；队号只输一次；统计自动算好。
%
% 局间仍需人工在模拟器界面点「确认开始测试」—— 开新一局是模拟器侧的动作，
% 接口不提供入口；本驱动在局间阻塞等待接口开放。
%
% 用法: main_batch_Q3Q4('Q3', '<参赛队号>', 8)
% 依赖: 同 main_Q3Q4

function summary = main_batch_Q3Q4(problem_type, robot_id, n_games, sim_url, ...
                                   grid_spacing, enter_wait_s, case_code)
    %% 0. 参数
    if nargin < 1 || isempty(problem_type), problem_type = 'Q3'; end
    if nargin < 3 || isempty(n_games),      n_games = 1;         end
    if nargin < 4, sim_url = [];            end
    if nargin < 5, grid_spacing = [];       end
    if nargin < 6 || isempty(enter_wait_s)
        % 局间要等人点「确认开始测试」，默认给 10 分钟预算（单局跑用 SimulatorClient 的 90 s）
        enter_wait_s = 600;
    end
    if nargin < 7, case_code = '';          end

    if nargin < 2 || isempty(robot_id)
        error('缺少参赛队号。用法: main_batch_Q3Q4(''Q3'',''<参赛队号>'',<局数>)');
    end
    n_games = floor(n_games);
    if n_games < 1
        error('局数必须 ≥ 1（收到 %g）', n_games);
    end
    if n_games > 30
        warning('局数 %d 偏大（>30）—— 确认这是有意的再继续。', n_games);
    end

    fprintf('\n');
    fprintf('########################################################################\n');
    fprintf('  %s 批量连跑：计划 %d 局  ｜  /enter 等待预算 %.0f s/局\n', ...
        problem_type, n_games, enter_wait_s);
    fprintf('  局间请在模拟器界面点「确认开始测试」——程序会自动等到接口开放\n');
    fprintf('########################################################################\n');

    %% 1. 逐局
    rec = repmat(struct('i', 0, 'ok', false, 'cleared', NaN, 'avg', NaN, ...
                        'tvir', NaN, 'realtime', NaN, 'ratio', NaN, ...
                        'total_lb', NaN, 'log_path', '', 'err', ''), n_games, 1);

    for g = 1:n_games
        fprintf('\n');
        fprintf('========================================================================\n');
        fprintf('  第 %d / %d 局\n', g, n_games);
        fprintf('========================================================================\n');
        if g > 1
            fprintf('>>> 请在模拟器界面点「确认开始测试」（若上一局已结束需重新选案例）。\n');
            fprintf('>>> 程序正在等待接口开放，最长等 %.0f s…\n', enter_wait_s);
        end

        rec(g).i = g;
        t_g = tic;
        try
            r = main_Q3Q4(problem_type, robot_id, case_code, sim_url, ...
                          grid_spacing, enter_wait_s);
            rec(g).ok       = true;
            rec(g).cleared  = r.cleared_count;
            rec(g).avg      = r.avg_time;
            rec(g).tvir     = r.virtual_time;
            rec(g).realtime = r.program_run_time;
            rec(g).ratio    = r.cleared_ratio;
            rec(g).total_lb = r.total_count;
            rec(g).log_path = r.log_path;
            fprintf('\n[第 %d 局完成] 清除 %d ｜ 均摊 %s s/源 ｜ 虚拟 %.0f s ｜ 墙钟 %.1f s ｜ 本局耗时 %.0f s\n', ...
                g, rec(g).cleared, fmtnum(rec(g).avg), rec(g).tvir, rec(g).realtime, toc(t_g));
        catch ME
            rec(g).ok  = false;
            rec(g).err = ME.message;
            fprintf('\n[第 %d 局失败] %s\n', g, ME.message);
            fprintf('>>> 若模拟器提示"已在测试中"，请先在界面结束本局，再让下一局继续；\n');
            fprintf('>>> 本局失败不中断批量，程序会继续等下一局。\n');
        end
    end

    %% 2. 汇总
    summary = aggregate(rec, problem_type, n_games);

    % 落盘（不写队号；本文件在 logs/ 下，不随支撑材料打包）
    stamp = datestr(now, 'yyyymmdd_HHMMSS');
    out_dir = fullfile(fileparts(mfilename('fullpath')), 'logs');
    if ~exist(out_dir, 'dir'), mkdir(out_dir); end
    out_path = fullfile(out_dir, sprintf('batch_summary_%s.txt', stamp));
    write_summary(out_path, rec, summary, problem_type, n_games);
    fprintf('\n[汇总] 已写入: %s\n', out_path);
    fprintf('[汇总] 该文件不含队号；每局的机器人日志在 logs/ 下，逐局一份。\n\n');
end

%% ======================================================================
%  汇总计算与打印
%% ======================================================================
function s = aggregate(rec, problem_type, n_games)
    ok = [rec.ok];
    n_ok = sum(ok);
    s = struct();
    s.n_games = n_games;
    s.n_ok = n_ok;
    s.n_fail = n_games - n_ok;
    s.rec = rec;

    fprintf('\n');
    fprintf('########################################################################\n');
    fprintf('  %s 批量结果汇总（%d 局：成功 %d ｜ 失败 %d）\n', problem_type, n_games, n_ok, s.n_fail);
    fprintf('########################################################################\n');

    %% 2.1 逐局明细
    fprintf('\n--- 逐局明细 ---\n');
    fprintf('%-4s %-10s %-8s %-12s %-12s %-12s %-9s %s\n', ...
        '局', '状态', '清除数', '虚拟时间(s)', '均摊(s/源)', '程序运行(s)', '清除比', '备注');
    for g = 1:n_games
        if rec(g).ok
            fprintf('%-4d %-10s %-8d %-12.1f %-12s %-12.2f %-9s %s\n', ...
                g, 'OK', rec(g).cleared, rec(g).tvir, fmtnum(rec(g).avg), ...
                rec(g).realtime, fmtpct(rec(g).ratio), '');
        else
            fprintf('%-4d %-10s %-8s %-12s %-12s %-12s %-9s %s\n', ...
                g, 'FAIL', '-', '-', '-', '-', '-', trunc(rec(g).err, 60));
        end
    end

    if n_ok == 0
        fprintf('\n无成功局 —— 不做统计（请先确认模拟器与接口可用）。\n');
        return;
    end

    avgs_all = [rec(ok).avg];        % 与成功局一一对齐（可能含 NaN：清除数为 0 的局）
    tvirs = [rec(ok).tvir];
    rts = [rec(ok).realtime];
    clr = [rec(ok).cleared];
    rat = [rec(ok).ratio];
    rat = rat(isfinite(rat));
    avgs = avgs_all(isfinite(avgs_all));   % 仅统计用的有限值子集

    %% 2.2 总体
    s.avg_mean = mean(avgs); s.avg_med = median(avgs);
    s.avg_min = min(avgs);   s.avg_max = max(avgs);
    s.avg_std = std(avgs);   s.tv_mean = mean(tvirs);
    s.rt_mean = mean(rts);   s.cleared_mean = mean(clr);
    s.ratio_min = min(rat);

    fprintf('\n--- 总体（仅成功局，n=%d；其中可算均摊 %d 局）---\n', n_ok, numel(avgs));
    fprintf('  均摊 s/源 : 均值 %.1f ｜ 中位 %.1f ｜ 最小 %.1f ｜ 最大 %.1f ｜ 标准差 %.1f\n', ...
        s.avg_mean, s.avg_med, s.avg_min, s.avg_max, s.avg_std);
    fprintf('  虚拟时间  : 均值 %.0f s（最小 %.0f ｜ 最大 %.0f）\n', ...
        s.tv_mean, min(tvirs), max(tvirs));
    fprintf('  程序运行  : 均值 %.2f s（墙钟，表 1 第 4 列；含 /enter 等待）\n', s.rt_mean);
    fprintf('  清除个数  : 均值 %.1f（最小 %d ｜ 最大 %d）\n', ...
        s.cleared_mean, min(clr), max(clr));
    fprintf('  清除比例  : 最小 %.1f%%%s\n', s.ratio_min * 100, ...
        tern(s.ratio_min >= 0.999, '（本批全部为 100%）', ' 有局未达 100%，逐局看上面明细'));

    %% 2.3 命中率 vs 均摊目标
    targets = [280 300 320 336 345 352 358 380 400];
    fprintf('\n--- 均摊目标命中率（分子 = 达标局数）---\n');
    fprintf('  %-10s %-10s %-9s  %s\n', '目标(s/源)', '达标局数', '占比', '达标局的清除个数');
    denom = numel(avgs);
    for t = targets
        hit = isfinite(avgs_all) & (avgs_all <= t);
        fprintf('  %-10d %-10s %-9s  %s\n', t, ...
            sprintf('%d / %d', sum(hit), denom), ...
            sprintf('%.0f%%', 100 * sum(hit) / max(denom, 1)), ...
            mat2str(sort(clr(hit))));
    end
    fprintf('  口径纪律（陷阱 R16）：均摊必须连着清除个数报 —— 均摊随源数强变化，\n');
    fprintf('     单看"均摊下降"可能只是抽到了更多源的局，不代表算法变快。\n');

    %% 2.4 按清除个数分组（R16 要求的正确读法）
    fprintf('\n--- 按清除个数分组（这才是可比的口径）---\n');
    fprintf('  %-8s %-6s %-12s %-12s %-12s %s\n', ...
        '清除个数', '局数', '均摊均值', '均摊最小', '总时间均值', '模型 3983/n+51');
    us = unique(clr);
    for i = 1:numel(us)
        m = (clr == us(i));
        a = avgs_all(m); a = a(isfinite(a));
        if isempty(a), continue; end
        fprintf('  %-8d %-6d %-12.1f %-12.1f %-12.0f %.1f\n', ...
            us(i), sum(m), mean(a), min(a), mean(tvirs(m)), 3983 / us(i) + 51);
    end

    %% 2.5 结论
    s.hit320 = sum(avgs <= 320);
    fprintf('\n--- 结论 ---\n');
    if s.avg_mean <= 320
        fprintf('  本批均值 %.1f ≤ 320 ⇒ 平均水准达到 320 s/源。\n', s.avg_mean);
    else
        fprintf('  本批均值 %.1f > 320 ⇒ 平均水准未达 320 s/源。\n', s.avg_mean);
        fprintf('     （中位 %.1f；320 达标 %d/%d 局，达标局的清除个数见上表）\n', ...
            s.avg_med, s.hit320, denom);
    end
    min_n_for_320 = [];
    ok_n = [];
    for i = 1:numel(us)
        m = (clr == us(i));
        a = avgs_all(m); a = a(isfinite(a));
        if ~isempty(a) && min(a) <= 320, ok_n(end+1) = us(i); end %#ok<AGROW>
    end
    if ~isempty(ok_n), min_n_for_320 = min(ok_n); end
    s.min_n_for_320 = min_n_for_320;
    if ~isempty(min_n_for_320)
        fprintf('     本批达到 320 的最小清除个数 = %d ⇒ 下面几局要刻意追这个大数档。\n', ...
            min_n_for_320);
    else
        fprintf('     本批没有任何源数档达到 320 ⇒ 想达标必须砍固定项（首推扫描路由 2400 s）。\n');
    end
    fprintf('########################################################################\n\n');
end

%% ======================================================================
%  落盘
%% ======================================================================
function write_summary(path, rec, s, problem_type, n_games)
    fid = fopen(path, 'w', 'n', 'UTF-8');
    if fid < 0
        warning('无法写汇总文件: %s', path);
        return;
    end
    fprintf(fid, '# %s 批量连跑汇总（不含队号）\n', problem_type);
    fprintf(fid, '# 生成时间: %s ｜ 局数 %d ｜ 成功 %d ｜ 失败 %d\n\n', ...
        datestr(now, 'yyyy-mm-dd HH:MM:SS'), n_games, s.n_ok, s.n_fail);
    fprintf(fid, '局\t状态\t清除个数\t虚拟时间s\t均摊s每源\t程序运行s\t清除比\t日志\n');
    for g = 1:n_games
        if rec(g).ok
            fprintf(fid, '%d\tOK\t%d\t%.2f\t%.2f\t%.2f\t%.4f\t%s\n', ...
                g, rec(g).cleared, rec(g).tvir, rec(g).avg, rec(g).realtime, ...
                rec(g).ratio, rec(g).log_path);
        else
            fprintf(fid, '%d\tFAIL\t\t\t\t\t\t%s\n', g, strrep(rec(g).err, newline, ' '));
        end
    end
    if s.n_ok > 0
        fprintf(fid, '\n# 总体（成功 %d 局）\n', s.n_ok);
        fprintf(fid, '均摊 均值\t%.2f\n均摊 中位\t%.2f\n均摊 最小\t%.2f\n均摊 最大\t%.2f\n', ...
            s.avg_mean, s.avg_med, s.avg_min, s.avg_max);
        fprintf(fid, '虚拟时间 均值\t%.1f\n程序运行 均值\t%.2f\n清除比例 最小\t%.4f\n', ...
            s.tv_mean, s.rt_mean, s.ratio_min);
        fprintf(fid, '320 达标局数\t%d\n', s.hit320);
        if ~isempty(s.min_n_for_320)
            fprintf(fid, '达到 320 的最小清除个数\t%d\n', s.min_n_for_320);
        end
    end
    fclose(fid);
end

%% ======================================================================
%  小工具（只用基础函数，不依赖任何工具箱 —— 本项目踩过 pdist 缺失的坑）
%% ======================================================================
function s = fmtnum(v)
    if isfinite(v)
        s = sprintf('%.1f', v);
    else
        s = 'n/a';
    end
end

function s = fmtpct(v)
    if isfinite(v)
        s = sprintf('%.1f%%', v * 100);
    else
        s = 'n/a';
    end
end

function s = trunc(txt, n)
    s = txt;
    if numel(s) > n
        s = [s(1:n) '…'];
    end
end

function out = tern(c, a, b)
    if c, out = a; else, out = b; end
end
