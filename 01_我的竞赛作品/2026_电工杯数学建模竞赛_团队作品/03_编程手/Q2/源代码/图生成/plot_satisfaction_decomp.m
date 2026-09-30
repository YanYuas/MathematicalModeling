% ============================================================
% 问题二 满意度分解堆叠柱状图 (美化版)
% S = 0.2*S1(距离) + 0.3*S2(利用率) + 0.5*S3(价格)
% 方案 P9 TOPSIS
% ============================================================
clear; close all; clc;

data_dir = fileparts(mfilename('fullpath'));
if isempty(data_dir), data_dir = pwd; end
parent_dir = fileparts(data_dir);
out_dir = fullfile(parent_dir, '问题二图测试');
if ~exist(out_dir, 'dir'), mkdir(out_dir); end

comm_names = {'A','B','C','D','E','F','G','H','I','J'};
station_names = {'D','C','C','D','G','G','C','D','G','G'};

s1_contrib = [0.1200, 0.1200, 0.2000, 0.2000, 0.1800, 0.1800, 0.1800, 0.2000, 0.1800, 0.1500];
s2_contrib = [0.1945, 0.2557, 0.2557, 0.1945, 0.2338, 0.2338, 0.2557, 0.1945, 0.2338, 0.2338];
s3_contrib = [0.5000, 0.5000, 0.5000, 0.5000, 0.5000, 0.5000, 0.5000, 0.5000, 0.5000, 0.5000];
total_sat = [0.8145, 0.8757, 0.9557, 0.8945, 0.9139, 0.9139, 0.9357, 0.8945, 0.9139, 0.8839];

% ---- 绘图 ----
figure('Position', [80, 80, 1050, 560], 'Color', 'w', ...
       'ToolBar', 'none', 'MenuBar', 'none');

% 暖色系: 蓝(距离) 橙珊瑚(利用率) 暖绿(价格) — 低饱和学术风
bar_colors = [
    0.25 0.45 0.72;   % S1 距禂 — 稳重蓝
    0.92 0.52 0.30;   % S2 利用率 — 暖珊瑚
    0.42 0.62 0.35;   % S3 价格 — 橄榄绿
];

y_data = [s1_contrib; s2_contrib; s3_contrib]';

b = bar(y_data, 'stacked', 'BarWidth', 0.62);
for k = 1:3
    b(k).FaceColor = bar_colors(k, :);
    b(k).EdgeColor = 'none';
end

% 柱顶总分
hold on;
for i = 1:10
    text(i, total_sat(i) + 0.010, sprintf('%.4f', total_sat(i)), ...
         'FontSize', 8.5, 'FontWeight', 'bold', ...
         'HorizontalAlignment', 'center', 'Color', [0.15 0.15 0.15]);
end

% 柱底分配站名
for i = 1:10
    text(i, 0.025, ['\bf' station_names{i}], ...
         'FontSize', 10, 'HorizontalAlignment', 'center', ...
         'Color', [1 1 1]);
end
hold off;

set(gca, 'XTick', 1:10, 'XTickLabel', comm_names, 'FontSize', 11, 'FontWeight', 'bold');
xlabel('小区', 'FontSize', 12, 'FontWeight', 'bold');
ylabel('满意度', 'FontSize', 12, 'FontWeight', 'bold');
title('各小区满意度分解 (P19 最优方案)', 'FontSize', 15, 'FontWeight', 'bold');
ylim([0, 1.03]);
grid on; set(gca, 'GridAlpha', 0.12, 'GridLineStyle', '--'); box on;

legend({'S1 距离满意度 (0.2)', 'S2 利用率满意度 (0.3)', 'S3 价格满意度 (0.5)'}, ...
       'Location', 'southoutside', 'Orientation', 'horizontal', ...
       'FontSize', 9.5, 'Box', 'off');

% 方案说明 (放在图例下方)
text(0.5, -0.18, ...
     '\bf P19方案:\rm C(中型)-D(中型)-G(大型)  |  3站 109万  |  覆盖率85.7%  |  注: S3按基准价恒为1.0', ...
     'Units', 'normalized', 'FontSize', 9, 'Color', [0.35 0.35 0.35], ...
     'HorizontalAlignment', 'center', 'VerticalAlignment', 'top');

out_path = fullfile(out_dir, 'q2_satisfaction_decomp.png');
exportgraphics(gcf, out_path, 'Resolution', 300);
fprintf('已保存: %s\n', out_path);
