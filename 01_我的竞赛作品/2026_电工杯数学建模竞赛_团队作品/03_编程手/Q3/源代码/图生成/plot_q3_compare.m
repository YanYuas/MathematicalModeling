% ============================================================
% Q3 补充图2: Q2 vs Q3 各小区满意度对比柱状图
% ============================================================
clear; close all; clc;

comm_names = {'A','B','C','D','E','F','G','H','I','J'};
station_names = {'D','C','C','D','G','G','C','D','G','G'};

q2_sat = [0.8145, 0.8757, 0.9557, 0.8945, 0.9139, 0.9139, 0.9357, 0.8945, 0.9139, 0.8839];
q3_sat = [0.7700, 0.7700, 0.8500, 0.8500, 0.8300, 0.8300, 0.8300, 0.8500, 0.8300, 0.8000];
diff_sat = q3_sat - q2_sat;

c_q2 = [0.30 0.50 0.80];
c_q3 = [0.92 0.45 0.25];
c_diff_pos = [0.35 0.65 0.35];
c_diff_neg = [0.85 0.30 0.25];

figure('Position', [80, 80, 1050, 580], 'Color', 'w', ...
       'ToolBar', 'none', 'MenuBar', 'none');

x = 1:10;
w = 0.28;

hold on;
b1 = bar(x - w, q2_sat, w, 'FaceColor', c_q2, 'EdgeColor', 'none');
b2 = bar(x + w, q3_sat, w, 'FaceColor', c_q3, 'EdgeColor', 'none');

% 变化箭头和标注
for i = 1:10
    if diff_sat(i) < -0.01
        text(x(i), (q2_sat(i)+q3_sat(i))/2, ...
             sprintf('↓%.3f', -diff_sat(i)), ...
             'FontSize', 7.5, 'FontWeight', 'bold', ...
             'HorizontalAlignment', 'center', 'Color', c_diff_neg);
        % 下降箭头
        plot([x(i) x(i)], [q2_sat(i)+0.01, q3_sat(i)-0.01], ...
             'k-', 'LineWidth', 0.8);
    end
    % 站名
    text(x(i), 0.74, ['\bf' station_names{i}], ...
         'FontSize', 8, 'HorizontalAlignment', 'center', 'Color', [1 1 1]);
end

% Q2均值线
q2_mean = mean(q2_sat);
plot([0.3 10.7], [q2_mean q2_mean], '--', 'Color', c_q2, 'LineWidth', 1.5);
text(10.5, q2_mean, sprintf('Q2均值=%.4f', q2_mean), 'FontSize', 9, 'Color', c_q2, 'FontWeight', 'bold');

% Q3均值线
q3_mean = mean(q3_sat);
plot([0.3 10.7], [q3_mean q3_mean], '--', 'Color', c_q3, 'LineWidth', 1.5);
text(10.5, q3_mean, sprintf('Q3均值=%.4f', q3_mean), 'FontSize', 9, 'Color', c_q3, 'FontWeight', 'bold');

hold off;

set(gca, 'XTick', x, 'XTickLabel', comm_names, 'FontSize', 11, 'FontWeight', 'bold');
xlabel('小区', 'FontSize', 12, 'FontWeight', 'bold');
ylabel('满意度', 'FontSize', 12, 'FontWeight', 'bold');
title('Q2 vs Q3 各小区满意度对比 — Q3全面下降(S2利用率崩塌)', 'FontSize', 14, 'FontWeight', 'bold');
ylim([0.72, 1.0]);
grid on; set(gca, 'GridAlpha', 0.12, 'GridLineStyle', '--'); box on;

legend([b1 b2], {'Q2 优化前', 'Q3 优化后(含补贴定价)'}, ...
       'Location', 'southoutside', 'Orientation', 'horizontal', ...
       'FontSize', 10, 'Box', 'off');

text(0.012, 0.985, ...
     '\bf 关键发现:\rm 全10小区满意度下降0.04-0.11, 均值从0.900降至0.822。定价降低虽使S3=1.0, 但需求量增加→利用率超100%→S2崩塌至0.50', ...
     'Units', 'normalized', 'FontSize', 8.5, 'Color', [0.35 0.35 0.35], 'VerticalAlignment', 'top');

exportgraphics(gcf, 'c:/Users/29845/Desktop/Q3图/图6_Q2vsQ3满意度对比.png', 'Resolution', 300);
fprintf('满意度对比 saved\n');
