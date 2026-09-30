% ============================================================
% Q3.2 图2: 年度利润瀑布图 (按站)
% 数据: Q3表格_年度利润.csv
% ============================================================
clear; close all; clc;

stations  = {'C(中型)','D(中型)','G(大型)'};
revenue   = [10335602, 10292154, 15351228] / 10000;  % 万元
direct    = [9808602,  9765145, 14671728] / 10000;
gross     = [527000,   527009,  679500]   / 10000;
subsidy   = [657000,   657000,  949000]   / 10000;
fixed     = [1168000,  1168000, 1606000]  / 10000;
depr      = [16000,    16000,   22500]    / 10000;
net_profit = [0, 9, 0] / 10000;

% 瀑布数据
c_pos  = [0.22 0.62 0.42];  % 正向 绿
c_neg  = [0.85 0.30 0.25];  % 负向 红
c_sub  = [0.25 0.50 0.80];  % 补贴 蓝
c_net  = [0.15 0.15 0.15];  % 净利润 深灰

figure('Position', [80, 80, 1000, 520], 'Color', 'w', ...
       'ToolBar', 'none', 'MenuBar', 'none');

for s_idx = 1:3
    subplot(1, 3, s_idx);

    rev = revenue(s_idx);
    dir_v = direct(s_idx);
    gr = gross(s_idx);
    sub_v = subsidy(s_idx);
    fix_v = fixed(s_idx);
    dep = depr(s_idx);
    net = net_profit(s_idx);

    x_pos = [1, 2, 3, 4, 5, 6];
    bar_values = [rev, -dir_v, gr, sub_v, -fix_v, -dep];

    hold on;
    for i = 1:6
        val = bar_values(i);
        if val >= 0
            if i == 4  % subsidy
                clr = c_sub;
            else
                clr = c_pos;
            end
        else
            clr = c_neg;
        end
        bar(x_pos(i), val, 0.55, 'FaceColor', clr, 'EdgeColor', 'none');

        if abs(val) > 0.5
            text(x_pos(i), val + sign(val)*3, sprintf('%.0f', abs(val)), ...
                 'FontSize', 8.5, 'FontWeight', 'bold', ...
                 'HorizontalAlignment', 'center');
        end
    end

    % 累积线
    cumsum_vals = [0, rev, rev-dir_v, rev-dir_v, rev-dir_v+sub_v, rev-dir_v+sub_v];
    for i = 2:6
        plot([x_pos(i-1) x_pos(i)], [cumsum_vals(i-1) cumsum_vals(i)], ...
             'k-', 'LineWidth', 1.5);
    end
    % 最终净利润
    plot(x_pos(6), cumsum_vals(6)-fix_v-dep, 'ko', 'MarkerSize', 10, 'MarkerFaceColor', c_net);

    hold off;

    set(gca, 'XTick', x_pos, 'XTickLabel', ...
         {'收入','支出','毛利','补贴','运营','折旧'}, ...
         'FontSize', 8.5, 'XTickLabelRotation', 30);
    ylabel('万元', 'FontSize', 10);
    title(sprintf('%s站 净利≈%.0f万', stations{s_idx}, net), ...
          'FontSize', 12, 'FontWeight', 'bold');
    grid on; set(gca, 'GridAlpha', 0.1); box on;
end

sgtitle('各站年度利润构成 (万元)', 'FontSize', 15, 'FontWeight', 'bold');

out_path = 'c:/Users/29845/Desktop/Q3图/图2_年度利润瀑布图.png';
exportgraphics(gcf, out_path, 'Resolution', 300);
fprintf('已保存: %s\n', out_path);
