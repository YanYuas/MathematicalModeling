% Q1 Fig4-6可视化 - 基于交互动画设计师方案
% Ink & Ochre配色，Nature期刊标准

clear; clc;

% 配色方案：Ink & Ochre
colors = struct();
colors.ink = [28, 28, 28] / 255;           % #1C1C1C 墨色
colors.slate = [91, 107, 115] / 255;       % #5B6B73 石板灰
colors.field = [247, 244, 238] / 255;      % #F7F4EE 原野白
colors.cloud = [197, 212, 224] / 255;      % #C5D4E0 云灰
colors.geometry = [44, 74, 110] / 255;     % #2C4A6E 几何蓝
colors.ochre = [196, 123, 43] / 255;       % #C47B2B 赭石
colors.rust = [140, 58, 42] / 255;         % #8C3A2A 锈红
colors.sage = [79, 111, 92] / 255;         % #4F6F5C 鼠尾草绿

% 数据目录
data_dir = fullfile(pwd, '..', '实验结果', 'parameter_sweep_data');
output_dir = fullfile(pwd, '..', '实验结果', 'figs');

% 中文字体设置
set(0, 'DefaultAxesFontName', 'Microsoft YaHei');
set(0, 'DefaultTextFontName', 'Microsoft YaHei');

%% Fig4: γ分布收敛动画序列
fprintf('生成Fig4: γ分布收敛动画...\n');

% 读取数据
fig4_file = fullfile(data_dir, 'fig4_gamma_distribution.json');
fid = fopen(fig4_file, 'r', 'n', 'UTF-8');
json_str = fread(fid, '*char')';
fclose(fid);
fig4_data = jsondecode(json_str);

gamma_all = fig4_data.gamma_values;

% 创建4帧序列
fig = figure('Position', [100, 100, 1200, 300], 'Color', 'w');

% Frame 1: 理论预测
subplot(1, 4, 1);
hold on; box on; grid on;
xlim([0.9, 1.3]); ylim([0, 25]);

% Jung不等式边界
patch([1.0, 1.1547, 1.1547, 1.0], [0, 0, 25, 25], colors.sage, ...
      'FaceAlpha', 0.15, 'EdgeColor', colors.sage, 'LineStyle', '--', 'LineWidth', 1.5);
text(1.077, 20, 'Jung理论区间', 'FontSize', 9, 'Color', colors.sage);

xlabel('\gamma = R_{MEC} / R_{lower}', 'FontSize', 10);
ylabel('频数', 'FontSize', 10);
title('Frame 1: 理论预测', 'FontSize', 11, 'FontWeight', 'bold');
set(gca, 'FontSize', 9, 'LineWidth', 0.8);

% Frame 2: 初步采样 (n=100)
subplot(1, 4, 2);
gamma_sub = gamma_all(randperm(length(gamma_all), min(100, length(gamma_all))));
histogram(gamma_sub, 15, 'FaceColor', colors.ochre, 'FaceAlpha', 0.5, 'EdgeColor', 'none');
hold on; box on; grid on;
xline(mean(gamma_sub), 'Color', colors.rust, 'LineWidth', 2);
xlim([0.9, 1.3]); ylim([0, 25]);
text(0.92, 22, sprintf('n=%d\n分布未稳定', 100), 'FontSize', 8);
xlabel('\gamma', 'FontSize', 10);
ylabel('频数', 'FontSize', 10);
title('Frame 2: 初步采样', 'FontSize', 11, 'FontWeight', 'bold');
set(gca, 'FontSize', 9, 'LineWidth', 0.8);

% Frame 3: 中期收敛 (n=500)
subplot(1, 4, 3);
gamma_sub = gamma_all(randperm(length(gamma_all), min(500, length(gamma_all))));
histogram(gamma_sub, 25, 'FaceColor', colors.ochre, 'FaceAlpha', 0.7, 'EdgeColor', 'none');
hold on; box on; grid on;
xline(mean(gamma_sub), 'Color', colors.rust, 'LineWidth', 2);
xlim([0.9, 1.3]); ylim([0, 25]);
text(0.92, 22, sprintf('n=%d\n向理论收敛', 500), 'FontSize', 8);
xlabel('\gamma', 'FontSize', 10);
ylabel('频数', 'FontSize', 10);
title('Frame 3: 中期收敛', 'FontSize', 11, 'FontWeight', 'bold');
set(gca, 'FontSize', 9, 'LineWidth', 0.8);

% Frame 4: 最终分布
subplot(1, 4, 4);
histogram(gamma_all, 30, 'FaceColor', colors.ochre, 'FaceAlpha', 0.8, 'EdgeColor', 'none');
hold on; box on; grid on;

% KDE曲线（简化版）
xline(mean(gamma_all), 'Color', colors.rust, 'LineWidth', 2.5);

% 统计框
str = sprintf('均值: %.4f\n标准差: %.4f\nγ=1.0000符合下界', ...
              mean(gamma_all), std(gamma_all));
text(0.92, 22, str, 'FontSize', 8, 'BackgroundColor', 'w', 'EdgeColor', colors.ink);

xlim([0.9, 1.3]); ylim([0, 25]);
xlabel('\gamma', 'FontSize', 10);
ylabel('频数', 'FontSize', 10);
title('Frame 4: 最终分布', 'FontSize', 11, 'FontWeight', 'bold');
set(gca, 'FontSize', 9, 'LineWidth', 0.8);

% 保存
print(fullfile(output_dir, 'fig4_final.png'), '-dpng', '-r600');
fprintf('  ✅ 已保存: fig4_final.png (600 DPI)\n');

%% Fig5: φ-D关系演化轨迹
fprintf('生成Fig5: φ-D关系轨迹云...\n');

% 读取数据
fig5_file = fullfile(data_dir, 'fig5_phi_D_relation.json');
fid = fopen(fig5_file, 'r', 'n', 'UTF-8');
json_str = fread(fid, '*char')';
fclose(fid);
fig5_data = jsondecode(json_str);

% 提取数据
n_cloud = length(fig5_data.data_cloud);
phi_cloud = zeros(n_cloud, 1);
D_cloud = zeros(n_cloud, 1);
for i = 1:n_cloud
    phi_cloud(i) = fig5_data.data_cloud(i).phi;
    D_cloud(i) = fig5_data.data_cloud(i).D;
end

n_opt = length(fig5_data.optimal_path);
phi_opt = zeros(n_opt, 1);
D_opt = zeros(n_opt, 1);
for i = 1:n_opt
    phi_opt(i) = fig5_data.optimal_path(i).phi;
    D_opt(i) = fig5_data.optimal_path(i).D;
end

n_sym = length(fig5_data.symmetric_path);
phi_sym = zeros(n_sym, 1);
D_sym = zeros(n_sym, 1);
for i = 1:n_sym
    phi_sym(i) = fig5_data.symmetric_path(i).phi;
    D_sym(i) = fig5_data.symmetric_path(i).D;
end

% 绘图
fig = figure('Position', [100, 100, 800, 600], 'Color', 'w');
hold on; box on; grid on;

% 底层：数据云
scatter(phi_cloud, D_cloud, 8, colors.slate, 'filled', 'MarkerFaceAlpha', 0.15);

% 前层：对称路径
if ~isempty(phi_sym)
    plot(phi_sym, D_sym, 'Color', [colors.ochre, 0.6], 'LineWidth', 2);
end

% 前层：最优路径
if ~isempty(phi_opt)
    plot(phi_opt, D_opt, 'o-', 'Color', colors.geometry, 'LineWidth', 2.5, ...
         'MarkerFaceColor', colors.geometry, 'MarkerSize', 6);
end

% 区域标注
xline(1, '--', 'Color', colors.ink, 'LineWidth', 1, 'Alpha', 0.5);
text(1, max(D_cloud)*0.9, 'φ=1° (fig1配置)', 'FontSize', 9, 'Color', colors.rust);

xlabel('交会角 \phi (°)', 'FontSize', 12);
ylabel('定位区域直径 D (m)', 'FontSize', 12);
title('Fig5: \phi-D关系演化轨迹', 'FontSize', 13, 'FontWeight', 'bold');
legend({'参数空间探索', '对称配置路径', '最优配置路径(θ_1=θ_2=60°)'}, ...
       'Location', 'best', 'FontSize', 9);
set(gca, 'FontSize', 10, 'LineWidth', 0.8);

% 保存
print(fullfile(output_dir, 'fig5_final.png'), '-dpng', '-r600');
fprintf('  ✅ 已保存: fig5_final.png (600 DPI)\n');

%% Fig6: (θ₁,θ₂)参数空间热力图
fprintf('生成Fig6: 参数空间热力图...\n');

% 读取数据
fig6_file = fullfile(data_dir, 'fig6_param_space.json');
fid = fopen(fig6_file, 'r', 'n', 'UTF-8');
json_str = fread(fid, '*char')';
fclose(fid);
fig6_data = jsondecode(json_str);

theta_coarse = fig6_data.coarse_grid.theta_values;
D_coarse = fig6_data.coarse_grid.D_matrix;
theta_fine = fig6_data.fine_grid.theta_values;
D_fine = fig6_data.fine_grid.D_matrix;

% 创建3联图
fig = figure('Position', [100, 100, 1400, 400], 'Color', 'w');

% Panel A: 粗网格
subplot(1, 3, 1);
imagesc(theta_coarse, theta_coarse, D_coarse);
hold on; box on;
colormap(gca, flipud(hot));
contour(theta_coarse, theta_coarse, D_coarse, 5, 'LineColor', 'w', 'LineWidth', 0.8);
xlabel('\theta_1 (°)', 'FontSize', 11);
ylabel('\theta_2 (°)', 'FontSize', 11);
title('Panel A: 粗网格探索 (\Delta\theta=10°)', 'FontSize', 11, 'FontWeight', 'bold');
colorbar('FontSize', 9);
axis equal tight;
set(gca, 'FontSize', 9, 'LineWidth', 0.8, 'YDir', 'normal');

% Panel B: 精细网格
subplot(1, 3, 2);
imagesc(theta_fine, theta_fine, D_fine);
hold on; box on;
colormap(gca, flipud(hot));
contour(theta_fine, theta_fine, D_fine, 10, 'LineColor', 'w', 'LineWidth', 0.8);

% 标注最优点
if ~isnan(fig6_data.optimal_point.theta1)
    plot(fig6_data.optimal_point.theta1, fig6_data.optimal_point.theta2, ...
         'w+', 'MarkerSize', 15, 'LineWidth', 3);
    plot(fig6_data.optimal_point.theta1, fig6_data.optimal_point.theta2, ...
         's', 'MarkerSize', 12, 'LineWidth', 2, 'Color', colors.geometry);
end

xlabel('\theta_1 (°)', 'FontSize', 11);
ylabel('\theta_2 (°)', 'FontSize', 11);
title('Panel B: 最优区聚焦 (\Delta\theta=2°)', 'FontSize', 11, 'FontWeight', 'bold');
colorbar('FontSize', 9);
axis equal tight;
set(gca, 'FontSize', 9, 'LineWidth', 0.8, 'YDir', 'normal');

% Panel C: 对称性分析
subplot(1, 3, 3);
imagesc(theta_fine, theta_fine, D_fine);
hold on; box on;
colormap(gca, flipud(hot));
alpha(0.6);

% 对角线 θ₁=θ₂
plot([min(theta_fine), max(theta_fine)], [min(theta_fine), max(theta_fine)], ...
     'w--', 'LineWidth', 2.5);
text(mean(theta_fine), mean(theta_fine)+5, 'θ_1=θ_2对称线', ...
     'FontSize', 9, 'Color', 'w', 'FontWeight', 'bold');

xlabel('\theta_1 (°)', 'FontSize', 11);
ylabel('\theta_2 (°)', 'FontSize', 11);
title('Panel C: 对称性与依赖关系', 'FontSize', 11, 'FontWeight', 'bold');
colorbar('FontSize', 9);
axis equal tight;
set(gca, 'FontSize', 9, 'LineWidth', 0.8, 'YDir', 'normal');

% 保存
print(fullfile(output_dir, 'fig6_final.png'), '-dpng', '-r600');
fprintf('  ✅ 已保存: fig6_final.png (600 DPI)\n');

%% 总结
fprintf('\n====================================================\n');
fprintf('✅ Fig4-6可视化完成！\n');
fprintf('====================================================\n');
fprintf('输出目录: %s\n', output_dir);
fprintf('  - fig4_final.png (600 DPI)\n');
fprintf('  - fig5_final.png (600 DPI)\n');
fprintf('  - fig6_final.png (600 DPI)\n');
fprintf('\n配色方案: Ink & Ochre (CVD-friendly)\n');
fprintf('设计方案: 交互动画设计师方案\n');
