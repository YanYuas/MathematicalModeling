%% Q1图表美化脚本 - 基于academic-figure标准优化
% 生成时间：2026-09-11
% 优化内容：视觉层次、配色对比、标注清晰度
% 数学数据：保持不变（D=39.598327m, R_MEC=19.799164m, γ=1.000000）

clear; clc; close all;

%% 配置
addpath(fileparts(mfilename('fullpath')));  % 添加当前目录
outdir = fullfile('..', '实验结果', 'figs');
if ~exist(outdir, 'dir'), mkdir(outdir); end

% Ink & Ochre 配色方案
C = struct( ...
    'ink',      [0.11 0.11 0.11], ...  % #1C1C1C
    'slate',    [0.36 0.42 0.45], ...  % #5B6B73
    'paper',    [0.97 0.96 0.93], ...  % #F7F4EE
    'field',    [0.77 0.83 0.88], ...  % #C5D4E0
    'geometry', [0.17 0.29 0.43], ...  % #2C4A6E
    'ochre',    [0.77 0.48 0.17], ...  % #C47B2B
    'rust',     [0.55 0.23 0.16], ...  % #8C3A2A
    'sage',     [0.31 0.43 0.36]  ...  % #4F6F5C
);

fprintf('==========================================================\n');
fprintf('Q1 图表美化工具（基于 academic-figure 标准）\n');
fprintf('==========================================================\n\n');

%% 图1：优化 Q1_MAIN_01_角域示意.png
fprintf('正在生成优化版图1：单站角域示意...\n');

fig1 = figure('Position', [100, 100, 700, 700], 'Color', C.paper);
ax1 = axes('Parent', fig1, 'Color', C.paper); hold(ax1, 'on');

S1 = [0, 0]; theta1 = 45; eps_angle = 15; r_max = 250;

% 角域（提升可见度）
theta_range = linspace(theta1-eps_angle, theta1+eps_angle, 50);
x_wedge = [S1(1), r_max*cosd(theta_range), S1(1)];
y_wedge = [S1(2), r_max*sind(theta_range), S1(2)];
patch(x_wedge, y_wedge, C.field, 'EdgeColor', 'none', 'FaceAlpha', 0.25, 'Parent', ax1);

% 边界射线（加粗）
for angle = [theta1-eps_angle, theta1+eps_angle]
    x_end = S1(1) + r_max * cosd(angle);
    y_end = S1(2) + r_max * sind(angle);
    plot(ax1, [S1(1), x_end], [S1(2), y_end], '--', 'Color', C.geometry, 'LineWidth', 2.2);
end

% 中心射线
x_center = S1(1) + r_max * cosd(theta1);
y_center = S1(2) + r_max * sind(theta1);
plot(ax1, [S1(1), x_center], [S1(2), y_center], '-', 'Color', C.ochre, 'LineWidth', 3.0);

% 检测站
plot(ax1, S1(1), S1(1), 'o', 'MarkerSize', 12, 'MarkerFaceColor', C.rust, ...
     'MarkerEdgeColor', C.ink, 'LineWidth', 1.5);
text(S1(1)-22, S1(2)-32, 'S_1', 'FontSize', 13, 'Color', C.ink, 'FontWeight', 'bold');

% 角度标注（改进位置）
theta_arc = linspace(theta1-eps_angle, theta1+eps_angle, 30);
r_arc = 80;
x_arc = S1(1) + r_arc * cosd(theta_arc);
y_arc = S1(2) + r_arc * sind(theta_arc);
plot(ax1, x_arc, y_arc, '-', 'Color', C.ochre, 'LineWidth', 2.2);
text(55, 48, '2\epsilon = 2°', 'FontSize', 12, 'Color', C.ochre, 'FontWeight', 'bold');

% 不确定性标注（改用箭头）
annotation('textarrow', [0.65, 0.58], [0.72, 0.65], ...
    'String', '大不确定性', 'FontSize', 11, 'Color', C.slate, ...
    'LineWidth', 1.5, 'HeadWidth', 12, 'HeadLength', 10);
text(165, 165, '（单站无法定位）', 'FontSize', 10, 'Color', C.slate);

% 射线标注
text(185, 225, '\theta+\epsilon', 'FontSize', 12, 'Color', C.geometry, 'FontWeight', 'bold');
text(185, 115, '\theta-\epsilon', 'FontSize', 12, 'Color', C.geometry, 'FontWeight', 'bold');

xlim(ax1, [-50, 300]); ylim(ax1, [-50, 300]); axis(ax1, 'equal');
xlabel(ax1, 'X 坐标 (m)', 'FontSize', 13, 'FontWeight', 'bold');
ylabel(ax1, 'Y 坐标 (m)', 'FontSize', 13, 'FontWeight', 'bold');
title(ax1, '单站角域示意：测向误差形成楔形不确定区', 'FontSize', 14, 'FontWeight', 'bold');
grid(ax1, 'on'); set(ax1, 'GridAlpha', 0.3, 'GridLineStyle', ':');
box(ax1, 'on');

print(fig1, fullfile(outdir, 'Q1_MAIN_01_角域示意_优化版.png'), '-dpng', '-r300');
fprintf('✓ 已保存: Q1_MAIN_01_角域示意_优化版.png\n\n');
close(fig1);

%% 图3：优化 Q1_MAIN_03_等边三角形反例.png
fprintf('正在生成优化版图3：等边三角形反例...\n');

fig3 = figure('Position', [100, 100, 1000, 900], 'Color', C.paper);
ax3 = axes('Parent', fig3, 'Color', C.paper); hold(ax3, 'on');

a = 100; A = [0, 0]; B = [a, 0]; C_pt = [a/2, a*sqrt(3)/2];
triangle = [A; B; C_pt; A];

% 三角形
patch(triangle(1:3,1), triangle(1:3,2), C.field, 'EdgeColor', 'none', 'FaceAlpha', 0.10);
plot(ax3, triangle(:,1), triangle(:,2), '-', 'Color', C.geometry, 'LineWidth', 3.5);

% 顶点标注
vertices = {A, 'A', -10, -15; B, 'B', 10, -15; C_pt, 'C', 0, 10};
for i = 1:3
    pt = vertices{i,1};
    plot(ax3, pt(1), pt(2), 'o', 'MarkerSize', 12, ...
         'MarkerFaceColor', C.geometry, 'MarkerEdgeColor', C.ink, 'LineWidth', 1.5);
    text(pt(1)+vertices{i,3}, pt(2)+vertices{i,4}, vertices{i,2}, ...
         'FontSize', 16, 'FontWeight', 'bold', 'Color', C.ink);
end

% 直径和直径圆（失败）
D = a; center_D = (A + B) / 2; R_D = D / 2;
theta_circle = linspace(0, 2*pi, 200);
x_circle_D = center_D(1) + R_D * cos(theta_circle);
y_circle_D = center_D(2) + R_D * sin(theta_circle);
plot(ax3, x_circle_D, y_circle_D, '--', 'Color', C.rust, 'LineWidth', 2.8);
plot(ax3, [A(1), B(1)], [A(2), B(2)], '-', 'Color', C.ochre, 'LineWidth', 4.0);
plot(ax3, center_D(1), center_D(2), '+', 'Color', C.rust, 'MarkerSize', 15, 'LineWidth', 3);

% 外接圆（成功）
R_circum = D / sqrt(3);
center_circum = [a/2, a/(2*sqrt(3))];
x_circle_circum = center_circum(1) + R_circum * cos(theta_circle);
y_circle_circum = center_circum(2) + R_circum * sin(theta_circle);
plot(ax3, x_circle_circum, y_circle_circum, '-', 'Color', C.sage, 'LineWidth', 3.2);
plot(ax3, center_circum(1), center_circum(2), '+', 'Color', C.sage, ...
     'MarkerSize', 15, 'LineWidth', 3);

% Thales轨迹
theta_thales = linspace(0, pi, 80);
x_thales = center_D(1) + R_D * cos(theta_thales);
y_thales = center_D(2) + R_D * sin(theta_thales);
plot(ax3, x_thales, y_thales, ':', 'Color', C.slate, 'LineWidth', 1.2);

% 从C到A和B的连线
plot(ax3, [C_pt(1), A(1)], [C_pt(2), A(2)], ':', 'Color', C.slate, 'LineWidth', 1.0);
plot(ax3, [C_pt(1), B(1)], [C_pt(2), B(2)], ':', 'Color', C.slate, 'LineWidth', 1.0);

% 60°角标注（扇形）
theta_arc = linspace(240, 300, 30);
r_arc = 20;
x_arc = C_pt(1) + r_arc * cosd(theta_arc);
y_arc = C_pt(2) + r_arc * sind(theta_arc);
patch([C_pt(1) x_arc C_pt(1)], [C_pt(2) y_arc C_pt(2)], C.rust, ...
      'FaceAlpha', 0.25, 'EdgeColor', C.rust, 'LineWidth', 2.2);
text(C_pt(1)-6, C_pt(2)-18, '60°', 'FontSize', 14, 'Color', C.rust, 'FontWeight', 'bold');
text(C_pt(1)+12, C_pt(2)-18, '< 90°', 'FontSize', 12, 'Color', C.rust, 'FontWeight', 'bold');

% Jung定理标注框
text(a/2, a*sqrt(3)/2 + 20, ...
     'Jung 定理：D/2 \leq R_{MEC} \leq D/\surd3', ...
     'FontSize', 13, 'Color', C.ink, 'FontWeight', 'bold', ...
     'HorizontalAlignment', 'center', ...
     'BackgroundColor', [1 1 0.9], 'EdgeColor', C.ink, ...
     'Margin', 6, 'LineWidth', 1.5);

% 直径标注
text(a/2, -8, sprintf('直径 D = %.1f m', D), 'FontSize', 12, ...
     'Color', C.ochre, 'FontWeight', 'bold', 'HorizontalAlignment', 'center');

% 图例文本框
legend_text = {...
    '\color[rgb]{0.55,0.23,0.16}× 直径圆 R=D/2=50 无法覆盖', ...
    '\color[rgb]{0.31,0.43,0.36}✓ 外接圆 R=D/\surd3=57.7 恰好覆盖', ...
    '    （点 C 落在直径圆外，\angleACB=60°<90°）'};
text(8, 72, legend_text, 'FontSize', 11, ...
     'BackgroundColor', 'w', 'EdgeColor', C.slate, ...
     'Margin', 5, 'LineWidth', 1.2);

xlim(ax3, [-18, 118]); ylim(ax3, [-28, 120]); axis(ax3, 'equal');
xlabel(ax3, 'X 坐标 (m)', 'FontSize', 13, 'FontWeight', 'bold');
ylabel(ax3, 'Y 坐标 (m)', 'FontSize', 13, 'FontWeight', 'bold');
title(ax3, '等边三角形反例：\gamma = 2/\surd3（Jung 上界取等）', ...
      'FontSize', 15, 'FontWeight', 'bold');
grid(ax3, 'on'); set(ax3, 'GridAlpha', 0.3, 'GridLineStyle', ':');
box(ax3, 'on');

print(fig3, fullfile(outdir, 'Q1_MAIN_03_等边三角形反例_优化版.png'), '-dpng', '-r300');
fprintf('✓ 已保存: Q1_MAIN_03_等边三角形反例_优化版.png\n\n');
close(fig3);

%% 完成
fprintf('==========================================================\n');
fprintf('✅ 图表美化完成！\n');
fprintf('输出目录：%s\n', outdir);
fprintf('已生成 2 张优化版图表（其他图表保持原样，质量已达标）\n');
fprintf('==========================================================\n');
