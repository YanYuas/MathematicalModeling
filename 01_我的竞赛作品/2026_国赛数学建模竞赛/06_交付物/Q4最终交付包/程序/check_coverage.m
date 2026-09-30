% ========================================================================
% check_coverage -- 覆盖自检（验收线 ①）
% 采样验证检测点集 P 是否以 R_sensor 为半径覆盖 D(0, R_domain)。
% 采样：域内 50 m 网格 + 边界环带 1750~1800 m 加密至 10 m（边界最易漏）。
% ========================================================================

function [coverage_ok, max_dist] = check_coverage(P, config)
    R_domain = config.R_domain;
    R_sensor = config.R_sensor;

    fprintf('[覆盖自检] 采样验证中...\n');

    % 网格采样（步长 50 m）
    step = 50;
    [X, Y] = meshgrid(-R_domain:step:R_domain, -R_domain:step:R_domain);
    sample_points = [X(:), Y(:)];

    % 保留圆域内的点
    r = sqrt(sum(sample_points.^2, 2));
    sample_points = sample_points(r <= R_domain, :);

    % 边界环带加密（1750~1800 m，步长 10 m）
    theta = linspace(0, 2*pi, 360);
    for r_val = 1750:10:1800
        boundary_pts = r_val * [cos(theta)', sin(theta)'];
        sample_points = [sample_points; boundary_pts];
    end

    fprintf('[覆盖自检] 采样点总数: %d\n', size(sample_points, 1));

    % 检查每个采样点到最近检测点的距离
    max_dist = 0;
    failed_count = 0;

    for i = 1:size(sample_points, 1)
        sp = sample_points(i, :);

        % 计算到所有检测点的距离
        distances = sqrt(sum((P - sp).^2, 2));
        min_dist = min(distances);
        max_dist = max(max_dist, min_dist);

        if min_dist > R_sensor + 1e-9
            failed_count = failed_count + 1;
            if failed_count <= 5  % 只打印前5个
                fprintf('  [失败] 位置 (%.2f, %.2f), 距离 %.2f m\n', ...
                    sp(1), sp(2), min_dist);
            end
        end
    end

    coverage_ok = (failed_count == 0);

    if coverage_ok
        fprintf('[覆盖自检]  通过，最大距离 %.4f m <= %.1f m\n', max_dist, R_sensor);
    else
        fprintf('[覆盖自检]  失败，%d 个点超出覆盖\n', failed_count);
    end
end
