% ============================================================
% Q3.2 图3: 各小区满意度分解堆叠柱状 (含价格满意度)
% 数据: Q3表格_小区满意度.csv
% ============================================================
clear; close all; clc;

comm_names = {'B','C','G','A','D','H','E','F','I','J'};
stations_assigned = {'C','C','C','D','D','D','G','G','G','G'};

% 贡献值 = 权重 × 因素得分
s1_contrib = [0.120, 0.200, 0.180, 0.120, 0.200, 0.200, 0.180, 0.180, 0.180, 0.150];
s2_contrib = [0.150, 0.150, 0.150, 0.150, 0.150, 0.150, 0.150, 0.150, 0.150, 0.150];
s3_contrib = [0.500, 0.500, 0.500, 0.500, 0.500, 0.500, 0.500, 0.500, 0.500, 0.500];
total_sat   = [0.770, 0.850, 0.830, 0.770, 0.850, 0.850, 0.830, 0.830, 0.830, 0.800];

% 配色
c_s1 = [0.25 0.45 0.72];   % S1 距离 蓝
c_s2 = [0.92 0.52 0.30];   % S2 利用率 珊瑚
c_s3 = [0.42 0.62 0.35];   % S3 价格 橄榄绿

figure('Position', [80, 80, 1050, 560], 'Color', 'w', ...
       'ToolBar', 'none', 'MenuBar', 'none');

y_data = [s1_contrib; s2_contrib; s3_contrib]';

b = bar(y_data, 'stacked', 'BarWidth', 0.62);
b(1).FaceColor = c_s1; b(1).EdgeColor = 'none';
b(2).FaceColor = c_s2; b(2).EdgeColor = 'none';
b(3).FaceColor = c_s3; b(3).EdgeColor = 'none';

hold on;
for i = 1:10
    text(i, total_sat(i) + 0.015, sprintf('%.3f', total_sat(i)), ...
         'FontSize', 8, 'FontWeight', 'bold', ...
         'HorizontalAlignment', 'center', 'Color', [0.15 0.15 0.15]);

    % 站名标注在柱底
    text(i, 0.03, ['\bf' stations_assigned{i}], ...
         'FontSize', 9, 'HorizontalAlignment', 'center', 'Color', [1 1 1]);

    % S3占比标注
    text(i, 0.60, sprintf('S3=%.2f', s3_contrib(i)/0.5), ...
         'FontSize', 7, 'HorizontalAlignment', 'center', 'Color', [1 1 1]);
end
hold off;

set(gca, 'XTick', 1:10, 'XTickLabel', comm_names, 'FontSize', 11, 'FontWeight', 'bold');
xlabel('小区', 'FontSize', 12, 'FontWeight', 'bold');
ylabel('满意度', 'FontSize', 12, 'FontWeight', 'bold');
title('各小区满意度分解 — S3(价格)满分, S2(利用率)崩塌', 'FontSize', 14, 'FontWeight', 'bold');
ylim([0, 0.92]);
grid on; set(gca, 'GridAlpha', 0.12, 'GridLineStyle', '--'); box on;

legend({'S1 距离 (0.2)', 'S2 利用率 (0.3)', 'S3 价格满意度 (0.5)'}, ...
       'Location', 'southoutside', 'Orientation', 'horizontal', ...
       'FontSize', 9.5, 'Box', 'off');

text(0.012, 0.985, '\rm 注: S2统一0.50因利用率超100%(容量不足), S3因全降价14.3%满分1.0', ...
     'Units', 'normalized', 'FontSize', 8.5, 'Color', [0.5 0.5 0.5], ...
     'VerticalAlignment', 'top');

out_path = 'c:/Users/29845/Desktop/Q3图/图3_满意度分解.png';
exportgraphics(gcf, out_path, 'Resolution', 300);
fprintf('已保存: %s\n', out_path);
