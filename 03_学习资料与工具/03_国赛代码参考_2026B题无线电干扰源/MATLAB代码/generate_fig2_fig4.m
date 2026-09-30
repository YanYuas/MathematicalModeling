% Q1 图2和图4生成 - 基于基准算例数值
% 直接使用已知的计算结果，避免依赖Python

clear; clc; close all;

% ============================================================================
% 配色方案
% ============================================================================
colors = struct();
colors.ink = [28, 28, 28] / 255;
colors.slate = [91, 107, 115] / 255;
colors.paper = [247, 244, 238] / 255;
colors.field = [197, 212, 224] / 255;
colors.geometry = [44, 74, 110] / 255;
colors.ochre = [196, 123, 43] / 255;
colors.rust = [140, 58, 42] / 255;
colors.sage = [79, 111, 92] / 255;

set(0, 'DefaultAxesFontName', 'Microsoft YaHei');
set(0, 'DefaultTextFontName', 'Microsoft YaHei');

output_dir = fullfile(pwd, '..', '实验结果', 'figs');

fprintf('正在生成图2和图4...\n\n');

% ============================================================================
% 图2：Q1_MAIN_02_交会定位区域构造.png
% ============================================================================
fprintf('正在生成图2：两站交会定位区域构造...\n');

% 基准算例数据
S1 = [0, 0];
S2 = [600, 0];
G = [300, 500];

% 定位区域顶点（从文档已知）
vertices = [
    299.127, 499.237;
    299.128, 501.763;
    300.873, 501.763;
    300.872, 499.237
];

% 直径和最小包围圆数据
D = 39.598;
p_d = [299.127, 499.237];
q_d = [300.873, 501.763];
center_mec = [300.000, 500.500];
R_mec = 19.799;

fig2 = figure('Position', [100, 100, 1000, 800], 'Color', colors.paper);
ax2 = axes('Parent', fig2, 'Color', colors.paper);
hold(ax2, 'on');

% 绘制定位区域
vertices_closed = [vertices; vertices(1,:)];
patch(vertices(:,1), vertices(:,2), colors.field, ...
      'FaceAlpha', 0.35, 'EdgeColor', 'none', 'Parent', ax2);
plot(ax2, vertices_closed(:,1), vertices_closed(:,2), '-', ...
     'Color', colors.geometry, 'LineWidth', 2.5);

% 标注顶点
for i = 1:size(vertices, 1)
    plot(ax2, vertices(i,1), vertices(i,2), 'o', ...
         'Color', colors.geometry, 'MarkerSize', 8, ...
         'MarkerFaceColor', colors.geometry);
    text(vertices(i,1)+0.05, vertices(i,2)+0.15, ...
         sprintf('V%d\n(%.1f,%.1f)', i, vertices(i,1), vertices(i,2)), ...
         'FontSize', 9, 'Color', colors.ink, 'Parent', ax2);
end

% 绘制直径
plot(ax2, [p_d(1), q_d(1)], [p_d(2), q_d(2)], '-', ...
     'Color', colors.ochre, 'LineWidth', 3, 'DisplayName', ...
     sprintf('直径 D=%.1f m', D));
plot(ax2, [p_d(1), q_d(1)], [p_d(2), q_d(2)], 'o', ...
     'Color', colors.ochre, 'MarkerSize', 8, 'MarkerFaceColor', colors.ochre);

% 绘制最小包围圆
theta = linspace(0, 2*pi, 100);
x_circle = center_mec(1) + R_mec * cos(theta);
y_circle = center_mec(2) + R_mec * sin(theta);
plot(ax2, x_circle, y_circle, '--', 'Color', colors.sage, ...
     'LineWidth', 1.5, 'DisplayName', sprintf('最小包围圆 R=%.1f m', R_mec));
plot(ax2, center_mec(1), center_mec(2), '+', 'Color', colors.sage, ...
     'MarkerSize', 12, 'LineWidth', 2);

% 绘制检测站（虽然不在视图范围内，但标注方向）
text(299.2, 499.0, '← S_1方向', 'FontSize', 9, 'Color', colors.geometry, ...
     'FontAngle', 'italic', 'Parent', ax2);
text(300.7, 499.0, 'S_2方向 →', 'FontSize', 9, 'Color', colors.geometry, ...
     'FontAngle', 'italic', 'Parent', ax2);

% 绘制真源
plot(ax2, G(1), G(2), '*', 'Color', colors.rust, ...
     'MarkerSize', 15, 'DisplayName', '真源');
text(G(1)+0.15, G(2)+0.25, '真源 G', 'FontSize', 11, ...
     'Color', colors.rust, 'FontWeight', 'bold', 'Parent', ax2);

% 标注
text(299.5, 500.5, {'定位区域 L', sprintf('(%.2f×%.2f m²)', ...
     max(vertices(:,1))-min(vertices(:,1)), ...
     max(vertices(:,2))-min(vertices(:,2)))}, ...
     'FontSize', 10, 'HorizontalAlignment', 'center', ...
     'Color', colors.geometry, 'FontWeight', 'bold', ...
     'BackgroundColor', 'white', 'EdgeColor', colors.geometry, ...
     'Margin', 4, 'Parent', ax2);

xlim(ax2, [298.9, 301.1]);
ylim(ax2, [498.9, 502.1]);
axis(ax2, 'equal');
xlabel(ax2, 'X坐标 (m)', 'FontSize', 12, 'FontWeight', 'bold');
ylabel(ax2, 'Y坐标 (m)', 'FontSize', 12, 'FontWeight', 'bold');
title(ax2, '两站交会定位区域构造', 'FontSize', 14, 'FontWeight', 'bold');
legend(ax2, 'Location', 'northwest', 'FontSize', 10);
grid(ax2, 'on');
set(ax2, 'GridAlpha', 0.2, 'GridLineStyle', ':');
box(ax2, 'on');

output_path2 = fullfile(output_dir, 'Q1_MAIN_02_交会定位区域构造.png');
print(fig2, output_path2, '-dpng', '-r300');
fprintf('✓ 已保存: %s\n\n', output_path2);
close(fig2);

% ============================================================================
% 图4：Q1_MAIN_04_Jung夹逼图.png
% ============================================================================
fprintf('正在生成图4：Jung夹逼图...\n');

R_lower = D / 2;
R_upper = D / sqrt(3);
gamma = R_mec / R_lower;

fig4 = figure('Position', [100, 100, 1400, 700], 'Color', colors.paper);

% 左图：主视图
ax_main = subplot(1, 2, 1, 'Parent', fig4);
set(ax_main, 'Color', colors.paper);
hold(ax_main, 'on');

% 绘制定位区域
patch(vertices(:,1), vertices(:,2), colors.field, ...
      'FaceAlpha', 0.25, 'EdgeColor', 'none', 'Parent', ax_main);
plot(ax_main, vertices_closed(:,1), vertices_closed(:,2), '-', ...
     'Color', colors.geometry, 'LineWidth', 2.5);

% 三层圆
% 下界圆
theta = linspace(0, 2*pi, 100);
x_lower = center_mec(1) + R_lower * cos(theta);
y_lower = center_mec(2) + R_lower * sin(theta);
plot(ax_main, x_lower, y_lower, '-', 'Color', colors.sage, ...
     'LineWidth', 2, 'DisplayName', sprintf('下界 D/2=%.2f m', R_lower));

% 实际MEC
x_mec = center_mec(1) + R_mec * cos(theta);
y_mec = center_mec(2) + R_mec * sin(theta);
plot(ax_main, x_mec, y_mec, '-', 'Color', colors.ochre, ...
     'LineWidth', 3, 'DisplayName', sprintf('实际 R_{MEC}=%.2f m', R_mec));

% 上界圆
x_upper = center_mec(1) + R_upper * cos(theta);
y_upper = center_mec(2) + R_upper * sin(theta);
plot(ax_main, x_upper, y_upper, '--', 'Color', colors.slate, ...
     'LineWidth', 1.5, 'DisplayName', sprintf('上界 D/√3=%.2f m', R_upper));

% 圆心
plot(ax_main, center_mec(1), center_mec(2), '+', ...
     'Color', colors.ink, 'MarkerSize', 14, 'LineWidth', 2.5);

% 直径
plot(ax_main, [p_d(1), q_d(1)], [p_d(2), q_d(2)], ':', ...
     'Color', colors.ochre, 'LineWidth', 1.5);
text((p_d(1)+q_d(1))/2, (p_d(2)+q_d(2))/2 - 0.5, ...
     sprintf('D=%.2f m', D), 'FontSize', 10, ...
     'HorizontalAlignment', 'center', 'Color', colors.ochre, ...
     'FontWeight', 'bold', 'Parent', ax_main);

xlim(ax_main, [center_mec(1)-R_upper*1.3, center_mec(1)+R_upper*1.3]);
ylim(ax_main, [center_mec(2)-R_upper*1.3, center_mec(2)+R_upper*1.3]);
axis(ax_main, 'equal');
xlabel(ax_main, 'X坐标 (m)', 'FontSize', 12, 'FontWeight', 'bold');
ylabel(ax_main, 'Y坐标 (m)', 'FontSize', 12, 'FontWeight', 'bold');
title(ax_main, 'Jung夹逼关系示意', 'FontSize', 14, 'FontWeight', 'bold');
legend(ax_main, 'Location', 'northwest', 'FontSize', 10);
grid(ax_main, 'on');
set(ax_main, 'GridAlpha', 0.2, 'GridLineStyle', ':');
box(ax_main, 'on');

% 右图：半径尺度
ax_scale = subplot(1, 2, 2, 'Parent', fig4);
set(ax_scale, 'Color', colors.paper);
hold(ax_scale, 'on');

xlim(ax_scale, [0, 1]);
ylim(ax_scale, [R_lower*0.95, R_upper*1.05]);

% 三个刻度线
y_vals = [R_lower, R_mec, R_upper];
labels_math = {'D/2', 'R_{MEC}', 'D/√3'};
line_colors = {colors.sage, colors.ochre, colors.slate};

for i = 1:length(y_vals)
    y = y_vals(i);
    color = line_colors{i};

    % 横线
    plot(ax_scale, [0, 1], [y, y], '-', 'Color', color, ...
         'LineWidth', 3);

    % 数值标注
    text(0.5, y, sprintf('%.2f m', y), 'FontSize', 11, ...
         'HorizontalAlignment', 'center', 'VerticalAlignment', 'bottom', ...
         'Color', color, 'FontWeight', 'bold', ...
         'BackgroundColor', 'white', 'EdgeColor', color, ...
         'Margin', 3, 'Parent', ax_scale);

    % 公式标注
    text(0.1, y, labels_math{i}, 'FontSize', 12, ...
         'HorizontalAlignment', 'left', 'VerticalAlignment', 'middle', ...
         'Color', color, 'FontWeight', 'bold', 'Interpreter', 'tex', ...
         'Parent', ax_scale);
end

% γ标注
mid_y = (R_lower + R_mec) / 2;
text(0.5, mid_y, sprintf('γ = %.4f\n下界取等！', gamma), ...
     'FontSize', 10, 'HorizontalAlignment', 'center', ...
     'FontAngle', 'italic', 'Color', colors.sage, ...
     'FontWeight', 'bold', 'BackgroundColor', [colors.sage, 0.15], ...
     'EdgeColor', colors.sage, 'LineWidth', 1.5, ...
     'Margin', 4, 'Parent', ax_scale);

% Jung区间双箭头
annotation(fig4, 'doublearrow', [0.80, 0.80], ...
           [(R_lower-R_lower*0.95)/(R_upper*1.05-R_lower*0.95), ...
            (R_upper-R_lower*0.95)/(R_upper*1.05-R_lower*0.95)], ...
           'Color', colors.ink, 'LineWidth', 2, 'HeadStyle', 'plain');
text(0.92, (R_lower+R_upper)/2, 'Jung区间', 'FontSize', 10, ...
     'Rotation', 90, 'HorizontalAlignment', 'center', ...
     'Color', colors.ink, 'FontWeight', 'bold', 'Parent', ax_scale);

axis(ax_scale, 'off');
title(ax_scale, '半径尺度', 'FontSize', 13, 'FontWeight', 'bold');

output_path4 = fullfile(output_dir, 'Q1_MAIN_04_Jung夹逼图.png');
print(fig4, output_path4, '-dpng', '-r300');
fprintf('✓ 已保存: %s\n\n', output_path4);
close(fig4);

fprintf('======================================================================\n');
fprintf('✅ 所有4张P0图表生成完成！\n');
fprintf('输出目录：%s\n', output_dir);
fprintf('======================================================================\n');
