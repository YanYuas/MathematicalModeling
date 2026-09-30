% ========================================================================
% clear_source —— 三路清除策略
%
% 按 R_MEC 选清除方式：R_MEC ≤ R_clear 直接清除；≤ R_star 扫掠；否则 homing 逼近。
% 可选 start_pos/start_theta 用于阶段 C：频道已有示向度时直接从该观测点 homing。
% 各路的具体构造与实测依据见《Q3 调优经验与补丁记录》P-3 / P-4。
% ========================================================================

function [success, cost, mode] = clear_source(source, sim_client, config, start_pos, start_theta)
    R_MEC = source.R_MEC;
    channel = source.channel;
    c_star = source.c_star;  % 最小包围圆圆心

    if R_MEC <= config.R_clear
        % 直接清除
        mode = 'direct';
        [success, cost] = direct_clear(c_star, channel, sim_client, config);

    elseif R_MEC <= config.R_star
        % 扫掠清除
        mode = 'sweep';
        [success, cost] = sweep_clear(source.L, R_MEC, c_star, channel, sim_client, config);

    else
        % Homing 逼近（阶段 C 会透传 start_pos/start_theta）
        mode = 'homing';
        if nargin >= 4 && ~isempty(start_pos)
            [success, cost] = homing_clear(source.L, channel, sim_client, config, ...
                                           start_pos, start_theta);
        else
            [success, cost] = homing_clear(source.L, channel, sim_client, config);
        end
    end
end

%% 直接清除（R_MEC ≤ 20）
function [success, cost] = direct_clear(c_star, channel, sim_client, config)
    fprintf('    [清除] 直接清除 频道 %d\n', channel);

    result = sim_client.clear(c_star(1), c_star(2), channel);
    success = strcmp(result.clear_result, 'success');

    if success
        cost = config.T_clear_success;
    else
        cost = config.T_clear_fail;
    end
end

%% 扫掠清除（20 < R_MEC ≤ R_star）
%  在 c* 测一次拿示向度 ⇒ 沿方位走一个清除半径再清 ⇒ 重复。
%  保证：方位误差 ≤1° 时距离 R 处横偏 ≈ 0.0175R，R ≤ 84 m ⇒ ≤1.5 m，每 20 m 采一点
%  ⇒ 最近采样点必落在清除半径内。步数上限 ⌈R_MEC/R_clear⌉ + 3。
%  兜底：某步测不到方位 ⇒ 退回以 c* 为中心的 8 邻域 20 m 格点逐个试
%  （不做包围盒大范围铺点）。详见《调优与补丁记录》P-3。
function [success, cost] = sweep_clear(L, R_MEC, c_star, channel, sim_client, config)
    fprintf('    [清除] 扫掠清除 频道 %d, R_MEC=%.2f m（定向短走）\n', channel, R_MEC);

    pos = c_star(:)';
    total_cost = 0;

    % 第 0 步：就地试一次（源可能就在 c* 的 20 m 内 —— 通常如此）
    r = sim_client.clear(pos(1), pos(2), channel);
    total_cost = total_cost + config.T_clear_fail;
    if strcmp(r.clear_result, 'success')
        success = true;
        cost = config.T_clear_success;
        return;
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
        if ~ok
            break;      % 测不到方位 ⇒ 走兜底
        end

        pos = pos + step * [cosd(th), sind(th)];
        r = sim_client.clear(pos(1), pos(2), channel);
        total_cost = total_cost + config.T_clear_fail;
        if strcmp(r.clear_result, 'success')
            success = true;
            cost = total_cost + 2.0;      % 补上清除动作那 2 s
            return;
        end
    end

    % ---- 兜底：以 c* 为中心的 8 邻域（20 m 格点）逐个试，不做包围盒大范围铺点 ----
    offs = [step 0; -step 0; 0 step; 0 -step;
            step step; step -step; -step step; -step -step];
    for i = 1:size(offs, 1)
        q = c_star(:)' + offs(i, :);
        r = sim_client.clear(q(1), q(2), channel);
        total_cost = total_cost + config.T_clear_fail;
        if strcmp(r.clear_result, 'success')
            success = true;
            cost = total_cost + 2.0;
            return;
        end
    end

    success = false;
    cost = total_cost;
end

%% Homing 逼近（R_MEC > R_star）
%  只前进、不后退；步长上限 R_homing_step_max；方位翻转（= 过冲）时步长减半
%  （几何衰减 ⇒ 必然收敛）；另有总移动与迭代双上限保时间预算。
%  原实现步长恒定且过冲后回退半步 ⇒ A→B→A 永久乒乓、原地不收敛，详见《调优与补丁记录》I-2。
function [success, cost] = homing_clear(L, channel, sim_client, config, start_pos, start_theta)
    % 防御性默认值：只带旧字段的 config 也能跑
    if ~isfield(config, 'R_homing_step_max'), config.R_homing_step_max = 300;  end
    if ~isfield(config, 'homing_max_iter'),   config.homing_max_iter   = 12;   end
    if ~isfield(config, 'homing_max_move'),   config.homing_max_move   = 2500; end

    fprintf('    [清除] Homing 逼近 频道 %d\n', channel);

    % 两种启动方式：
    %   (a) 由 L 启动 —— 起点取 L 的形心，先检测一次拿方位；
    %   (b) 单方位启动（start_pos + start_theta）—— 阶段 C 用：频道有示向度但没交会出区域。
    if nargin >= 5 && ~isempty(start_pos)
        pos = start_pos(:)';
        theta = start_theta;
        total_cost = 0;
        D = [];
    else
        % 初始位置（L的中心）
        pos = mean(L, 1);

        % 初始检测
        result = sim_client.measure(pos(1), pos(2), channel);
        total_cost = config.T_measure;

        if strcmp(result.measure_result, 'near')
            [success, cost] = direct_clear(pos, channel, sim_client, config);
            return;
        end

        % svd_deg 只在 measure_result="direction" 时存在（附件2 §7.2/§12）
        [ok, theta] = svd_of(result);
        if ~ok
            fprintf('      [Homing] 起点 (%.1f, %.1f) 无示向度（%s），放弃本频道本轮\n', ...
                pos(1), pos(2), result.measure_result);
            success = false;
            cost = total_cost;
            return;
        end

        D = Q1_geometry.polygon_diameter(L);
    end

    % 初始步长：取"定位不确定度半径"与上限的较小者（旧版无上限 ⇒ 必然过冲）
    if isempty(D)
        h = config.R_homing_step_max;      % 单方位启动：无 L ⇒ 直接用步长上限
    else
        h = min(D / 2, config.R_homing_step_max);
    end
    h = max(h, config.R_clear);          % 至少一个清除半径

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
            % 方位翻转 ⇒ 这一步**过冲了** ⇒ 步长减半（下一轮朝回指的方位走更小一步）
            h = h / 2;
        end
        theta = theta_new;

        if total_move >= config.homing_max_move
            fprintf('      [Homing] 累计移动达上限 %.0f m，停止逼近\n', config.homing_max_move);
            break;
        end

        if h < config.R_clear / 2
            % 步长已小于半个清除半径 ⇒ 就地试清一次（此时距源通常已 ≤20 m）
            [success, cost_clear] = direct_clear(pos, channel, sim_client, config);
            cost = total_cost + cost_clear;
            return;
        end
    end

    fprintf('      [Homing] 未收敛（累计移动 %.0f m），本频道本轮未清除\n', total_move);
    success = false;
    cost = total_cost;
end

%% 安全取示向度：只有 measure_result=="direction" 才读 svd_deg（附件2 §7.2）
function [ok, deg] = svd_of(result)
    ok = isfield(result, 'measure_result') && strcmp(result.measure_result, 'direction') ...
         && isfield(result, 'svd_deg') && ~isempty(result.svd_deg);
    if ok
        deg = result.svd_deg;
    else
        deg = NaN;
    end
end

%% 辅助函数：角度差（处理环绕）
function diff = angdiff(phi, theta)
    diff = mod(phi - theta + 180, 360) - 180;
end
