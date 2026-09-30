% ========================================================================
% clear_source -- 三路清除策略
%   R_MEC <= R_clear(20)        直接清除（在 c* 一次 /clear）
%   R_MEC <= R_star(84.0369)    扫掠清除（用 20 m 圆盘覆盖整个 L，逐个试）
%   R_MEC > R_star             Homing 逼近
% 拐点来源：扫掠成本 ~= 10·N（N = 覆盖 L 所需 20-盘数），homing ~= 213.49 s（与 R_MEC 无关），

function [success, cost, mode] = clear_source(source, sim_client, config, start_pos, start_theta)
    R_MEC = source.R_MEC;
    channel = source.channel;
    c_star = source.c_star;  % 最小包围圆圆心

    if R_MEC <= config.R_clear
        % 直接清除
        mode = 'direct';
        [success, cost] = direct_clear(c_star, channel, sim_client, config);

    elseif R_MEC <= config.R_star
        % 扫掠清除（扇区无关；覆盖整个 L）
        mode = 'sweep';
        if isfield(source, 'L') && ~isempty(source.L) && size(source.L, 1) >= 3
            [success, cost] = sweep_clear_L(source.L, R_MEC, c_star, channel, ...
                                            sim_client, config);
        else
            % L 退化（无顶点）-> 退回旧的"以 c* 为心的定向短走"
            [success, cost] = sweep_clear_directed(R_MEC, c_star, channel, sim_client, config);
        end

    else
        % Homing 逼近（阶段 C 会透传 start_pos/start_theta）
        mode = 'homing';
        if nargin >= 4 && ~isempty(start_pos)
            [success, cost] = homing_clear(source.L, channel, sim_client, config, ...
                                           start_pos, start_theta);
        else
            [success, cost] = homing_clear(source.L, channel, sim_client, config);
        end

        % ---- Q4 兜底：homing 断线 -> 转扫掠（与朝向无关，命题 Q4-B）----
        % 为什么必须兜底：定向源在逼近中滑出扇区，示向度就断（Q4 全解总览 ）。
        %  离线实测：seed=7 频道 3 正是这样丢的（R_MEC=142.91 m -> 走 homing，
        % homing 第 2 步 no_signal -> 未清除 -> 该局 92.3%）。扫掠只读 /clear 结果，不受朝向影响。
        if ~success && isfield(config, 'R_sweep_fallback_max') ...
                && isfield(source, 'L') && ~isempty(source.L) && size(source.L, 1) >= 3 ...
                && isfinite(R_MEC) && R_MEC <= config.R_sweep_fallback_max
            fprintf('    [清除] 频道 %d：homing 未成功 -> 转扫掠兜底（R_MEC=%.1f m）\n', ...
                channel, R_MEC);
            [ok2, cost2] = sweep_clear_L(source.L, R_MEC, c_star, channel, sim_client, config);
            cost = cost + cost2;
            if ok2
                success = true;
                mode = 'homing_fallback';
            end
        end
    end
end

%% 直接清除（R_MEC <= 20）
function [success, cost] = direct_clear(c_star, channel, sim_client, config)
    fprintf('    [清除] 直接清除 频道 %d @ (%.1f, %.1f)\n', channel, c_star(1), c_star(2));

    result = sim_client.clear(c_star(1), c_star(2), channel);
    success = strcmp(result.clear_result, 'success');

    if success
        cost = config.T_clear_success;
    else
        cost = config.T_clear_fail;
    end
end

%% 扫掠清除（20 < R_MEC <= R_star）-- 用 20 m 圆盘覆盖 L，逐点 /clear
%  完备性（命题 Q4-C）：G  in  L ⊆ ∪ᵢ B(cᵢ,20) -> 必有一次 /clear 成功。
%  覆盖中心集：三角格（间距 20sqrt(3) -> 外接半径 20）+ L 的顶点/边中点补强（：要盖住角）。
%  执行顺序按 NN+2-opt 就近（扫掠本身不改判定）。
function [success, cost] = sweep_clear_L(L, R_MEC, c_star, channel, sim_client, config)
    centers = sweep_centers(L, config.R_clear);
    N = size(centers, 1);

    % 理论上界（Q4-F33）：N ~= ⌈1.2091996·(R_MEC/20)^2⌉；超过硬上限说明 L 退化得离谱
    N_cap = max(60, 4 * ceil(design_constants.COVERAGE_DENSITY * (R_MEC / 20)^2));
    if N > N_cap
        fprintf('    [清除] 扫掠 频道 %d：中心集 %d 超过上限 %d（L 退化）-> 转 homing\n', ...
            channel, N, N_cap);
        success = false; cost = 0;
        return;
    end

    fprintf('    [清除] 扫掠清除 频道 %d, R_MEC=%.2f m, 覆盖中心 %d 个（L 顶点 %d）\n', ...
        channel, R_MEC, N, size(L, 1));

    pos0 = sim_client_last_pos(sim_client, c_star);
    order = optimize_route(centers, pos0);

    % 虚拟时间预算（可选）：超了就收手，别把整局吃光
    if isfield(config, 'sweep_budget_s'), budget = config.sweep_budget_s; else, budget = Inf; end
    vt0 = sim_client.virtual_time;

    total_cost = 0;
    for k = 1:numel(order)
        % 现实时间保护：剩余不足预留 -> 立刻收手，交给阶段 B/C 或下一局
        if sim_client.remaining_time < config.time_reserve
            fprintf('      [扫掠] 现实时间不足（剩 %.0f s）-> 中止扫掠\n', sim_client.remaining_time);
            success = false; cost = total_cost;
            return;
        end
        if sim_client.virtual_time - vt0 > budget
            fprintf('      [扫掠] 虚拟时间预算 %.0f s 用尽（第 %d/%d 次）-> 中止扫掠\n', ...
                budget, k, N);
            success = false; cost = total_cost;
            return;
        end

        q = centers(order(k), :);
        r = sim_client.clear(q(1), q(2), channel);
        if strcmp(r.clear_result, 'success')
            success = true;
            cost = total_cost + config.T_clear_success;
            fprintf('      [扫掠] 第 %d/%d 次命中 @ (%.1f, %.1f)\n', k, N, q(1), q(2));
            return;
        end
        total_cost = total_cost + config.T_clear_fail;
    end

    success = false;
    cost = total_cost;
end

%% 扫掠中心集移动到 `sweep_centers.m`（独立文件 -> 断言 7 能直接测生产同一份逻辑，
%  而不是在测试里重写一份；见 run_assertions 的断言 7·Q4）。

%% 旧扫掠：以 c* 为心的定向短走（仅在 L 退化时兜底）
%  在 c* 测一次拿示向度 -> 沿方位走一个清除半径再清 -> 重复。步数上限 ⌈R_MEC/R_clear⌉ + 3；
%  末段兜底用 c* 的 8 邻域。。
function [success, cost] = sweep_clear_directed(R_MEC, c_star, channel, sim_client, config)
    fprintf('    [清除] 扫掠（定向短走兜底） 频道 %d, R_MEC=%.2f m\n', channel, R_MEC);

    pos = c_star(:)';
    total_cost = 0;

    r = sim_client.clear(pos(1), pos(2), channel);
    total_cost = total_cost + config.T_clear_fail;
    if strcmp(r.clear_result, 'success')
        success = true; cost = config.T_clear_success; return;
    end

    step = config.R_clear;
    n_max = ceil(R_MEC / step) + 3;
    for k = 1:n_max
        m = sim_client.measure(pos(1), pos(2), channel);
        total_cost = total_cost + config.T_measure;

        if strcmp(m.measure_result, 'near')
            [success, cost_clear] = direct_clear(pos, channel, sim_client, config);
            cost = total_cost + cost_clear;
            return;
        end

        [ok, th] = svd_of(m);
        if ~ok, break; end

        pos = pos + step * [cosd(th), sind(th)];
        r = sim_client.clear(pos(1), pos(2), channel);
        total_cost = total_cost + config.T_clear_fail;
        if strcmp(r.clear_result, 'success')
            success = true; cost = total_cost + 2.0; return;
        end
    end

    offs = [step 0; -step 0; 0 step; 0 -step;
            step step; step -step; -step step; -step -step];
    for i = 1:size(offs, 1)
        q = c_star(:)' + offs(i, :);
        r = sim_client.clear(q(1), q(2), channel);
        total_cost = total_cost + config.T_clear_fail;
        if strcmp(r.clear_result, 'success')
            success = true; cost = total_cost + 2.0; return;
        end
    end

    success = false; cost = total_cost;
end

%% Homing 逼近（R_MEC > R_star）
%  只前进、不后退；步长上限 R_homing_step_max；方位翻转（= 过冲）时步长减半
%  （几何衰减 -> 必然收敛）；另有总移动与迭代双上限保时间预算。
%   Q4：定向源盲侧永不返回 near（附录2(9)）-> 末端判据必须是 /clear，
%     near 只作可选加速。本函数已满足（循环末尾直接 direct_clear）。
function [success, cost] = homing_clear(L, channel, sim_client, config, start_pos, start_theta)
    if ~isfield(config, 'R_homing_step_max'), config.R_homing_step_max = 300;  end
    if ~isfield(config, 'homing_max_iter'),   config.homing_max_iter   = 12;   end
    if ~isfield(config, 'homing_max_move'),   config.homing_max_move   = 2500; end

    fprintf('    [清除] Homing 逼近 频道 %d\n', channel);

    if nargin >= 5 && ~isempty(start_pos)
        pos = start_pos(:)';
        theta = start_theta;
        total_cost = 0;
        D = [];
    else
        if isempty(L)
            success = false; cost = 0; return;
        end
        pos = mean(L, 1);

        result = sim_client.measure(pos(1), pos(2), channel);
        total_cost = config.T_measure;

        if strcmp(result.measure_result, 'near')
            [success, cost] = direct_clear(pos, channel, sim_client, config);
            return;
        end

        [ok, theta] = svd_of(result);
        if ~ok
            fprintf('      [Homing] 起点 (%.1f, %.1f) 无示向度（%s），放弃本频道本轮\n', ...
                pos(1), pos(2), result.measure_result);
            success = false; cost = total_cost; return;
        end

        D = Q1_geometry.polygon_diameter(L);
    end

    if isempty(D)
        h = config.R_homing_step_max;
    else
        h = min(D / 2, config.R_homing_step_max);
    end
    h = max(h, config.R_clear);

    total_move = 0;
    for k = 1:config.homing_max_iter
        pos = pos + h * [cosd(theta), sind(theta)];
        total_move = total_move + h;

        result = sim_client.measure(pos(1), pos(2), channel);
        total_cost = total_cost + config.T_measure;

        if strcmp(result.measure_result, 'near')
            [success, cost_clear] = direct_clear(pos, channel, sim_client, config);
            cost = total_cost + cost_clear;
            fprintf('      [Homing] 第 %d 步抵达（累计移动 %.0f m）\n', k, total_move);
            return;
        end

        [ok, theta_new] = svd_of(result);
        if ~ok
            fprintf('      [Homing] 第 %d 步丢失信号（%s），停止逼近\n', k, result.measure_result);
            break;
        end

        if abs(angdiff(theta_new, theta)) > 90
            h = h / 2;      % 方位翻转 -> 过冲 -> 步长减半
        end
        theta = theta_new;

        if total_move >= config.homing_max_move
            fprintf('      [Homing] 累计移动达上限 %.0f m，停止逼近\n', config.homing_max_move);
            break;
        end

        if h < config.R_clear / 2
            % 步长已小于半个清除半径 -> 就地试清一次（此时距源通常已 <=20 m）
            % Q4：这里正是"末端用 /clear 而非等 near"的落点
            [success, cost_clear] = direct_clear(pos, channel, sim_client, config);
            cost = total_cost + cost_clear;
            return;
        end
    end

    fprintf('      [Homing] 未收敛（累计移动 %.0f m），本频道本轮未清除\n', total_move);
    success = false; cost = total_cost;
end

%% 取机器狗当前落点（供扫掠路由用；SimulatorClient 每次合法动作后维护 last_pos）
function p = sim_client_last_pos(sim_client, fallback)
    if isprop(sim_client, 'last_pos') && ~isempty(sim_client.last_pos)
        p = sim_client.last_pos(:)';
    else
        p = fallback(:)';
    end
end

%% 安全取示向度：只有 measure_result=="direction" 才读 svd_deg（附件2 ）
function [ok, deg] = svd_of(result)
    ok = isfield(result, 'measure_result') && strcmp(result.measure_result, 'direction') ...
         && isfield(result, 'svd_deg') && ~isempty(result.svd_deg);
    if ok
        deg = result.svd_deg;
    else
        deg = NaN;
    end
end

%% 角度差（处理环绕）
function d = angdiff(phi, theta)
    d = mod(phi - theta + 180, 360) - 180;
end
