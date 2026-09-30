% CUMCM2026 B题 Q3/Q4 -- 机器狗搜索定位与清除主程序
% 用法（推荐双击同目录的 run_Q4.bat）:
%   main_Q3Q4('Q3', '<参赛队号>')                        % 最小调用
%   main_Q3Q4('Q4', '<参赛队号>', '<测试案例编码>')        % Q4
%   main_Q3Q4('Q3', '<参赛队号>', '', [], 1000, [], 0)   % 强制回退三角格（对照跑）
%

function results = main_Q3Q4(problem_type, robot_id, case_code, sim_url, grid_spacing, enter_wait_s, r_outer)
    %% 0. 参数检查与初始化
    if nargin < 1 || isempty(problem_type)
        problem_type = 'Q3';
    end
    if nargin < 3
        case_code = '';       % 测试案例编码（附件1），可留空
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
    fprintf('\n');
    fprintf('  CUMCM2026 B题 %s - 机器狗自动搜索定位与清除\n', problem_type);
    fprintf('\n');
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

    % 第 7 参数: > 0 覆写外环半径; <= 0 强制回退三角格
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

    % 队号必须运行期传入：附件2 要求 robot_id 逐字节等于当前登录队号
    if nargin < 2 || isempty(robot_id)
        error(['缺少参赛队号。请用:  matlab -batch "main_Q3Q4(''%s'',''<参赛队号>'')"' ...
               newline '或直接双击同目录的 run_Q4.bat（会提示输入队号）。'], problem_type);
    end
    config.robot_id = robot_id;
    fprintf('[队号] robot_id = %s（运行期传入）\n', config.robot_id);
    if ~isempty(case_code)
        fprintf('[案例] 测试案例编码 = %s\n', case_code);
    end

    %% 2. 连接模拟器
    fprintf('[模拟器] 连接中...\n');
    sim_client = SimulatorClient(config.simulator_url, config.robot_id);

    % /enter 等待预算可覆写（批量连跑时局间要等人点确认开始测试）
    if ~isempty(enter_wait_s)
        sim_client.enter_wait_s = enter_wait_s;
        fprintf('[模拟器] /enter 等待预算 = %.0f s\n', sim_client.enter_wait_s);
    end

    % 进入测试
    try
        enter_resp = sim_client.enter;
        fprintf('[模拟器] /enter 成功！本局可用现实时间: %.1f s\n', ...
            enter_resp.remaining_real_duration_s);
        if enter_resp.remaining_real_duration_s < 1200
            fprintf('[提示] 不足 1200 s -- 说明 /enter 晚于窗口开始 5 分钟，按剩余时间规划\n');
        end
    catch ME
        error('[错误] 模拟器连接/进入失败: %s', ME.message);
    end

    %% 3. 生成检测点网格
    fprintf('\n[阶段 1] 生成检测点网格...\n');
    is_Q4 = strcmp(problem_type, 'Q4');

    % Q4 专属量先给默认值 -- 下面 log_record 用的是 ternary，两侧都会被求值
    surr_ok = NaN;
    surr_fail = NaN;
    surr_stats = struct('fail_rate', NaN, 'third_nearest_max', NaN);
    dz = struct('passed', NaN, 'witness', [], 'G', [], 'n_hit', 0);
    %  ternary 的两个分支都会被求值 -> 这些默认值必须字段齐全，
    %    否则 Q3 走到这一行会因访问不存在的字段而报错。
    grid_info = struct('n_ring', NaN, 'ring_kind', 'n/a');

    if is_Q4
        % Q4：检测点集（ring 档 = 内层格 + 外层正 12 边形环，25 点）
        [detection_points, grid_info] = Q4_extensions.generate_extended_grid(...
            config.grid_spacing, config.R_domain, config.R_sensor, config.q4_grid_mode);

        % 全域 surrounding 自检（边界带加密）
        [surr_ok, surr_fail, ~, surr_stats] = Q4_extensions.check_surrounding_all(...
            detection_points, config.R_domain, config.R_sensor);
        if ~surr_ok
            warning(['[Q4] 全域 surrounding 自检未通过（%d 点，%.2f%%）' ...
                     ' -- 策略的100%% 清除依据不成立，先查环带宽度（须 >= d，不是 d/sqrt(3)）'], ...
                surr_fail, 100 * surr_stats.fail_rate);
        end

        % 死角反例（正面）：G=(1800,0)、u=(1,0) 必须能找到圆外侧的可见点
        dz = Q4_extensions.deadzone_case(detection_points, config.R_domain, config.R_sensor);
        if dz.passed
            fprintf('[死角回归]  G=(%.0f,0)、u=(1,0)：可见点 %s（距 %.1f m，共 %d 个）\n', ...
                config.R_domain, mat2str(dz.witness), ...
                norm(dz.witness - dz.G), dz.n_hit);
        else
            warning(['[Q4] 死角反例回归失败：环带里找不到 p_x >= %.0f 的可见点' ...
                     ' -- 环带被裁掉了'], config.R_domain);
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
        fprintf('[自检] 覆盖验证通过\n');
    end

    % 记录本局实际用的网格档，供事后分档统计（两种档的日志其余字段不可辨）
    sim_client.log_record('grid_info', struct( ...
        'grid_style', ternary(is_Q4, 'q4_extended', ...
                              ternary(isempty(config.r_outer), 'triangular', 'radial')), ...
        'r_outer', ternary(isempty(config.r_outer), NaN, config.r_outer), ...
        'grid_spacing', config.grid_spacing, ...
        'n_points', size(detection_points, 1), ...
        'grid_mode', ternary(is_Q4, config.q4_grid_mode, 'q3'), ...
        'ring_kind', ternary(is_Q4, grid_info.ring_kind, 'n/a'), ...
        'R_domain', config.R_domain, ...
        'R_sensor', config.R_sensor, ...
        'surrounding_ok', ternary(is_Q4, surr_ok, NaN), ...
        'surrounding_fail', ternary(is_Q4, surr_fail, NaN), ...
        'third_nearest_max', ternary(is_Q4, surr_stats.third_nearest_max, NaN), ...
        'deadzone_ok', ternary(is_Q4, dz.passed, NaN)));

    %% 4. 初始化状态管理器
    fprintf('\n[阶段 2] 初始化状态管理...\n');
    state = ChannelStateMachine(config.n_channels, size(detection_points, 1));

    %% 5. 阶段 A: 侦察 -- 扫描检测点（动态重规划 + 发现即清除）
    fprintf('\n[阶段 A] 侦察阶段 - 扫描检测点（动态重规划）...\n');
    % 每步都从当前落点重规划，不走一次算好的固定顺序
    n_pts = size(detection_points, 1);
    remaining = true(n_pts, 1);
    step_i = 0;
    n_skip_queued = 0;   % 被跳过的重复检测次数（免测集命中数）
    n_skip_ray = 0;      % 被声线过滤跳过的测量次数（几何上不可能看到）
    n_deferred = 0;      % 因定位太松被推迟派发的次数
    discovered_sources = cell(0);  % 阶段 B/C 兜底用的未清源
    cur_pos = [0, 0];              % 当前落点（供就近排序）
    current_channel = 1;           % 当前测向机频道
    pending = cell(0);             % 已定位但未清除的源
    % 三路清除的次数与耗时分布（Q3 档 direct 占 ~89%/94.8%）
    mode_count = struct('direct', 0, 'sweep', 0, 'homing', 0, 'homing_fallback', 0);
    mode_cost  = struct('direct', 0, 'sweep', 0, 'homing', 0, 'homing_fallback', 0);
    r_mec_all  = [];               % 本局全部交会结果的 R_MEC（供分布统计）
    n_triangulate_fail = 0;        % 交会失败次数（退化配对：两观测夹角过小导致 R_MEC 假性偏小）
    step_guard = 0;                     % 防死循环护栏（任何调度逻辑出错都退化成"收尾"而不是卡死）
    while any(remaining) || ~isempty(pending)
        step_guard = step_guard + 1;
        if step_guard > 20 * n_pts + 200
            warning(['[Q4] 主循环迭代达上限 %d（格点 %d 个）-> 强制收尾。' ...
                     '这是不该发生的，请把本局日志发回来定位。'], step_guard, n_pts);
            break;
        end
        % 防御：清掉空槽（否则 `~isempty(pending)` 可能永远为真 -> 死循环）
        if ~isempty(pending)
            pending = pending(~cellfun(@isempty, pending));
        end
        % 任务表 = 剩余格点 ∪ 待清源，整体做 2-opt 取第一站
        %   锁死格点巡游首站 + 按绕行代价 τ 插清 -> 离线 8 种子扫 τ 均劣于本方案。
        %   一次规划整条任务序列、连走 K 步再重规划 -> 实机在阶段 A 停滞。
        %   两条路均可排除：把源混进任务表做整体 2-opt，等价于对"格点 ∪ 源"
        %   做动态 TSP，比"固定格点巡游 + 插入"更接近最优。
        %   （"事后重排同一批点只需实走的 70~89%"衡量的是静态最优，
        %    动态策略取不到该收益。）
        tasks = detection_points(remaining, :);
        kind_of = repmat({'grid'}, 1, size(tasks, 1));
        idx_of = find(remaining)';
        for k = 1:numel(pending)
            if isempty(pending{k}), continue; end
            if ~isfield(pending{k}, 'c_star') || isempty(pending{k}.c_star), continue; end
            % 定位太松的先不派发
            % 两条近共线的观测能给出 R_MEC 数百米的 L（离线 seed=11 为 600.9 m）。若当场派发，
            % homing 会断线、扫掠要几百次 /clear（该档 444 次 / 1344 s）。
            % 推迟派发 -> 该频道继续被扫描测到 -> 楔形变多 -> L 收紧后再清，便宜得多。
            % 只在"还有格点可扫"时推迟；扫完了就不再推迟，交给三路清除兜底。
            rq = inf;
            if isfield(pending{k}, 'R_MEC'), rq = pending{k}.R_MEC; end
            if any(remaining) && rq > config.clear_dispatch_max
                n_deferred = n_deferred + 1;
                continue;
            end
            tasks(end+1, :) = pending{k}.c_star(:)';
            kind_of{end+1} = 'clear';
            idx_of(end+1) = k;
        end
        if isempty(tasks), break; end
        ord = optimize_route(tasks, cur_pos);
        task_kind = kind_of{ord(1)};
        task_pick = idx_of(ord(1));

        if strcmp(task_kind, 'clear')
            % 就近去清一个已知源
            src = pending{task_pick};
            pending(task_pick) = [];        % 用元素删除（不是置空），保证 pending 会缩短
            if state.is_cleared(src.channel), continue; end
            say(config.verbose, '  [调度] 就近清除 频道 %d（距 %.0f m，待清 %d 个）\n', ...
                src.channel, norm(src.c_star(:)' - cur_pos), numel(pending));
            [ok_c, cost_c, mode_c] = clear_source(src, sim_client, config);
            [mode_count, mode_cost] = bump_mode(mode_count, mode_cost, mode_c, cost_c);
            if ok_c
                state.mark_cleared(src.channel);
                cur_pos = sim_client.last_pos;   % 用真实落点（扫掠/ homing 后未必在 c*）
                fprintf('  [清除] 频道 %d 成功 (%s, %.1f s)\n', src.channel, mode_c, cost_c);
            else
                discovered_sources{end+1} = src;
                fprintf('  [清除] 频道 %d 未成功 (%s) -> 转入阶段 B 兜底\n', src.channel, mode_c);
            end
            continue;
        end

        % 就近去扫一个格点
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

        % 免测集 = 已清除 并 已定位得足够准的待清频道
        % 依据：triangulate_source 用多条楔形求交，重测能继续收紧 L。
        %   原做法"只要在待清队列就跳过重测"会把差的 L 冻住 --
        %   实机与离线统计中 R_MEC 的 p90 可达 1379~1739 m（两条观测近共线 -> 交会退化成
        %   几乎整个圆域），随后扫掠要几百次 /clear（离线 seed=11 为 492 次）。
        %   现在只跳 R_MEC <= queue_skip_r_mec 的；L 还大的频道继续测，
        %   让更多楔形把 L 收紧 -- 这一步不花额外移动，只花本来也要花的检测时间。
        skip_queued = false(config.n_channels, 1);
        for k_q = 1:numel(pending)
            if ~isempty(pending{k_q}) && isfield(pending{k_q}, 'channel')
                rq = inf;
                if isfield(pending{k_q}, 'R_MEC'), rq = pending{k_q}.R_MEC; end
                if rq <= config.queue_skip_r_mec
                    skip_queued(pending{k_q}.channel) = true;
                end
            end
        end
        for ch = 1:config.n_channels
            skip_here = false;
            if state.is_cleared(ch)
                continue;
            end
            if skip_queued(ch)
                n_skip_queued = n_skip_queued + 1;
                continue;
            end

            % 声线过滤
            % 实机统计：每个有源频道平均被测 10.9 次（交会只需 2~3 次）
            % -> 约 144 次/局为无效测量 ~= 10% 的 T_vir。原因：频道在拿到第 2 个观测前，
            % 会在每个格点被"盲测"一遍（多数点根本看不见它）。
            % 射线可见性判据，实现在 Q4_extensions 内；
            % 单边正确 -> 永不丢掉真正的第 2 个观测，完备性不受影响。
            % 已入队且 R_MEC 够小的频道由上面的 skip_queued 处理，这里只打"1 条观测"窗口。
            obs_ch = state.get_observations(ch);
            if numel(obs_ch) == 1
                if ~Q4_extensions.ray_can_see(obs_ch(1).position, obs_ch(1).svd_deg, pos, config)
                    n_skip_ray = n_skip_ray + 1;
                    continue;
                end
            elseif numel(obs_ch) >= 2
                % >=2 条观测时已有紧的估计区域：用 c*/R_MEC 做更紧的距离界（同样是充要的保守向）
                for k_q = 1:numel(pending)
                    if ~isempty(pending{k_q}) && isfield(pending{k_q}, 'channel') ...
                            && pending{k_q}.channel == ch ...
                            && isfield(pending{k_q}, 'c_star') && ~isempty(pending{k_q}.c_star)
                        if norm(pos - pending{k_q}.c_star(:)') - pending{k_q}.R_MEC > config.R_sensor
                            n_skip_ray = n_skip_ray + 1;
                            skip_here = true;
                        end
                        break;
                    end
                end
                if skip_here, continue; end
            end

            % 检测
            result = sim_client.measure(pos(1), pos(2), ch);
            current_channel = ch;

            % 更新状态
            state.update(ch, pt_idx, result.measure_result, result, pos);

            % 处理结果
            if strcmp(result.measure_result, 'direction')
                % 发现信号，记录示向度
                say(config.verbose, '  [发现] 频道 %d 在点 %d 处测得示向度 %.2f度\n', ...
                    ch, pt_idx, result.svd_deg);

                % 拿到 2 个观测就地交会定位并入待清队列（等待更多观测不会更准，
                % 因为三角化只用前两条）。清不掉则交阶段 B/C 兜底。
                if state.has_two_observations(ch)
                    source_info = triangulate_source(state.get_observations(ch), config);
                    if isempty(source_info)
                        % 观测确实有 2 条却交会不出区域 -> 退化配对（两观测近共线 / 交会区被截断）：
                        % 两观测夹角过小（如 2.2度）导致 R_MEC 假性偏小 -> 一局 97 次无效 /clear。
                        n_triangulate_fail = n_triangulate_fail + 1;
                        fprintf('  [定位] 频道 %d 交会失败（退化配对）-> 留待阶段 C 单方位 homing\n', ch);
                    else
                        r_mec_all(end+1) = source_info.R_MEC; %#ok<AGROW>
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
                            fprintf(['  [定位] 频道 %d 已定位 R_MEC=%.2f m（楔形 %d 条）' ...
                                     ' -> 入待清队列\n'], ch, source_info.R_MEC, ...
                                     ternary(isfield(source_info,'n_wedges'), source_info.n_wedges, 2));
                        else
                            % 已在队列里：新观测可以把 L 收得更紧（楔形越多交集越小）
                            % -> 取 R_MEC 更小的那个。这一步不花任何移动成本，
                            % 却能把后续的清除路子从 homing 拉回直接/扫掠。
                            for k_q = 1:numel(pending)
                                if isempty(pending{k_q}) || ~isfield(pending{k_q}, 'channel') ...
                                        || pending{k_q}.channel ~= ch
                                    continue;
                                end
                                if source_info.R_MEC < pending{k_q}.R_MEC - 1e-9
                                    old_r = pending{k_q}.R_MEC;
                                    pending{k_q} = source_info;
                                    fprintf(['  [定位] 频道 %d 楔形增至 %d 条 -> ' ...
                                             'R_MEC %.1f -> %.1f m\n'], ch, ...
                                             ternary(isfield(source_info,'n_wedges'), ...
                                                     source_info.n_wedges, 2), ...
                                             old_r, source_info.R_MEC);
                                end
                                break;
                            end
                        end
                    end
                end

            elseif strcmp(result.measure_result, 'near')
                % 距离很近，直接清除
                say(config.verbose, '  [Near] 频道 %d 在 5m 内\n', ch);
                clear_result = sim_client.clear(pos(1), pos(2), ch);
                if strcmp(clear_result.clear_result, 'success')
                    state.mark_cleared(ch);
                    fprintf('  [清除] 频道 %d 清除成功 \n', ch);
                end

            elseif strcmp(result.measure_result, 'no_signal')
                % Q4 的 no_signal 是三义（无源 / 超距 / 盲区，附录2）-> 单点不蕴含无源。
                % 判空只能靠"全 P 遍历"（ChannelStateMachine 已按 position_id 去重计数）。
                %  扇区探针不在本条分支触发：它必须由"已有示向度"的观测点发起。
                %    （早期版本在此调 handle_no_signal_Q4 并把检测点本身当源位置估计，
                %      于是"是否被 surrounding"恒真 -> 探针永不触发，属静默死代码。）
            end
        end

        % 定期检查完备性
        if mod(step_i, 3) == 0
            [complete, stats] = state.check_completeness;
            % 紧凑进度行（每 3 步一条，替代逐点流水）
            fprintf('[扫描 %2d/%d] 清除 %2d | 待清 %d | 确认空 %2d | 虚拟 %6.0f s\n', ...
                sum(~remaining), n_pts, stats.cleared, numel(pending), ...
                stats.confirmed_empty, sim_client.virtual_time);
        end
    end

    % 报告声线过滤的收益
    if n_skip_ray > 0
        fprintf(['[优化] 声线过滤跳过 %d 次几何上不可能看到的测量 ' ...
                 '-> 省约 %.0f s 虚拟时间（5 s 检测 + 1 s 切换/次）\n'], ...
            n_skip_ray, n_skip_ray * 6);
    end

    % 报告免测跳过的收益
    if n_skip_queued > 0
        fprintf(['[优化] 跳过已定位且已排队待清的重复检测 %d 次 ' ...
                 '-> 省约 %.0f s 虚拟时间（5 s 检测 + 1 s 切换/次）\n'], ...
            n_skip_queued, n_skip_queued * 6);
    end

    %% 5.5 扇区探针补测（Q4）
    % 覆盖只保证"每个源至少被 1 个格点发现"，不保证被 2 个发现；而交会定位需要 2 个观测
    % -> 只被 1 个发现的频道 L 无界、永不清除（退化情形）。
    % Q4 的补救是扇区探针（引理 Q4-D）：从该观测点沿垂直视线方向偏移 ±b 补测，
    % 两点中至少一个仍落在同一半平面内 -> <=2 次即可拿到第二条同扇区示向度。
    probe_stats = struct('channels', 0, 'used', 0, 'requests', 0, 'hit_near', 0);
    single_obs = [];
    for ch = 1:config.n_channels
        if state.is_cleared(ch) || state.is_confirmed_empty(ch), continue; end
        if numel(state.get_observations(ch)) == 1
            single_obs(end+1) = ch; %#ok<AGROW>
        end
    end

    if isempty(single_obs)
        fprintf('\n[探针] 无单观测频道（每个未清除频道都有 >= 2 个观测）-> 无需补测\n\n');
    elseif ~is_Q4
        fprintf(['\n[探针] 单观测频道 %s -- Q3 全向源下属几何巧合，' ...
                 '交阶段 C homing 兜底（Q4 才启用扇区探针）\n\n'], mat2str(single_obs));
    else
        fprintf('\n[探针] 单观测频道 %s -> 启用扇区探针补测\n', mat2str(single_obs));

        % 按就近顺序访问各观测点（探针是局部动作，不打乱主巡游）
        tgt = zeros(numel(single_obs), 2);
        for k = 1:numel(single_obs)
            o = state.get_observations(single_obs(k));
            tgt(k, :) = o(1).position;
        end
        ord = optimize_route(tgt, cur_pos);

        for k = ord(:)'
            ch = single_obs(k);
            if state.is_cleared(ch) || state.is_confirmed_empty(ch), continue; end
            if sim_client.remaining_time < config.time_reserve
                fprintf('       [探针] 现实时间不足（剩 %.0f s）-> 中止补测\n', sim_client.remaining_time);
                break;
            end
            o = state.get_observations(ch);
            if numel(o) ~= 1, continue; end

            probe_stats.channels = probe_stats.channels + 1;
            out = Q4_extensions.sector_probe(o(1).position, o(1).svd_deg, ch, ...
                                             sim_client, config);
            probe_stats.requests = probe_stats.requests + out.n_probe;
            cur_pos = sim_client.last_pos;

            if ~out.found, continue; end
            probe_stats.used = probe_stats.used + 1;

            if strcmp(out.kind, 'near')
                probe_stats.hit_near = probe_stats.hit_near + 1;
                r = sim_client.clear(out.position(1), out.position(2), ch);
                if strcmp(r.clear_result, 'success')
                    state.mark_cleared(ch);
                    cur_pos = sim_client.last_pos;
                    [mode_count, mode_cost] = bump_mode(mode_count, mode_cost, 'direct', config.T_clear_success);
                    fprintf('       [探针] 频道 %d 由 near 偏移点直接清除 \n', ch);
                end
            else
                state.update(ch, -ch, 'direction', struct('svd_deg', out.svd_deg), out.position);
                if state.has_two_observations(ch)
                    src = triangulate_source(state.get_observations(ch), config);
                    if isempty(src)
                        fprintf('       [探针] 频道 %d 交会失败（退化配对）-> 留待阶段 C\n', ch);
                        continue;
                    end
                    r_mec_all(end+1) = src.R_MEC; %#ok<AGROW>
                    fprintf('       [探针] 频道 %d 交会成功 R_MEC=%.2f m -> 就地尝试清除\n', ...
                        ch, src.R_MEC);
                    [okc, costc, modec] = clear_source(src, sim_client, config);
                    [mode_count, mode_cost] = bump_mode(mode_count, mode_cost, modec, costc);
                    cur_pos = sim_client.last_pos;
                    if okc
                        state.mark_cleared(ch);
                        fprintf('       [探针] 频道 %d 清除成功 (%s, %.1f s) \n', ch, modec, costc);
                    else
                        discovered_sources{end+1} = src; %#ok<AGROW>
                        fprintf('       [探针] 频道 %d 未清除 (%s) -> 转入阶段 B 兜底\n', ch, modec);
                    end
                end
            end
        end
        fprintf(['       [探针] 小结：补测 %d 个频道，成功补到第二条示向度 %d 个，' ...
                 '共 %d 次 /measure\n\n'], ...
            probe_stats.channels, probe_stats.used, probe_stats.requests);
    end

    %% 6. 阶段 B: 清除（主循环漏掉/清失败的源在此兜底）
    fprintf('\n[阶段 B] 清除阶段...\n');
    % 按"就近"重排清除顺序：只改访问顺序，不动任何判定/清除逻辑
    % （按发现顺序清 vs 就近重排：13160 m -> 8789 m）
    discovered_sources = order_sources_nearest(discovered_sources, cur_pos);
    for i = 1:length(discovered_sources)
        source = discovered_sources{i};

        % 检查是否已清除
        if state.is_cleared(source.channel)
            continue;
        end

        % 三路清除策略
        [success, cost, mode] = clear_source(source, sim_client, config);
        [mode_count, mode_cost] = bump_mode(mode_count, mode_cost, mode, cost);
        if success
            state.mark_cleared(source.channel);
            fprintf('  [清除] 频道 %d 清除成功 (%s, %.1f s) \n', ...
                source.channel, mode, cost);
        end
    end

    %% 7. 阶段 C: 收尾 -- 对"未清除但有示向度"的频道做定向 homing
    % 这些频道已经拿到过示向度（附件2：有 svd_deg 就能定向），
    % 直接从该观测点 homing 逼近，而不是盲目重扫全部格点。
    % 无观测的频道必然已在主循环里被判为 confirmed_empty，不会走到这里。
    fprintf('\n[阶段 C] 收尾 -- 对未清除频道做定向 homing...\n');
    for ch = 1:config.n_channels
        if state.is_cleared(ch) || state.is_confirmed_empty(ch)
            continue;
        end
        obs = state.get_observations(ch);
        if isempty(obs)
            say(config.verbose, '  [收尾] 频道 %d 未清除且无观测（异常情形），跳过\n', ch);
            continue;
        end
        o = obs(1);

        % 收尾优先走"有 L"的路：有 >=2 条观测就能交会出 L -> 可走三路（含扇区无关的扫掠），
        % 而单方位 homing 一旦滑出扇区就断线（Q4 的典型失效模式）。退化配对才退回单方位。
        src = [];
        if numel(obs) >= 2
            src = triangulate_source(obs, config);
        end

        if ~isempty(src)
            fprintf(['  [收尾] 频道 %d 有 %d 个观测 -> 交会 R_MEC=%.2f m，' ...
                     '按三路清除（扫掠对朝向免疫）\n'], ch, numel(obs), src.R_MEC);
            r_mec_all(end+1) = src.R_MEC; %#ok<AGROW>
            [okh, costh, modeh] = clear_source(src, sim_client, config);
        else
            say(config.verbose, '  [收尾] 频道 %d 有 %d 个观测（交会失败）-> 从 (%.1f, %.1f) 沿示向度 %.2f度 homing\n', ...
                ch, numel(obs), o.position(1), o.position(2), o.svd_deg);
            % R_MEC = Inf -> clear_source 必走 homing 分支；start_pos/start_theta 透传到 homing_clear
            src = struct('channel', ch, 'L', [], 'c_star', o.position(:)', ...
                         'R_MEC', Inf, 'D', 0);
            [okh, costh, modeh] = clear_source(src, sim_client, config, o.position(:)', o.svd_deg);
        end
        [mode_count, mode_cost] = bump_mode(mode_count, mode_cost, modeh, costh);
        if okh
            state.mark_cleared(ch);
            fprintf('  [清除] 频道 %d homing 成功 (%.1f s) \n', ch, costh);
        else
            fprintf('  [收尾] 频道 %d homing 未成功（%.1f s）\n', ch, costh);
        end
    end
    [complete, stats] = state.check_completeness;

    %% 8. 退出测试
    fprintf('\n[结束] 调用 /exit...\n');
    exit_resp = sim_client.exit;

    %% 9. 统计结果
    [complete, stats] = state.check_completeness;
    results = struct;
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
    % 表 1 第 4 列：程序运行时间 = /enter -> 结束 的墙钟（附件1）
    results.program_run_time = sim_client.wall_clock_s;
    results.case_code = case_code;
    results.log_path = sim_client.get_log_path;

    % Q4/Q3 指标（供离线分析脚本汇总）
    results.problem_type       = problem_type;
    results.n_grid_points      = size(detection_points, 1);
    results.n_requests         = sim_client.request_counter;
    results.n_measure          = sim_client.n_measure;
    results.n_clear            = sim_client.n_clear;
    results.n_switch           = sim_client.n_switch;
    results.n_channels         = config.n_channels;
    results.n_confirmed_empty  = stats.confirmed_empty;
    results.grid_spacing       = config.grid_spacing;
    results.grid_mode          = ternary(is_Q4, config.q4_grid_mode, 'q3');
    results.mode_count         = mode_count;
    results.mode_cost          = mode_cost;
    results.n_probe_channels   = probe_stats.channels;
    results.n_probe_success    = probe_stats.used;
    results.n_probe_requests   = probe_stats.requests;
    results.n_probe_near       = probe_stats.hit_near;
    results.n_skip_ray         = n_skip_ray;
    results.n_triangulate_fail = n_triangulate_fail;
    if isempty(r_mec_all)
        results.R_MEC_median = NaN; results.R_MEC_max = NaN; results.R_MEC_p90 = NaN;
    else
        results.R_MEC_median = median(r_mec_all);
        results.R_MEC_max    = max(r_mec_all);
        results.R_MEC_p90    = prctile_simple(r_mec_all, 90);
    end
    if is_Q4
        results.surrounding_ok      = surr_ok;
        results.surrounding_fail    = surr_fail;
        results.surrounding_fail_rate = surr_stats.fail_rate;
        results.third_nearest_max   = surr_stats.third_nearest_max;
        results.deadzone_ok         = dz.passed;
        results.n_grid_ring         = grid_info.n_ring;
    else
        results.surrounding_ok = NaN; results.surrounding_fail = NaN;
        results.surrounding_fail_rate = NaN; results.third_nearest_max = NaN;
        results.deadzone_ok = NaN; results.n_grid_ring = NaN;
    end

    sim_client.close_log;   % 写 session_end 并落盘

    % 每局导出机器可读的 summary（"导出数据供再调试"的落点；与 JSONL 同级）
    summary_path = write_run_summary(sim_client.log_dir, problem_type, results, config);
    results.summary_path = summary_path;

    % 本局报告
    bar = repmat('', 1, 74);
    fprintf('\n%s\n', bar);
    fprintf('  %s 本局结果\n', problem_type);
    fprintf('%s\n', bar);

    % ① 表 1 四列（附件3；正式测试只有这四列，不含比例）
    fprintf('\n\n');
    fprintf('  测试案例编码     : %s\n', ...
        ternary(isempty(case_code), '（从模拟器界面获取，附件1）', case_code));
    fprintf('  清除干扰源个数   : %d\n', results.cleared_count);
    fprintf('  平均定位清除时间 : %s\n', ternary(isnan(results.avg_time), ...
        'n/a（清除数为 0）', sprintf('%.2f s', results.avg_time)));
    fprintf('  程序运行时间     : %.2f s   <- /enter -> 结束 的现实墙钟\n', ...
        results.program_run_time);

    % ② 本局读数（口径提示与代价拆解）
    fprintf('\n\n');
    % 口径提示：本程序无法知道源总数（附件2 接口不返回）
    % -> total_count 只是"已清除 + 状态机判为未清"的下界，不是真总数
    if results.total_count > 0
        fprintf('  清除 / 本地状态机总数 : %d / %d（%.1f%%）  <- 分母是本地下界，非真源总数\n', ...
            stats.cleared, results.total_count, results.cleared_ratio * 100);
    else
        fprintf('  清除 / 本地状态机总数 : %d / %d（本局未发现任何源）\n', stats.cleared, 0);
    end
    fprintf('  已确认空的频道        : %d\n', stats.confirmed_empty);
    fprintf('  虚拟时间(定位清除总)  : %.1f s\n', results.virtual_time);

    % 虚拟时间四分解（移动 = 其余三项之外的全部）
    ca = 0;
    if isprop(sim_client, 'clear_action_s'), ca = sim_client.clear_action_s; end
    t_meas = 5 * results.n_measure;
    t_sw   = results.n_switch;
    t_move = results.virtual_time - t_meas - t_sw - ca;
    if results.virtual_time > 0
        fprintf('  时间构成              : 移动 %.0f (%.0f%%) | 检测 %.0f (%.0f%%) | 切频 %.0f (%.0f%%) | 清除 %.0f (%.0f%%)\n', ...
            t_move, 100*t_move/results.virtual_time, ...
            t_meas, 100*t_meas/results.virtual_time, ...
            t_sw,   100*t_sw/results.virtual_time, ...
            ca,     100*ca/results.virtual_time);
    end
    fprintf('  请求数                : %d（检测 %d | 清除 %d | 切频 %d）\n', ...
        results.n_requests, results.n_measure, results.n_clear, results.n_switch);
    fprintf('  日志体积              : %.3f MB（上限 2 MB，附件1）\n', sim_client.log_size_mb);
    fprintf('  自记录日志            : %s\n', results.log_path);
    fprintf('  本局汇总 JSON         : %s\n', results.summary_path);
    fprintf('   另需从模拟器导出本局加密行为日志（不要改文件名）\n');

    % ③ 诊断（排查/调优用；verbose 关时折成一行）
    if config.verbose
        fprintf('\n\n');
        fprintf('  检测点数 N            : %d（档 %s，圆外环带 %s 个）\n', ...
            results.n_grid_points, num2str(results.grid_mode), num2str(results.n_grid_ring));
        fprintf('  三路清除              : direct %d | sweep %d | homing %d | 断线转扫掠 %d\n', ...
            mode_count.direct, mode_count.sweep, mode_count.homing, mode_count.homing_fallback);
        fprintf('  三路本地计时          : direct %.0f | sweep %.0f | homing %.0f | 兜底 %.0f s\n', ...
            mode_cost.direct, mode_cost.sweep, mode_cost.homing, mode_cost.homing_fallback);
        fprintf('  扇区探针              : 补测 %d 频道 / 成功 %d / 请求 %d 次（near %d）\n', ...
            results.n_probe_channels, results.n_probe_success, ...
            results.n_probe_requests, results.n_probe_near);
        fprintf('  声线过滤              : 跳过 %d 次测量（省约 %.0f s）\n', ...
            results.n_skip_ray, results.n_skip_ray * 6);
        fprintf('  交会失败（退化配对）  : %d 次\n', results.n_triangulate_fail);
        if isnan(results.R_MEC_median)
            fprintf('  R_MEC 分布            : 本局无成功交会\n');
        else
            fprintf('  R_MEC 分布            : 中位 %.1f | p90 %.1f | 最大 %.1f m\n', ...
                results.R_MEC_median, results.R_MEC_p90, results.R_MEC_max);
        end
        if is_Q4
            fprintf('  surrounding 自检      : %s（失败 %d，第三近邻最大 %.1f m）\n', ...
                ternary(surr_ok, '通过', '未通过'), surr_fail, surr_stats.third_nearest_max);
            fprintf('  死角反例回归          : %s\n', ternary(dz.passed, '通过', '未通过'));
        end
    else
        fprintf('  诊断                  : N=%d | 三路 %d/%d/%d/%d | 探针 %d | 声线过滤 %d | R_MEC 中位 %s | 交会失败 %d\n', ...
            results.n_grid_points, mode_count.direct, mode_count.sweep, mode_count.homing, ...
            mode_count.homing_fallback, results.n_probe_channels, results.n_skip_ray, ...
            ternary(isnan(results.R_MEC_median), 'n/a', sprintf('%.1f', results.R_MEC_median)), ...
            results.n_triangulate_fail);
    end
    fprintf('%s\n\n', bar);
    return;
end




function say(v, fmt, varargin)
%SAY 只在 verbose 打开时打印（默认关 -- 一局的逐点流水太长，会把重点埋掉）
    if v, fprintf(fmt, varargin{:}); end
end

function out = ternary(cond, a, b)
    if cond, out = a; else, out = b; end
end

% 三路清除的次数/耗时计数（mode 取 'direct' / 'sweep' / 'homing'）
function [cnt, cst] = bump_mode(cnt, cst, mode, cost)
    m = '';
    if ischar(mode), m = mode; elseif isstring(mode) && isscalar(mode), m = char(mode); end
    if ~isempty(m) && isfield(cnt, m)
        cnt.(m) = cnt.(m) + 1;
        cst.(m) = cst.(m) + cost;
    end
end

% 简易 90 分位（不依赖 Statistics Toolbox -- 避免 pdist 缺工具箱的问题）
function v = prctile_simple(x, p)
    x = sort(x(:));
    if isempty(x), v = NaN; return; end
    k = max(1, min(numel(x), ceil(p / 100 * numel(x))));
    v = x(k);
end

% 写机器可读的本局汇总（logs/run_summary_*.json），供离线汇总脚本汇总成表
function p = write_run_summary(log_dir, problem_type, results, config)
    stamp = datestr(now, 'yyyymmdd_HHMMSS');
    p = fullfile(log_dir, sprintf('run_summary_%s_%s.json', problem_type, stamp));
    try
        s = struct;
        s.schema = 'q3q4_run_summary/1';
        s.problem_type = problem_type;
        s.stamp = stamp;
        s.team = config.robot_id;
        s.sim_url = config.simulator_url;      % 端口是区分"实机 / 离线回放"的现成字段
        % 实机默认 http://127.0.0.1:2026；离线回放一律用别的端口 -> 非 2026 即回放。
        % （口径：分析实机数字前先按端口过滤。）
        s.is_replay = isempty(strfind(config.simulator_url, ':2026')); %#ok<STREMP>
        s.case_code = results.case_code;
        s.cleared_count = results.cleared_count;
        s.total_count_local = results.total_count;      % 本地状态机下界，非真源总数
        s.cleared_ratio_local = results.cleared_ratio;
        s.virtual_time_s = results.virtual_time;
        s.avg_time_s = results.avg_time;
        s.program_run_time_s = results.program_run_time;
        s.n_grid_points = results.n_grid_points;
        s.n_grid_ring = results.n_grid_ring;
        s.grid_spacing = results.grid_spacing;
        s.grid_mode = results.grid_mode;
        s.n_requests = results.n_requests;
        s.n_measure = results.n_measure;
        s.n_clear = results.n_clear;
        s.n_switch = results.n_switch;
        s.grid_style = ternary(strcmp(problem_type, 'Q4'), 'q4_extended', 'q3_style');
        s.surrounding_ok = results.surrounding_ok;
        s.surrounding_fail = results.surrounding_fail;
        s.surrounding_fail_rate = results.surrounding_fail_rate;
        s.third_nearest_max = results.third_nearest_max;
        s.deadzone_ok = results.deadzone_ok;
        s.mode_count = results.mode_count;
        s.mode_cost = results.mode_cost;
        s.n_probe_channels = results.n_probe_channels;
        s.n_probe_success = results.n_probe_success;
        s.n_probe_requests = results.n_probe_requests;
        s.n_probe_near = results.n_probe_near;
        s.n_skip_ray = results.n_skip_ray;
        s.n_triangulate_fail = results.n_triangulate_fail;
        s.n_confirmed_empty = results.n_confirmed_empty;
        s.R_MEC_median = results.R_MEC_median;
        s.R_MEC_p90 = results.R_MEC_p90;
        s.R_MEC_max = results.R_MEC_max;
        s.log_path = results.log_path;

        fid = fopen(p, 'w');
        if fid > 0
            fprintf(fid, '%s\n', jsonencode(s, 'PrettyPrint', true));
            fclose(fid);
            fprintf('[导出] 本局汇总: %s\n', p);
        end
    catch ME
        warning('[导出] 汇总写入失败: %s', ME.message);
    end
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

%  辅助函数

function config = load_config(problem_type)
    %% 加载配置参数
    config = struct;

    % 模拟器参数
    config.simulator_url = 'http://127.0.0.1:2026';
    % robot_id 由 main_Q3Q4 运行期注入（附件2 要求等于当前登录队号），此处不设默认值
    config.robot_id = '';

    % 题设参数
    config.R_domain = 1800;          % 圆域半径 [m]
    config.R_sensor = 1000;          % 最坏接收半径 [m]
    config.R_clear = 20;             % 清除半径 [m]
    config.R_near = 5;               % near 阈值 [m]
    config.velocity = 5;             % 移动速度 [m/s]
    config.epsilon_deg = 1;          % 示向度误差 [度]
    config.n_channels = 20;          % 频道数

    % 时间参数
    config.T_measure = 5;            % 检测耗时 [s]
    config.T_switch = 1;             % 切换频道耗时 [s]
    config.T_clear_success = 5;      % 清除成功耗时 [s]
    config.T_clear_fail = 3;         % 清除失败耗时 [s]
    config.time_reserve = 60;        % 预留收尾时间 [s]

    % 网格间距 d：2-观测要求"每源至少 2 个格点落在 1000 m 内"-> 第二近邻 ~= d -> d <= 1000
    % d=1500 不可用
    config.grid_spacing = 1000;

    % Q3 检测点布局：径向档外环半径。有值 -> 径向（中心 + 6@d + 6@r_outer，两环错开 30度）；
    % 空/0 -> 三角格。外环半径定档 1300 m。
    config.r_outer = 1300;

    % Q4 检测点集档位：
    %   'ring'   = 内层圆内规则格（13 点）+ 外层半径 R_domain+100 的正 12 边形 -> 25 点
    %              MST 30000 -> 17407 m（−42%），最远半径 2645.8 -> 1900。默认档。
    %   'lattice'= 外扩规则格环带（宽度 = d）-> 31 点。留作对照与回归。
    % 换档依据：实机 T_vir 里移动占 74~78%，降移动只能降点数或外径。
    % 两个模式下都必须存在（ternary 会求值两侧；Q3 下仅占位）
    config.q4_grid_mode = 'ring';

    % 交会时最多用几条楔形（观测）。楔形只多不少地收紧 L -> 越多越准；
    % 上限只为控住 polyshape 逐次求交的耗时（每条楔形 = 一次布尔交）。
    config.max_wedges = 6;

    % 免测门限：待清频道的 R_MEC <= 此值时才"停止重测"（否则继续测以收紧 L）。
    % 取扫掠/homing 拐点 84.0369 m -- 定位精度已足以走便宜的清除路子。
    config.queue_skip_r_mec = 84.0369;

    % 派发门限：待清源的 R_MEC 大于此值且还有格点可扫时，先不派发，
    % 让它继续被扫描测到、攒更多楔形把 L 收紧（见上文派发处注释）。
    % 取 150 m：扫掠成本 ~= 10·1.2092(R/20)^2 在此约 700 s，再大就不如等一等。
    config.clear_dispatch_max = 150;

    % 顺路插清的绕行门限 τ [m]：
    %   detour = |cur-c*| + |c*-next格点| - |cur-next格点| <= τ 才顺路去清。
    %   τ 大 -> 更早清（该频道更早停止被测量，但移动更多）；τ=0 -> 只接受完全顺路。
    %   定档：离线扫 τ = 0/150/300/600/inf。

    % Homing 参数
    config.lambda_ideal = 2 * sind(0.5);  % 理想收缩率 = 0.0174531
    config.lambda_safe = sind(1) + 2 * deg2rad(1);  % 工程收缩率 = 0.0523590
    config.R_star = 84.0369;         % 扫掠/homing 拐点 [m]
    % homing 收敛与时间预算的三个上限（原实现步长恒定且无衰减 -> 原地循环不收敛）
    config.R_homing_step_max = 300;  % 初始步长上限 [m]
    config.homing_max_iter   = 12;   % 最大迭代次数
    config.homing_max_move   = 2500; % 单次 homing 移动上限 [m]（超了就停，避免占满整局窗口）

    % 覆盖参数
    config.coverage_density = 2*pi/(3*sqrt(3));  % 1.2091996

    % 逐点流水开关：默认关。一局的 [发现]/[定位]/[调度] 有几百行，
    % 真正的重点（自检、清除成功、警告、最终报告）会被埋掉。
    % 要排查问题时把它置 true。
    config.verbose = false;

    % Q4 参数
    % 扇区探针步长 b（引理 Q4-D 的垂直偏移量）：b 过大 -> sqrt(r^2+b^2) 出 R_eff ->
    % 两次探针都 no_signal。取 100 m；仍失败时 Q4_extensions.sector_probe 会自动
    % 减半到 25 m 再试一轮（共 <=2 轮 4 次）。
    config.sector_probe_step = 100;

    % homing 断线后转扫掠的上限 [m]：定向源滑出扇区会导致示向度中断，homing 于是失效；
    % 扫掠与朝向无关（命题 Q4-B），是唯一对朝向免疫的兜底。
    % 定档依据（离线 8 种子）：250 m 时 seed=11/42 各有 1 源（R_MEC=304 m）
    % homing 第一步就断线且够不着兜底 -> 该局掉到 92.3%。此情形必须清掉：
    % 上限放到 1000 m，真正的成本闸门交给下面的 sweep_budget_s（虚拟时间预算）
    % 与 clear_source 里的中心数上限。
    config.R_sweep_fallback_max = 1000;
    % 单次扫掠的虚拟时间预算 [s]：超了就收手（宁可留白也不吃光整局）。
    % 扫掠中心集由 `sweep_centers(L, 20)` 按 L 的实际形状生成（细长 L 远少于圆盘估计），
    % 常见 R_MEC <= 60 m 只需十几次 /clear（典型 8~20 次）。
    config.sweep_budget_s = 6000;
end
