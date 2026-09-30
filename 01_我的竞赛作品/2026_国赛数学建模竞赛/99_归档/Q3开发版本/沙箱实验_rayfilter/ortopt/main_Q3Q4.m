% ========================================================================
% CUMCM2026 B题 Q3/Q4 —— 机器狗搜索定位与清除主程序
%
% 用法（推荐双击同目录的 一键_跑Q3.bat）:
%   main_Q3Q4('Q3', '<参赛队号>')                        % 最小调用
%   main_Q3Q4('Q4', '<参赛队号>', '<测试案例编码>')        % Q4
%   main_Q3Q4('Q3', '<参赛队号>', '', [], 1000, [], 0)   % 强制回退三角格（对照跑）
%
% 参数: problem_type / robot_id（必填，逐字节等于当前登录队号）/ case_code /
%       sim_url（覆写地址，仅离线自测用）/ grid_spacing / enter_wait_s /
%       r_outer（径向档外环半径；≤0 强制回退三角格）
% 输出: results 结构体（表 1 四列即取自其中）
%
% 依赖: MATLAB R2020a+（webwrite）
% ========================================================================

function results = main_Q3Q4(problem_type, robot_id, case_code, sim_url, grid_spacing, enter_wait_s, r_outer)
    %% 0. 参数检查与初始化
    if nargin < 1 || isempty(problem_type)
        problem_type = 'Q3';
    end
    if nargin < 3
        case_code = '';       % 测试案例编码（附件1 §4.6），可留空
    end
    if nargin < 4 || isempty(sim_url)
        sim_url = '';         % 空 = 用配置里的默认地址
    end
    if nargin < 5
        grid_spacing = [];    % 空 = 用 load_config 默认档
    end
    if nargin < 6
        enter_wait_s = [];    % 空 = 用 SimulatorClient 默认；批量连跑时传大值
    end
    if nargin < 7
        r_outer = [];         % 空 = 用 load_config 的 config.r_outer
    end

    fprintf('\n');
    fprintf('========================================================================\n');
    fprintf('  CUMCM2026 B题 %s - 机器狗自动搜索定位与清除\n', problem_type);
    fprintf('========================================================================\n');
    fprintf('\n');

    %% 1. 加载配置参数
    config = load_config(problem_type);

    % 可选覆写（仅供离线自测与 A/B 对照，不动默认档）
    if ~isempty(sim_url)
        config.simulator_url = sim_url;
        fprintf('[模拟器] 地址被覆写为 %s（离线自测用）\n', sim_url);
    end

    if ~isempty(grid_spacing)
        fprintf('[网格] 间距 d 被覆写为 %.0f m（原 %s）\n', grid_spacing, ...
            num2str(config.grid_spacing));
        config.grid_spacing = grid_spacing;
    end

    % 第 7 参数: > 0 覆写外环半径; ≤ 0 强制回退三角格
    if nargin >= 7 && ~isempty(r_outer)
        if r_outer > 0
            fprintf('[网格] 外环半径被覆写为 %.0f m（原 %s）\n', r_outer, ...
                num2str(config.r_outer));
            config.r_outer = r_outer;
        else
            fprintf('[网格] 强制回退三角格（第 7 参数 = %.0f）\n', r_outer);
            config.r_outer = [];
        end
    end

    % 队号必须运行期传入：附件2 §5.1 要求逐字节等于当前登录队号，
    % 且格式规范要求支撑材料中隐去队号 ⇒ 源码不留真号
    if nargin < 2 || isempty(robot_id)
        error(['缺少参赛队号。请用:  matlab -batch "main_Q3Q4(''%s'',''<参赛队号>'')"' ...
               newline '或直接双击同目录的  一键_跑Q3.bat （会提示输入队号）。'], problem_type);
    end
    config.robot_id = robot_id;
    fprintf('[队号] robot_id = %s（运行期传入，源码不含真实队号）\n', config.robot_id);
    if ~isempty(case_code)
        fprintf('[案例] 测试案例编码 = %s\n', case_code);
    end

    %% 2. 连接模拟器
    fprintf('[模拟器] 连接中...\n');
    sim_client = SimulatorClient(config.simulator_url, config.robot_id);

    % /enter 等待预算可覆写（批量连跑时局间要等人点「确认开始测试」）
    if ~isempty(enter_wait_s)
        sim_client.enter_wait_s = enter_wait_s;
        fprintf('[模拟器] /enter 等待预算 = %.0f s\n', sim_client.enter_wait_s);
    end

    % 进入测试
    try
        enter_resp = sim_client.enter();
        fprintf('[模拟器] /enter 成功！本局可用现实时间: %.1f s\n', ...
            enter_resp.remaining_real_duration_s);
        if enter_resp.remaining_real_duration_s < 1200
            fprintf('[提示] 不足 1200 s —— 说明 /enter 晚于窗口开始 5 分钟，按剩余时间规划\n');
        end
    catch ME
        error('[错误] 模拟器连接/进入失败: %s', ME.message);
    end

    %% 3. 生成检测点网格
    fprintf('\n[阶段 1] 生成检测点网格...\n');
    is_Q4 = strcmp(problem_type, 'Q4');

    if is_Q4
        % ===== P0-3 接线：Q4 用「外扩环带」（宽度 = d，见 Q4_extensions 更正），不用圆内裁剪 =====
        detection_points = Q4_extensions.generate_extended_grid(...
            config.grid_spacing, config.R_domain, config.R_sensor);
        fprintf('[网格] Q4 外扩环带：%d 个检测点 (d=%.1f m)\n', ...
            size(detection_points, 1), config.grid_spacing);

        % 全域零漏点自检（surrounding；P0-3(ii)）
        [surr_ok, ~, ~] = Q4_extensions.check_surrounding_all(...
            detection_points, config.R_domain, config.R_sensor);
        if ~surr_ok
            warning('[Q4] 全域 surrounding 自检未通过 —— 策略的「100%% 清除」依据不成立');
        end
    else
        % Q3 检测点布局：径向档（config.r_outer 有值）或三角格
        if ~isempty(config.r_outer)
            detection_points = generate_radial_grid(config.grid_spacing, ...
                config.R_domain, config.r_outer);
        else
            grid_params = struct(...
                'd', config.grid_spacing, ...
                'R_domain', config.R_domain, ...
                'extend_for_Q4', false);
            detection_points = generate_triangular_grid(grid_params);
        end
        fprintf('[网格] 生成 %d 个检测点 (d=%.1f m)\n', size(detection_points, 1), config.grid_spacing);

        coverage_ok = check_coverage(detection_points, config);
        if ~coverage_ok
            error('[错误] 覆盖自检失败！');
        end
        fprintf('[自检] 覆盖验证通过 ✓\n');
    end

    % 记录本局实际用的网格档，供事后分档统计（两种档的日志其余字段不可辨）
    sim_client.log_record('grid_info', struct( ...
        'grid_style', ternary(is_Q4, 'q4_extended', ...
                              ternary(isempty(config.r_outer), 'triangular', 'radial')), ...
        'r_outer', ternary(isempty(config.r_outer), NaN, config.r_outer), ...
        'grid_spacing', config.grid_spacing, ...
        'n_points', size(detection_points, 1), ...
        'R_domain', config.R_domain, ...
        'R_sensor', config.R_sensor));

    %% 4. 初始化状态管理器
    fprintf('\n[阶段 2] 初始化状态管理...\n');
    state = ChannelStateMachine(config.n_channels, size(detection_points, 1));

    %% 5. 阶段 A: 侦察 —— 扫描检测点（动态重规划 + 发现即清除）
    fprintf('\n[阶段 A] 侦察阶段 - 扫描检测点（动态重规划）...\n');
    % 每步都从当前落点重规划，不照一次算好的固定顺序走（理由见《调优与补丁记录》P-1）
    n_pts = size(detection_points, 1);
    remaining = true(n_pts, 1);
    step_i = 0;
    n_skip_queued = 0;   % 被跳过的重复检测次数（免测集命中数）
    discovered_sources = cell(0);  % 阶段 B/C 兜底用的未清源
    cur_pos = [0, 0];              % 当前落点（供就近排序）
    current_channel = 1;           % 当前测向机频道
    pending = cell(0);             % 已定位但未清除的源
    while any(remaining) || ~isempty(pending)
        % 防御：清掉空槽（否则 `~isempty(pending)` 可能永远为真 ⇒ 死循环）
        if ~isempty(pending)
            pending = pending(~cellfun(@isempty, pending));
        end
        % 任务表 = 剩余格点 ∪ 待清源，整体做 NN+2-opt 取第一站
        % （"发现即清除"单独用不省移动，必须配合就近调度；见《调优与补丁记录》P-1、P-2）
        tasks = detection_points(remaining, :);
        kind_of = repmat({'grid'}, 1, size(tasks, 1));
        idx_of = find(remaining)';
        for k = 1:numel(pending)
            if isempty(pending{k}), continue; end
            if ~isfield(pending{k}, 'c_star') || isempty(pending{k}.c_star), continue; end
            tasks(end+1, :) = pending{k}.c_star(:)';
            kind_of{end+1} = 'clear';
            idx_of(end+1) = k;
        end
        if isempty(tasks), break; end
        ord = optimize_route(tasks, cur_pos);
        task_kind = kind_of{ord(1)};
        task_pick = idx_of(ord(1));

        if strcmp(task_kind, 'clear')
            % ---- 就近去清一个已知源 ----
            src = pending{task_pick};
            pending(task_pick) = [];        % 用**元素删除**（不是置空），保证 pending 会缩短
            if state.is_cleared(src.channel), continue; end
            fprintf('  [调度] 就近清除 频道 %d（距 %.0f m，任务表 %d 项）\n', ...
                src.channel, norm(src.c_star(:)' - cur_pos), numel(tasks));
            [ok_c, cost_c, mode_c] = clear_source(src, sim_client, config);
            if ok_c
                state.mark_cleared(src.channel);
                cur_pos = src.c_star(:)';
                fprintf('  [清除] 频道 %d 成功 (%s, %.1f s)\n', src.channel, mode_c, cost_c);
            else
                % 清不掉 ⇒ 交阶段 B 兜底重试（原逻辑保留）
                discovered_sources{end+1} = src;
                fprintf('  [清除] 频道 %d 未成功 (%s) ⇒ 转入阶段 B 兜底\n', src.channel, mode_c);
            end
            continue;
        end

        % ---- 就近去扫一个格点 ----
        pt_idx = task_pick;
        remaining(pt_idx) = false;
        step_i = step_i + 1;

        pos = detection_points(pt_idx, :);
        cur_pos = pos;

        % 检查现实时间
        if sim_client.remaining_time < config.time_reserve
            fprintf('[警告] 现实时间不足，进入收尾阶段\n');
            break;
        end

        % 免测集 = 已清除 ∪ 已在待清队列
        % 依据：triangulate_source 只读前两个观测 ⇒ 第 3 个起无人读，重测是纯浪费。
        % 已清除/待清的频道都不参与"判空"，故不影响完备性；清除失败会离开 pending
        % ⇒ 判据立刻失效、恢复测量。详见《调优与补丁记录》P-5。
        skip_queued = false(config.n_channels, 1);
        for k_q = 1:numel(pending)
            if ~isempty(pending{k_q}) && isfield(pending{k_q}, 'channel')
                skip_queued(pending{k_q}.channel) = true;
            end
        end
        for ch = 1:config.n_channels
            if state.is_cleared(ch)
                continue;
            end
            if skip_queued(ch)
                n_skip_queued = n_skip_queued + 1;
                continue;
            end

            % 检测
            result = sim_client.measure(pos(1), pos(2), ch);
            current_channel = ch;

            % 更新状态
            state.update(ch, pt_idx, result.measure_result, result, pos);

            % 处理结果
            if strcmp(result.measure_result, 'direction')
                % 发现信号，记录示向度
                fprintf('  [发现] 频道 %d 在点 %d 处测得示向度 %.2f°\n', ...
                    ch, pt_idx, result.svd_deg);

                % 拿到 2 个观测就地交会定位并入待清队列（等待更多观测不会更准，
                % 因为三角化只用前两条）。清不掉则交阶段 B/C 兜底。见《调优与补丁记录》P-4。
                if state.has_two_observations(ch)
                    source_info = triangulate_source(state.get_observations(ch), config);
                    if ~isempty(source_info)
                        % 不入队"发现即冲过去清"，而是排进待清队列由任务表决定何时顺路去清。
                        % 同一频道只入队一次：三角化恒用前两条观测，重复入队只会让任务表
                        % 反复派发同一件已判定不可清的任务。清不掉则交阶段 B/C 兜底。
                        queued = false;
                        for k_q = 1:numel(pending)
                            if ~isempty(pending{k_q}) && isfield(pending{k_q}, 'channel') ...
                                    && pending{k_q}.channel == ch
                                queued = true; break;
                            end
                        end
                        if ~queued
                            pending{end+1} = source_info;
                            fprintf('  [定位] 频道 %d 已定位 R_MEC=%.2f m ⇒ 入待清队列\n', ...
                                ch, source_info.R_MEC);
                        end
                    end
                end

            elseif strcmp(result.measure_result, 'near')
                % 距离很近，直接清除
                fprintf('  [Near] 频道 %d 在 5m 内\n', ch);
                clear_result = sim_client.clear(pos(1), pos(2), ch);
                if strcmp(clear_result.clear_result, 'success')
                    state.mark_cleared(ch);
                    fprintf('  [清除] 频道 %d 清除成功 ✓\n', ch);
                end

            elseif strcmp(result.measure_result, 'no_signal') && is_Q4
                % ===== P0-3 接线：Q4 的 no_signal 接入 surrounding / 扇区探针 =====
                action = Q4_extensions.handle_no_signal_Q4(...
                    pos, ch, detection_points, sim_client, config);
                if strcmp(action, 'skip') && Q4_extensions.is_surrounding(pos, detection_points, config.R_sensor)
                    % surrounding 成立 ⇒ 该点周围无漏测死角，此频道可跳过（不视为已确认空）
                    continue;
                end
            end
        end

        % 定期检查完备性
        if mod(step_i, 3) == 0
            [complete, stats] = state.check_completeness();
            fprintf('[进度] 已清除: %d, 已确认空: %d, 剩余: %d\n', ...
                stats.cleared, stats.confirmed_empty, stats.remaining);
        end
    end

    % 报告免测跳过的收益
    if n_skip_queued > 0
        fprintf(['[优化] 跳过「已定位且已排队待清」的重复检测 %d 次 ' ...
                 '⇒ 省约 %.0f s 虚拟时间（5 s 检测 + 1 s 切换/次）\n'], ...
            n_skip_queued, n_skip_queued * 6);
    end

    %% 5.5 单观测频道预警（风险探针）
    % 覆盖只保证"每个源至少被 1 个格点发现"，不保证被 2 个发现；
    % 而交会定位需要 2 个观测 ⇒ 只被 1 个发现的频道可能永不清除。
    % 这里把它在终端当场暴露，不用等日志分析。
    single_obs = [];
    for ch = 1:config.n_channels
        if state.is_cleared(ch) || state.is_confirmed_empty(ch)
            continue;
        end
        if numel(state.get_observations(ch)) == 1
            single_obs(end+1) = ch; %#ok<AGROW>
        end
    end
    if ~isempty(single_obs)
        fprintf('\n[风险] 以下频道**只被 1 个格点发现** —— 交会定位需 2 个观测 ⇒ **可能永不清除**：\n');
        fprintf('       %s\n', mat2str(single_obs));
        fprintf('       ⇒ 这是 d=1500 对照轨的已知风险；若这些频道最终未被清除，说明该档不适用。\n\n');
    else
        fprintf('\n[风险] 无单观测频道（每个未清除频道都有 >= 2 个观测）\n\n');
    end

    %% 6. 阶段 B: 清除（主循环漏掉/清失败的源在此兜底）
    fprintf('\n[阶段 B] 清除阶段...\n');
    % 按"就近"重排清除顺序：只改访问顺序，不动任何判定/清除逻辑
    % （按发现顺序清 vs 就近重排：13160 m → 8789 m，见《调优与补丁记录》P-2）
    discovered_sources = order_sources_nearest(discovered_sources, cur_pos);
    for i = 1:length(discovered_sources)
        source = discovered_sources{i};

        % 检查是否已清除
        if state.is_cleared(source.channel)
            continue;
        end

        % 三路清除策略
        [success, cost, mode] = clear_source(source, sim_client, config);
        if success
            state.mark_cleared(source.channel);
            fprintf('  [清除] 频道 %d 清除成功 (%s, %.1f s) ✓\n', ...
                source.channel, mode, cost);
        end
    end

    %% 7. 阶段 C: 收尾 —— 对"未清除但有示向度"的频道做定向 homing
    % 这些频道已经拿到过示向度（附件2 §7.2：有 svd_deg 就能定向），
    % 直接从该观测点 homing 逼近，而不是盲目重扫全部格点。见《调优与补丁记录》P-4。
    % 无观测的频道必然已在主循环里被判为 confirmed_empty，不会走到这里。
    fprintf('\n[阶段 C] 收尾 —— 对未清除频道做定向 homing...\n');
    for ch = 1:config.n_channels
        if state.is_cleared(ch) || state.is_confirmed_empty(ch)
            continue;
        end
        obs = state.get_observations(ch);
        if isempty(obs)
            fprintf('  [收尾] 频道 %d 未清除且无观测（异常情形），跳过\n', ch);
            continue;
        end
        o = obs(1);
        fprintf('  [收尾] 频道 %d 有 %d 个观测 ⇒ 从 (%.1f, %.1f) 沿示向度 %.2f° homing\n', ...
            ch, numel(obs), o.position(1), o.position(2), o.svd_deg);
        % R_MEC = Inf ⇒ clear_source 必走 homing 分支；start_pos/start_theta 透传到 homing_clear
        src = struct('channel', ch, 'L', [], 'c_star', o.position(:)', ...
                     'R_MEC', Inf, 'D', 0);
        [okh, costh] = clear_source(src, sim_client, config, o.position(:)', o.svd_deg);
        if okh
            state.mark_cleared(ch);
            fprintf('  [清除] 频道 %d homing 成功 (%.1f s) ✓\n', ch, costh);
        else
            fprintf('  [收尾] 频道 %d homing 未成功（%.1f s）\n', ch, costh);
        end
    end
    [complete, stats] = state.check_completeness();

    %% 8. 退出测试
    fprintf('\n[结束] 调用 /exit...\n');
    exit_resp = sim_client.exit();

    %% 9. 统计结果
    [complete, stats] = state.check_completeness();
    results = struct();
    results.cleared_count = stats.cleared;
    results.total_count = stats.cleared + stats.remaining;
    if results.total_count > 0
        results.cleared_ratio = stats.cleared / results.total_count;
    else
        results.cleared_ratio = NaN;
    end
    results.virtual_time = sim_client.virtual_time;
    % 平均定位清除时间 = 虚拟时间 ÷ 被清除个数（附件3 表 1 口径）
    if stats.cleared > 0
        results.avg_time = results.virtual_time / stats.cleared;
    else
        results.avg_time = NaN;
    end
    % 表 1 第 4 列：程序运行时间 = /enter → 结束 的墙钟（附件1 §4.6）
    results.program_run_time = sim_client.wall_clock_s();
    results.case_code = case_code;
    results.log_path = sim_client.get_log_path();

    sim_client.close_log();   % 写 session_end 并落盘

    fprintf('\n========================================================================\n');
    fprintf('  测试完成\n');
    fprintf('========================================================================\n');
    % 口径提示：本程序**无法知道源总数**（附件2 §1.3 接口不返回）
    % ⇒ total_count 只是"已清除 + 状态机判为未清"的下界，不是真总数
    fprintf('已清除: %d', stats.cleared);
    if results.total_count > 0
        fprintf(' ／ 下界 %d（%.1f%%）  ← 分母来自本地状态机，**非**真源总数\n', ...
            results.total_count, results.cleared_ratio * 100);
    else
        fprintf('   （本局未发现任何源 ⇒ 比例无法计算）\n');
    end
    fprintf('虚拟时间(定位清除总时间): %.2f s\n', results.virtual_time);
    if isnan(results.avg_time)
        fprintf('平均定位清除时间: n/a（清除数为 0，已屏蔽除零）\n');
    else
        fprintf('平均定位清除时间: %.2f s\n', results.avg_time);
    end

    % 表 1 复制块（附件3）：四列 = 案例编码 / 清除个数 / 平均定位清除时间 / 程序运行时间
    % 表 1 不要比例（正式测试不显示案例真值，附件1 §4.6）
    fprintf('\n---- 表 1 填写用（直接抄进论文） ----\n');
    fprintf('测试案例编码          : %s\n', ...
        ternary(isempty(case_code), '（从模拟器界面抄，附件1 §4.6）', case_code));
    fprintf('清除干扰源个数        : %d\n', results.cleared_count);
    fprintf('平均定位清除时间      : %s\n', ternary(isnan(results.avg_time), ...
        'n/a（清除数为 0）', sprintf('%.2f s', results.avg_time)));
    fprintf('程序运行时间          : %.2f s   (= /enter → 结束 墙钟)\n', ...
        results.program_run_time);
    fprintf('-------------------------------------\n');
    fprintf('机器狗自记录日志      : %s\n', results.log_path);
    fprintf('日志体积              : %.3f MB（附件1 §4.6：模拟器加密日志上限 2 MB；\n', ...
        sim_client.log_size_mb());
    fprintf('                        此值供演练时核对"有无异常高频循环"）\n');
    fprintf('⚠️ 另需从模拟器导出本局**加密行为日志**（不要改文件名）放入支撑材料\n');
    fprintf('========================================================================\n\n');
end

function out = ternary(cond, a, b)
    if cond, out = a; else, out = b; end
end

% 按"就近"重排待清除的源。排序基准用各源的 c_star（三路清除都是奔它去的），
% 复用 optimize_route 的 NN + 2-opt，不另造算法。
function srcs = order_sources_nearest(srcs, from_pos)
    n = numel(srcs);
    if n < 2
        return;
    end
    pt = zeros(n, 2);
    for i = 1:n
        if isfield(srcs{i}, 'c_star') && ~isempty(srcs{i}.c_star)
            pt(i, :) = srcs{i}.c_star(:)';
        else
            pt(i, :) = from_pos(:)';
        end
    end
    order = optimize_route(pt, from_pos);
    if numel(order) == n
        srcs = srcs(order);
    end
end

%% ========================================================================
%  辅助函数
%% ========================================================================

function config = load_config(problem_type)
    %% 加载配置参数
    config = struct();

    % 模拟器参数
    config.simulator_url = 'http://127.0.0.1:2026';
    % robot_id 由 main_Q3Q4 运行期注入（附件2 §5.1 要求等于当前登录队号；
    % 格式规范要求支撑材料隐去队号 ⇒ 此处故意不设默认值）
    config.robot_id = '';

    % 题设参数
    config.R_domain = 1800;          % 圆域半径 [m]
    config.R_sensor = 1000;          % 最坏接收半径 [m]
    config.R_clear = 20;             % 清除半径 [m]
    config.R_near = 5;               % near 阈值 [m]
    config.velocity = 5;             % 移动速度 [m/s]
    config.epsilon_deg = 1;          % 示向度误差 [°]
    config.n_channels = 20;          % 频道数

    % 时间参数
    config.T_measure = 5;            % 检测耗时 [s]
    config.T_switch = 1;             % 切换频道耗时 [s]
    config.T_clear_success = 5;      % 清除成功耗时 [s]
    config.T_clear_fail = 3;         % 清除失败耗时 [s]
    config.time_reserve = 60;        % 预留收尾时间 [s]

    % 网格间距 d：2-观测要求"每源至少 2 个格点落在 1000 m 内"⇒ 第二近邻 ≈ d ⇒ d ≤ 1000
    % d=1500 已实测不可用，见《调优与补丁记录》§六
    config.grid_spacing = 1000;

    % Q3 检测点布局：径向档外环半径。有值 ⇒ 径向（中心 + 6@d + 6@r_outer，两环错开 30°）；
    % 空/0 ⇒ 三角格。1300 的定档与被否决的更紧档见《调优与补丁记录》P-6。
    config.r_outer = 1300;

    % Homing 参数
    config.lambda_ideal = 2 * sind(0.5);  % 理想收缩率 = 0.0174531
    config.lambda_safe = sind(1) + 2 * deg2rad(1);  % 工程收缩率 = 0.0523590
    config.R_star = 84.0369;         % 扫掠/homing 拐点 [m]
    % homing 收敛与时间预算的三个上限（原实现步长恒定且无衰减 ⇒ 原地循环不收敛）
    config.R_homing_step_max = 300;  % 初始步长上限 [m]
    config.homing_max_iter   = 12;   % 最大迭代次数
    config.homing_max_move   = 2500; % 单次 homing 移动上限 [m]（超了就停，别吃掉整个窗口）

    % 覆盖参数
    config.coverage_density = 2*pi/(3*sqrt(3));  % 1.2091996
end
