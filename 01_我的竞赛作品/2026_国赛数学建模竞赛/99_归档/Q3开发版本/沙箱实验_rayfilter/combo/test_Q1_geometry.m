% ========================================================================
% test_Q1_geometry.m - Q1 几何模块验证脚本
% ========================================================================
% 功能: 验证 Q1 几何三件套的正确性
% 验收标准: Q1 基准算例
% ========================================================================

function test_Q1_geometry()
    fprintf('\n');
    fprintf('========================================================================\n');
    fprintf('  Q1 几何模块验证\n');
    fprintf('========================================================================\n');
    fprintf('\n');

    %% Q1 基准算例（建模手修正版）
    % S1 = (0, 0), θ1 = 59.036°, ε = 1°
    % S2 = (600, 0), θ2 = 120.964°, ε = 1°
    % 期望: D = 39.5978 m, R_MEC = 19.7989 m

    fprintf('[基准算例] S1=(0,0), θ1=59.036°, S2=(600,0), θ2=120.964°\n\n');

    % 构造角域
    wedge1 = struct('station', [0, 0], 'theta_deg', 59.036, 'epsilon_deg', 1);
    wedge2 = struct('station', [600, 0], 'theta_deg', 120.964, 'epsilon_deg', 1);
    wedges = [wedge1; wedge2];

    %% 测试 1: 半平面交
    fprintf('[测试 1] 半平面交算法...\n');
    tic;
    L = Q1_geometry.intersect_wedges(wedges);
    t1 = toc;

    fprintf('  定位区域 L: %d 个顶点\n', size(L, 1));
    fprintf('  耗时: %.3f s\n', t1);

    if isempty(L)
        error('❌ 半平面交失败: 返回空集');
    end

    % 可视化
    figure('Name', 'Q1 基准算例 - 定位区域');
    plot(L(:,1), L(:,2), 'b-o', 'LineWidth', 2, 'MarkerSize', 8);
    hold on;
    plot(0, 0, 'rs', 'MarkerSize', 12, 'LineWidth', 2);
    plot(600, 0, 'rs', 'MarkerSize', 12, 'LineWidth', 2);
    axis equal;
    grid on;
    xlabel('x (m)');
    ylabel('y (m)');
    title('定位区域 L (角域交集)');
    legend('定位区域 L', '检测点', 'Location', 'best');

    fprintf('  ✓ 半平面交通过\n\n');

    %% 测试 2: 凸多边形直径
    fprintf('[测试 2] 凸多边形直径...\n');
    tic;
    [D, p1, p2] = Q1_geometry.polygon_diameter(L);
    t2 = toc;

    fprintf('  直径 D = %.6f m\n', D);
    fprintf('  端点 p1 = (%.6f, %.6f)\n', p1(1), p1(2));
    fprintf('  端点 p2 = (%.6f, %.6f)\n', p2(1), p2(2));
    fprintf('  耗时: %.3f s\n', t2);

    D_expected = 39.5978;
    error_D = abs(D - D_expected);
    fprintf('  误差: %.6f m (%.3f%%)\n', error_D, error_D/D_expected*100);

    if error_D < 0.01
        fprintf('  ✓ 直径验证通过\n\n');
    else
        error('❌ 直径不匹配: 期望 %.6f, 实际 %.6f', D_expected, D);
    end

    % 可视化直径
    hold on;
    plot([p1(1), p2(1)], [p1(2), p2(2)], 'r--', 'LineWidth', 2);
    legend('定位区域 L', '检测点', '直径', 'Location', 'best');

    %% 测试 3: 最小包围圆
    fprintf('[测试 3] 最小包围圆 (Welzl 算法)...\n');
    tic;
    [c_star, R_MEC] = Q1_geometry.minimum_enclosing_circle(L);
    t3 = toc;

    fprintf('  圆心 c* = (%.6f, %.6f)\n', c_star(1), c_star(2));
    fprintf('  半径 R_MEC = %.6f m\n', R_MEC);
    fprintf('  耗时: %.3f s\n', t3);

    R_expected = 19.7989;
    error_R = abs(R_MEC - R_expected);
    fprintf('  误差: %.6f m (%.3f%%)\n', error_R, error_R/R_expected*100);

    if error_R < 0.01
        fprintf('  ✓ 最小包围圆验证通过\n\n');
    else
        error('❌ R_MEC 不匹配: 期望 %.6f, 实际 %.6f', R_expected, R_MEC);
    end

    % 可视化包围圆
    theta = linspace(0, 2*pi, 100);
    x_circle = c_star(1) + R_MEC * cos(theta);
    y_circle = c_star(2) + R_MEC * sin(theta);
    plot(x_circle, y_circle, 'g-', 'LineWidth', 2);
    plot(c_star(1), c_star(2), 'go', 'MarkerSize', 10, 'LineWidth', 2);
    legend('定位区域 L', '检测点', '直径', '最小包围圆', '圆心', 'Location', 'best');

    %% 测试 4: Jung 定理验证
    fprintf('[测试 4] Jung 定理验证...\n');
    gamma = R_MEC / (D / 2);
    fprintf('  γ = R_MEC / (D/2) = %.6f\n', gamma);

    gamma_upper = 2 / sqrt(3);  % Jung 定理上界：γ = R_MEC/(D/2) ≤ 2/√3（1/√3 是 R_MEC/D 的上界）
    fprintf('  Jung 上界 = 2/√3 = %.6f\n', gamma_upper);

    if gamma <= gamma_upper + 1e-6
        fprintf('  ✓ 满足 Jung 定理\n\n');
    else
        warning('⚠ γ 超过 Jung 上界');
    end

    %% 总结
    fprintf('========================================================================\n');
    fprintf('  验证结果\n');
    fprintf('========================================================================\n');
    fprintf('直径 D:          %.6f m (期望 %.6f m, 误差 %.3f%%)\n', D, D_expected, error_D/D_expected*100);
    fprintf('最小包围圆 R:    %.6f m (期望 %.6f m, 误差 %.3f%%)\n', R_MEC, R_expected, error_R/R_expected*100);
    fprintf('Jung 系数 γ:     %.6f (上界 %.6f)\n', gamma, gamma_upper);
    fprintf('总耗时:          %.3f s\n', t1 + t2 + t3);
    fprintf('========================================================================\n');
    fprintf('\n');

    if error_D < 0.01 && error_R < 0.01
        fprintf('✅ Q1 几何模块验证通过！\n\n');
    else
        error('❌ Q1 几何模块验证失败');
    end
end
