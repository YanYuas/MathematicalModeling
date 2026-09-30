% ============================================================
% Q3.2 图1: 最优定价 vs 基准价 分组柱状图
% 数据: Q3表格_最优定价.csv
% ============================================================
clear; close all; clc;

% 数据
services = {'助餐','日间照料','上门护理','康复理疗','助浴'};
benchmark = [10, 20, 30, 28, 25];
optimal   = [8.57, 17.15, 25.72, 24.00, 21.43];
drop_pct  = (optimal - benchmark) ./ benchmark * 100;

% 配色
c_bench = [0.30 0.50 0.75];   % 基准价 蓝
c_opt   = [0.92 0.52 0.25];   % 最优价 暖橙

figure('Position', [100, 100, 880, 560], 'Color', 'w', ...
       'ToolBar', 'none', 'MenuBar', 'none');

x = 1:5;
w = 0.32;
hold on;
b1 = bar(x - w/2, benchmark, w, 'FaceColor', c_bench, 'EdgeColor', 'none');
b2 = bar(x + w/2, optimal,   w, 'FaceColor', c_opt,   'EdgeColor', 'none');

% 柱顶标注
for i = 1:5
    text(x(i)-w/2, benchmark(i)+0.6, sprintf('%.0f', benchmark(i)), ...
         'FontSize', 9, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Color', c_bench);
    text(x(i)+w/2, optimal(i)+0.6, sprintf('%.2f', optimal(i)), ...
         'FontSize', 9, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', 'Color', c_opt);
    text(x(i), max(benchmark(i), optimal(i)) + 2.2, sprintf('%.1f%%', drop_pct(i)), ...
         'FontSize', 8, 'HorizontalAlignment', 'center', 'Color', [0.6 0.2 0.2]);
end

hold off;
set(gca, 'XTick', x, 'XTickLabel', services, 'FontSize', 11);
ylabel('价格 (元/次)', 'FontSize', 12, 'FontWeight', 'bold');
title('最优定价 vs 基准价', 'FontSize', 15, 'FontWeight', 'bold');
legend([b1 b2], {'基准价', '最优定价'}, 'Location', 'northeast', 'FontSize', 10, 'Box', 'off');
grid on; set(gca, 'GridAlpha', 0.15); box on;
ylim([0, 35]);

text(0.01, 0.96, '\rm 注: 五项服务均降价14.3%, S3价格满意度=1.0(平价满分)', ...
     'Units', 'normalized', 'FontSize', 9, 'Color', [0.45 0.45 0.45]);

out_path = 'c:/Users/29845/Desktop/Q3图/图1_最优定价对比.png';
exportgraphics(gcf, out_path, 'Resolution', 300);
fprintf('已保存: %s\n', out_path);
