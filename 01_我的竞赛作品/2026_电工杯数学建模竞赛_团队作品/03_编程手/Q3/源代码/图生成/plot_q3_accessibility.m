% ============================================================
% Q3.3 图4: 三类老人可及性双轴图
% 数据: Q3表格_可及性分析.csv
% ============================================================
clear; close all; clc;

types = {'自理','半失能','失能'};
total_pop  = [4981, 1471, 1125];
affordable_pct = [100.0, 93.1, 37.4];
fulfill_rate   = [100.0, 99.7, 93.7];
daily_subsidy  = [1.61, 3.12, 4.06];
annual_subsidy = [588, 1140, 1482];

% 配色
c_types = [0.25 0.55 0.70; 0.92 0.55 0.25; 0.80 0.25 0.25];

figure('Position', [80, 80, 900, 560], 'Color', 'w', ...
       'ToolBar', 'none', 'MenuBar', 'none');

x = 1:3;
w = 0.5;

yyaxis left;
hold on;
for i = 1:3
    bar(x(i), affordable_pct(i), w, 'FaceColor', c_types(i,:), ...
        'EdgeColor', 'none', 'FaceAlpha', 0.85);
    text(x(i), affordable_pct(i) + 3, sprintf('%.1f%%', affordable_pct(i)), ...
         'FontSize', 11, 'FontWeight', 'bold', ...
         'HorizontalAlignment', 'center', 'Color', c_types(i,:));
end
ylabel('可负担比例 (%)', 'FontSize', 12, 'FontWeight', 'bold');
set(gca, 'YColor', [0.2 0.2 0.2]);
ylim([0, 115]);

yyaxis right;
plot(x, fulfill_rate, 'ko-', 'LineWidth', 2.5, 'MarkerSize', 12, ...
     'MarkerFaceColor', [0.15 0.15 0.15]);
for i = 1:3
    text(x(i), fulfill_rate(i) - 1.5, sprintf('%.1f%%', fulfill_rate(i)), ...
         'FontSize', 9, 'FontWeight', 'bold', ...
         'HorizontalAlignment', 'center', 'Color', [0.15 0.15 0.15]);
end
ylabel('需求满足率 (%)', 'FontSize', 12, 'FontWeight', 'bold');
set(gca, 'YColor', [0.15 0.15 0.15]);
ylim([90, 102]);
hold off;

set(gca, 'XTick', x, 'XTickLabel', types, 'FontSize', 12, 'FontWeight', 'bold');
title('三类老人服务可及性对比', 'FontSize', 15, 'FontWeight', 'bold');
grid on; set(gca, 'GridAlpha', 0.12); box on;

% 人数和补贴标注
for i = 1:3
    text(x(i), 95 - i*2, ...
         sprintf('%.0f人 | 补贴%.0f元/年', total_pop(i), annual_subsidy(i)), ...
         'FontSize', 8.5, 'HorizontalAlignment', 'center', 'Color', [0.45 0.45 0.45]);
end

% 失能老人高亮
text(3, 38, '\bf 失能老人仅37.4%可负担!', ...
     'FontSize', 11, 'Color', [0.7 0.15 0.15], 'HorizontalAlignment', 'center', ...
     'VerticalAlignment', 'top');

legend({'可负担比例', '', '', '需求满足率'}, ...
       'Location', 'northeast', 'FontSize', 10, 'Box', 'off');

out_path = 'c:/Users/29845/Desktop/Q3图/图4_可及性分析.png';
exportgraphics(gcf, out_path, 'Resolution', 300);
fprintf('已保存: %s\n', out_path);
