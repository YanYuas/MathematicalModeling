% ========================================================================
% sweep_clear_exact -- 扫掠清除（早期按包围盒铺点的版本，已被取代）
% 现行扫掠是 clear_source.m 里的局部函数（定向短走），主流程不调用本函数。
% 保留备查：早期版本按 L 的包围盒铺 20 m 格点、按"距 c* 升序"逐个试，
% 实测平均浪费 10~19 个探点。
% ========================================================================

function [success, cost, N_sweep] = sweep_clear_exact(L, channel, sim_client, config)
    % 输入: L - 定位区域顶点 (N×2)；channel；sim_client；config
    % 输出: success / cost [s] / N_sweep

    if isempty(L)
        success = false;
        cost = 0;
        N_sweep = 0;
        return;
    end

    % 计算定位区域的边界框
    x_min = min(L(:,1));
    x_max = max(L(:,1));
    y_min = min(L(:,2));
    y_max = max(L(:,2));

    % 计算 MEC
    [c_star, R_MEC] = Q1_geometry.minimum_enclosing_circle(L);

    % 理论扫掠次数
    N_theory = ceil(design_constants.COVERAGE_DENSITY * (R_MEC / 20)^2);

    % 三角格间距（保证覆盖半径 R_clear = 20m）
    d_sweep = 20 * sqrt(3);  % 34.64 m

    % 生成三角格覆盖点
    a1 = [d_sweep, 0];
    a2 = [d_sweep/2, sqrt(3)*d_sweep/2];

    % 网格范围
    n_max = ceil((max(x_max, y_max) - min(x_min, y_min)) / d_sweep) + 2;

    % 生成候选点
    sweep_points = [];
    for i = -n_max:n_max
        for j = -n_max:n_max
            p = [x_min, y_min] + i * a1 + j * a2;

            % 判断点是否在定位区域 L 内或边界附近
            dist_to_L = inf;
            for k = 1:size(L, 1)
                dist_to_L = min(dist_to_L, norm(p - L(k, :)));
            end

            if dist_to_L <= 20  % 在 L 内或边界 20m 范围
                sweep_points = [sweep_points; p];
            end
        end
    end

    % 去重
    if size(sweep_points, 1) > 1
        sweep_points = unique(round(sweep_points, 2), 'rows');
    end

    N_sweep = size(sweep_points, 1);

    fprintf('  [扫掠精确版] R_MEC=%.2f, N理论=%d, N实际=%d\n', R_MEC, N_theory, N_sweep);

    % 执行扫掠清除
    total_cost = 0;
    success = false;

    for i = 1:N_sweep
        p = sweep_points(i, :);

        try
            resp = sim_client.clear(p(1), p(2), channel);

            if strcmp(resp.clear_result, 'success')
                success = true;
                total_cost = total_cost + config.T_clear_success;
                fprintf('    清除成功 at (%.2f, %.2f)\n', p(1), p(2));
                break;
            else
                total_cost = total_cost + config.T_clear_fail;
            end
        catch ME
            fprintf('    清除失败: %s\n', ME.message);
            total_cost = total_cost + config.T_clear_fail;
        end
    end

    cost = total_cost;
end
