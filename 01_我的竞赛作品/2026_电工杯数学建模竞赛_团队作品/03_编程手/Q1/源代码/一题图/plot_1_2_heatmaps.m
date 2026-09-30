% ============================================================
% 问题1.2：三类老人 × 服务 × 小区 需求热力图（3张）
% 配色：白→黄→红→黑（hot反转）
% ============================================================
clear; close all; clc;

% ---- 第5年末各小区老人数 (问题1.1结果) ----
N5 = [
    521, 150, 114;   % A
    436, 130, 106;   % B
    669, 199, 150;   % C
    391, 115,  94;   % D
    567, 168, 129;   % E
    345, 101,  74;   % F
    626, 185, 142;   % G
    413, 123,  91;   % H
    533, 159, 120;   % I
    480, 141, 105;   % J
];

% ---- 每老人月均服务需求 (行=服务, 列=[自理,半失能,失能]) ----
demand_pp = [
    14,    20,  22;     % 助餐
     8,    14,  18;     % 日间照料
     0,     6,  12;     % 上门护理
     2,     4,   6;     % 康复理疗
     0,     2,   4;     % 助浴
     0.15,  1,   3;     % 紧急救助
];

communities = {'A','B','C','D','E','F','G','H','I','J'};
services = {'助餐','日间照料','上门护理','康复理疗','助浴','紧急救助'};
types_cn = {'自理老人','半失能老人','失能老人'};

n_comm = 10;
n_svc = 6;

% ---- 计算 10×6×3 需求张量 ----
D = zeros(n_comm, n_svc, 3);
for j = 1:3
    D(:, :, j) = N5(:, j) * demand_pp(:, j)';
end

% ---- 白→黄→红→黑 (hot反转) ----
cmap = flipud(hot(256));

% ---- 3张热力图 ----
out_dir = fileparts(mfilename('fullpath'));
if isempty(out_dir), out_dir = pwd; end

for j = 1:3
    figure('Position', [50 + (j-1)*550, 150, 520, 620], ...
           'Color', 'w', 'ToolBar', 'none', 'MenuBar', 'none');

    data = D(:, :, j);
    vmin = 0;
    vmax = max(data(:));

    imagesc(data, [vmin, vmax]);
    colormap(gca, cmap);
    hold on;

    % 网格线
    for x = 0.5:1:(n_svc+0.5)
        plot([x x], [0.5 n_comm+0.5], 'w', 'LineWidth', 1.5);
    end
    for y = 0.5:1:(n_comm+0.5)
        plot([0.5 n_svc+0.5], [y y], 'w', 'LineWidth', 1.5);
    end

    % 数值标注
    for i = 1:n_comm
        for k = 1:n_svc
            val = data(i, k);
            if val > vmax * 0.45
                clr = [1 1 1];   % 深色背景用白字
            else
                clr = [0 0 0];   % 浅色背景用黑字
            end
            text(k, i, sprintf('%.0f', val), ...
                'HorizontalAlignment', 'center', ...
                'VerticalAlignment', 'middle', ...
                'FontSize', 9, 'FontWeight', 'bold', 'Color', clr);
        end
    end
    hold off;

    set(gca, 'XTick', 1:n_svc, 'XTickLabel', services, ...
             'YTick', 1:n_comm, 'YTickLabel', communities, ...
             'FontSize', 10, 'YDir', 'normal', ...
             'TickLength', [0 0]);
    xlabel('服务类型', 'FontSize', 12);
    ylabel('小区', 'FontSize', 12);
    title(sprintf('%s 月服务需求 (次/月)', types_cn{j}), ...
          'FontSize', 14, 'FontWeight', 'bold');

    cb = colorbar('eastoutside');
    cb.FontSize = 10;
    ylabel(cb, '次/月', 'FontSize', 11);

    fname = fullfile(out_dir, sprintf('热力图_%s.png', types_cn{j}));
    exportgraphics(gcf, fname, 'Resolution', 200);
    fprintf('已保存: %s\n', fname);
end

% ---- 汇总 ----
fprintf('\n各类型需求汇总 (次/月):\n');
for j = 1:3
    fprintf('  %s: %.0f\n', types_cn{j}, sum(D(:,:,j), 'all'));
end
fprintf('  总计: %.0f\n', sum(D(:), 'all'));
fprintf('\n===== 问题1.2 热力图全部完成 =====\n');
