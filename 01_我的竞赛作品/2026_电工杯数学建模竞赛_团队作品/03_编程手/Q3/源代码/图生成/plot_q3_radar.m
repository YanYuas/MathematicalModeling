% ============================================================
% Q3 补充图1: Q2 vs Q3 雷达图 — 六维综合对比
% ============================================================
clear; close all; clc;

% 六维指标: [覆盖率, 满意度, 价格S3, 利润率%, 补贴/10万, 最低小区满意度]
dim_names = {'覆盖率(%)','加权满意度','价格满意度S3','利润率(%)','政府补贴(万/年)','最低小区满意度'};

q2_vals = [85.66, 0.8999, 1.00, 5.0, 0, 0.8145];
q3_vals = [85.66, 0.8215, 1.00, 0.0, 226.3, 0.7700];

% 归一化到0-1 (覆盖率/100, 补贴/300)
q2_norm = [q2_vals(1)/100, q2_vals(2), q2_vals(3), q2_vals(4)/10, q2_vals(5)/300, q2_vals(6)];
q3_norm = [q3_vals(1)/100, q3_vals(2), q3_vals(3), q3_vals(4)/10, q3_vals(5)/300, q3_vals(6)];

n_dim = 6;
angles = linspace(0, 2*pi, n_dim+1);
angles = angles(1:end-1);

figure('Position', [80, 80, 750, 650], 'Color', 'w', ...
       'ToolBar', 'none', 'MenuBar', 'none');

% 雷达背景
hold on;
for level = 0.2:0.2:1.0
    x_ring = level * cos(angles);
    y_ring = level * sin(angles);
    patch([x_ring x_ring(1)], [y_ring y_ring(1)], [0.9 0.9 0.9], ...
          'EdgeColor', [0.7 0.7 0.7], 'LineWidth', 0.5, 'FaceAlpha', 0.05);
end

% 轴线
for i = 1:n_dim
    plot([0 cos(angles(i))], [0 sin(angles(i))], 'Color', [0.7 0.7 0.7], 'LineWidth', 0.8);
end

% Q2填充
q2_x = q2_norm .* cos(angles);
q2_y = q2_norm .* sin(angles);
patch([q2_x q2_x(1)], [q2_y q2_y(1)], [0.30 0.50 0.80], ...
      'FaceAlpha', 0.2, 'EdgeColor', [0.20 0.35 0.60], 'LineWidth', 2);

% Q3填充
q3_x = q3_norm .* cos(angles);
q3_y = q3_norm .* sin(angles);
patch([q3_x q3_x(1)], [q3_y q3_y(1)], [0.92 0.45 0.25], ...
      'FaceAlpha', 0.2, 'EdgeColor', [0.75 0.30 0.15], 'LineWidth', 2);

% 标注维度名
for i = 1:n_dim
    r = 1.15;
    text(r*cos(angles(i)), r*sin(angles(i)), dim_names{i}, ...
         'FontSize', 9, 'FontWeight', 'bold', ...
         'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle');
end

% 数值标注 (Q2在左, Q3在右)
for i = 1:n_dim
    r_q2 = q2_norm(i) + 0.06;
    r_q3 = q3_norm(i) + 0.06;
    if i == 5  % 补贴轴 Q2=0
        text(r_q2*cos(angles(i))-0.05, r_q2*sin(angles(i)), ...
             sprintf('Q2:%.1f', q2_vals(i)), 'FontSize', 8, 'Color', [0.20 0.35 0.60]);
    else
        text(r_q2*cos(angles(i)), r_q2*sin(angles(i)), ...
             sprintf('Q2:%.2f', q2_vals(i)), 'FontSize', 8, 'Color', [0.20 0.35 0.60]);
    end
    text(r_q3*cos(angles(i)), r_q3*sin(angles(i))-0.04, ...
         sprintf('Q3:%.2f', q3_vals(i)), 'FontSize', 8, 'Color', [0.75 0.30 0.15]);
end

hold off;
axis equal; axis off;

title('Q2 vs Q3 六维综合对比', 'FontSize', 15, 'FontWeight', 'bold');
legend({'Q2 (优化前)', 'Q3 (优化后)'}, 'Location', 'southoutside', ...
       'Orientation', 'horizontal', 'FontSize', 11, 'Box', 'off');

text(0, -1.3, '\rm 注: Q3补贴2.26M/年, Q2无补贴; 满意度从0.90降至0.82因S2利用率崩塌', ...
     'Units', 'data', 'FontSize', 9, 'Color', [0.45 0.45 0.45], ...
     'HorizontalAlignment', 'center');

exportgraphics(gcf, 'c:/Users/29845/Desktop/Q3图/图5_Q2vsQ3雷达图.png', 'Resolution', 300);
fprintf('雷达图 saved\n');
