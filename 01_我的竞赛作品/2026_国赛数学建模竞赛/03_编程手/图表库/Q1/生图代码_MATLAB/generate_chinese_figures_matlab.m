% Q1 中文图表生成脚本 - 使用MATLAB
% 基于交接文档要求生成4张P0优先级图表
% 配色：Ink & Ochre方案
% 分辨率：300 DPI

clear; clc; close all;

% ============================================================================
% Ink & Ochre 配色方案
% ============================================================================
colors = struct();
colors.ink = [28, 28, 28] / 255;           % #1C1C1C 深墨色
colors.slate = [91, 107, 115] / 255;       % #5B6B73 板岩灰
colors.paper = [247, 244, 238] / 255;      % #F7F4EE 纸质底色
colors.field = [197, 212, 224] / 255;      % #C5D4E0 云灰
colors.geometry = [44, 74, 110] / 255;     % #2C4A6E 几何蓝
colors.ochre = [196, 123, 43] / 255;       % #C47B2B 赭石色
colors.rust = [140, 58, 42] / 255;         % #8C3A2A 锈红色
colors.sage = [79, 111, 92] / 255;         % #4F6F5C 鼠尾草绿

% 中文字体设置
set(0, 'DefaultAxesFontName', 'Microsoft YaHei');
set(0, 'DefaultTextFontName', 'Microsoft YaHei');
set(0, 'DefaultAxesFontSize', 10);

% 输出目录
output_dir = fullfile(pwd, '..', '实验结果', 'figs');
if ~exist(output_dir, 'dir')
    mkdir(output_dir);
end

fprintf('======================================================================\n');
fprintf('Q1 中文图表生成工具 (MATLAB版)\n');
fprintf('配色：Ink & Ochre | 分辨率：300 DPI | 字体：Microsoft YaHei\n');
fprintf('======================================================================\n\n');

% ============================================================================
% 图1：Q1_MAIN_01_角域示意.png（单站楔形）
% ============================================================================
fprintf('正在生成图1：单站角域示意...\n');

fig1 = figure('Position', [100, 100, 700, 700], 'Color', colors.paper);
ax1 = axes('Parent', fig1, 'Color', colors.paper);
hold(ax1, 'on');

% 检测站位置
S1 = [0, 0];
theta1 = 45;  % 中心方向
eps_angle = 15;  % 夸张的角度便于展示

% 绘制楔形区域（使用patch）
theta_range = linspace(theta1-eps_angle, theta1+eps_angle, 50);
r_max = 250;
x_wedge = [S1(1), r_max*cosd(theta_range), S1(1)];
y_wedge = [S1(2), r_max*sind(theta_range), S1(2)];
patch(x_wedge, y_wedge, colors.field, 'EdgeColor', 'none', ...
      'FaceAlpha', 0.15, 'Parent', ax1);

% 绘制边界射线
for angle = [theta1-eps_angle, theta1+eps_angle]
    x_end = S1(1) + r_max * cosd(angle);
    y_end = S1(2) + r_max * sind(angle);
    plot(ax1, [S1(1), x_end], [S1(2), y_end], '--', ...
         'Color', colors.geometry, 'LineWidth', 1.5);
end

% 绘制中心射线
x_center = S1(1) + r_max * cosd(theta1);
y_center = S1(2) + r_max * sind(theta1);
plot(ax1, [S1(1), x_center], [S1(2), y_center], '-', ...
     'Color', colors.ochre, 'LineWidth', 2.5);

% 标注检测站
plot(ax1, S1(1), S1(2), 'o', 'Color', colors.rust, ...
     'MarkerSize', 12, 'MarkerFaceColor', colors.rust);
text(S1(1)-20, S1(2)-30, '检测站 S_1', 'FontSize', 12, ...
     'FontWeight', 'bold', 'Color', colors.ink, 'Parent', ax1);

% 标注角度弧线
theta_arc = linspace(theta1-eps_angle, theta1+eps_angle, 30);
r_arc = 80;
x_arc = S1(1) + r_arc * cosd(theta_arc);
y_arc = S1(2) + r_arc * sind(theta_arc);
plot(ax1, x_arc, y_arc, '-', 'Color', colors.ochre, 'LineWidth', 2);
text(50, 40, '2\epsilon = 2°', 'FontSize', 11, 'Color', colors.ochre, 'Parent', ax1);

% 标注不确定性
text(150, 180, {'大不确定性', '（单站无法定位）'}, ...
     'FontSize', 11, 'HorizontalAlignment', 'center', ...
     'FontAngle', 'italic', 'Color', colors.slate, ...
     'BackgroundColor', 'white', 'EdgeColor', colors.slate, ...
     'Margin', 5, 'Parent', ax1);

% 标注射线
text(180, 220, '\theta + \epsilon', 'FontSize', 10, ...
     'Color', colors.geometry, 'Parent', ax1);
text(180, 120, '\theta - \epsilon', 'FontSize', 10, ...
     'Color', colors.geometry, 'Parent', ax1);

% 设置坐标轴
xlim(ax1, [-50, 300]);
ylim(ax1, [-50, 300]);
axis(ax1, 'equal');
xlabel(ax1, 'X坐标 (m)', 'FontSize', 12, 'FontWeight', 'bold');
ylabel(ax1, 'Y坐标 (m)', 'FontSize', 12, 'FontWeight', 'bold');
title(ax1, '单站角域示意图', 'FontSize', 14, 'FontWeight', 'bold');
grid(ax1, 'on');
set(ax1, 'GridAlpha', 0.2, 'GridLineStyle', ':');
box(ax1, 'on');

% 保存
output_path1 = fullfile(output_dir, 'Q1_MAIN_01_角域示意.png');
print(fig1, output_path1, '-dpng', '-r300');
fprintf('✓ 已保存: %s\n\n', output_path1);
close(fig1);

% ============================================================================
% 图3：Q1_MAIN_03_等边三角形反例.png（Jung反例）
% ============================================================================
fprintf('正在生成图3：等边三角形反例...\n');

fig3 = figure('Position', [100, 100, 900, 800], 'Color', colors.paper);
ax3 = axes('Parent', fig3, 'Color', colors.paper);
hold(ax3, 'on');

% 等边三角形（边长a=100）
a = 100;
A = [0, 0];
B = [a, 0];
C = [a/2, a*sqrt(3)/2];

% 绘制三角形
triangle = [A; B; C; A];
plot(ax3, triangle(:,1), triangle(:,2), '-', ...
     'Color', colors.geometry, 'LineWidth', 2.5);
patch(triangle(1:3,1), triangle(1:3,2), colors.field, ...
      'EdgeColor', 'none', 'FaceAlpha', 0.15, 'Parent', ax3);

% 标注顶点
vertices = {A, 'A', -8, -12; B, 'B', 8, -12; C, 'C', 0, 8};
for i = 1:size(vertices, 1)
    pt = vertices{i,1};
    lbl = vertices{i,2};
    offset_x = vertices{i,3};
    offset_y = vertices{i,4};
    plot(ax3, pt(1), pt(2), 'o', 'Color', colors.ink, ...
         'MarkerSize', 10, 'MarkerFaceColor', colors.ink);
    text(pt(1)+offset_x, pt(2)+offset_y, lbl, 'FontSize', 14, ...
         'FontWeight', 'bold', 'Color', colors.ink, 'Parent', ax3);
end

% 直径AB和直径圆（失败）
D = a;
center_D = (A + B) / 2;
R_D = D / 2;

theta_circle = linspace(0, 2*pi, 100);
x_circle_D = center_D(1) + R_D * cos(theta_circle);
y_circle_D = center_D(2) + R_D * sin(theta_circle);
plot(ax3, x_circle_D, y_circle_D, '--', 'Color', colors.rust, ...
     'LineWidth', 1.5, 'DisplayName', sprintf('直径圆 (R=D/2=%.1f) 无法覆盖', R_D));

% 标注直径
plot(ax3, [A(1), B(1)], [A(2), B(2)], '-', ...
     'Color', colors.ochre, 'LineWidth', 2.5);
text(a/2, -5, sprintf('直径 D=%.1f', D), 'FontSize', 11, ...
     'HorizontalAlignment', 'center', 'Color', colors.ochre, ...
     'FontWeight', 'bold', 'Parent', ax3);

% 外接圆（成功）
R_circum = D / sqrt(3);
center_circum = (A + B + C) / 3 + [0, a/(2*sqrt(3))];

x_circle_circum = center_circum(1) + R_circum * cos(theta_circle);
y_circle_circum = center_circum(2) + R_circum * sin(theta_circle);
plot(ax3, x_circle_circum, y_circle_circum, '-', 'Color', colors.sage, ...
     'LineWidth', 2, 'DisplayName', sprintf('外接圆 (R=D/√3=%.1f) 覆盖', R_circum));
plot(ax3, center_circum(1), center_circum(2), '+', 'Color', colors.sage, ...
     'MarkerSize', 12, 'LineWidth', 2);

% Thales轨迹（90°轨迹，上半圆）
theta_thales = linspace(0, pi, 50);
x_thales = center_D(1) + R_D * cos(theta_thales);
y_thales = center_D(2) + R_D * sin(theta_thales);
plot(ax3, x_thales, y_thales, ':', 'Color', colors.slate, ...
     'LineWidth', 1, 'DisplayName', 'Thales轨迹 (90°)');

% 从C到A和B的连线
plot(ax3, [C(1), A(1)], [C(2), A(2)], ':', ...
     'Color', colors.slate, 'LineWidth', 1);
plot(ax3, [C(1), B(1)], [C(2), B(2)], ':', ...
     'Color', colors.slate, 'LineWidth', 1);

% 标注60°角
theta_arc = linspace(240, 300, 20);
r_arc = 15;
x_arc = C(1) + r_arc * cosd(theta_arc);
y_arc = C(2) + r_arc * sind(theta_arc);
plot(ax3, x_arc, y_arc, '-', 'Color', colors.rust, 'LineWidth', 2);
text(C(1)-8, C(2)-12, '60° < 90°', 'FontSize', 10, ...
     'Color', colors.rust, 'FontWeight', 'bold', 'Parent', ax3);

% 标注说明
text(a/2, a*sqrt(3)/2 + 25, ...
     {'反例说明：顶点C落在直径圆外', '∠ACB = 60° < 90°（违反Thales判据）'}, ...
     'FontSize', 11, 'HorizontalAlignment', 'center', ...
     'Color', colors.ink, 'BackgroundColor', 'white', ...
     'EdgeColor', colors.ochre, 'LineWidth', 2, ...
     'Margin', 6, 'Parent', ax3);

% 设置坐标轴
xlim(ax3, [-15, 115]);
ylim(ax3, [-20, 110]);
axis(ax3, 'equal');
xlabel(ax3, 'X坐标', 'FontSize', 12, 'FontWeight', 'bold');
ylabel(ax3, 'Y坐标', 'FontSize', 12, 'FontWeight', 'bold');
title(ax3, '等边三角形反例：直径圆失败', 'FontSize', 14, 'FontWeight', 'bold');
legend(ax3, 'Location', 'northeast', 'FontSize', 10);
grid(ax3, 'on');
set(ax3, 'GridAlpha', 0.2, 'GridLineStyle', ':');
box(ax3, 'on');

% 保存
output_path3 = fullfile(output_dir, 'Q1_MAIN_03_等边三角形反例.png');
print(fig3, output_path3, '-dpng', '-r300');
fprintf('✓ 已保存: %s\n\n', output_path3);
close(fig3);

% ============================================================================
% 完成
% ============================================================================
fprintf('======================================================================\n');
fprintf('✅ 图表生成完成！\n');
fprintf('输出目录：%s\n', output_dir);
fprintf('注意：图2和图4需要q1_main.py的数据，请单独生成\n');
fprintf('======================================================================\n');
