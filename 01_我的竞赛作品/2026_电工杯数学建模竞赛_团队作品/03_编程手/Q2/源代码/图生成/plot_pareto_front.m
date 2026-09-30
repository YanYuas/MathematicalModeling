% ============================================================
% 问题二 Pareto前沿图 — MATLAB美化版
% 数据来源: q2_pareto_results.csv
% ============================================================
clear; close all; clc;

% ---- 读取数据 ----
data_dir = fileparts(mfilename('fullpath'));
if isempty(data_dir), data_dir = pwd; end
parent_dir = fileparts(data_dir);

csv_path = fullfile(parent_dir, '问题二最终结果', 'enum_pareto_results.csv');
out_dir = fullfile(parent_dir, '问题二图测试');
if ~exist(out_dir, 'dir'), mkdir(out_dir); end

% 动态读取CSV行数
fid = fopen(csv_path, 'r', 'n', 'UTF-8');
lines = {};
fgetl(fid);  % skip header
while ~feof(fid)
    line = fgetl(fid);
    if ischar(line) && ~isempty(line)
        lines{end+1} = line;
    end
end
fclose(fid);
n_rows = length(lines);

coverage_pct = zeros(n_rows, 1);
satisfaction = zeros(n_rows, 1);
labels = cell(n_rows, 1);
details = cell(n_rows, 1);

for i = 1:n_rows
    parts = strsplit(lines{i}, ',');
    coverage_pct(i) = str2double(parts{4}) * 100;
    satisfaction(i) = str2double(parts{5});
    labels{i} = parts{1};
    details{i} = parts{6};
end

% ---- 绘图 ----
figure('Position', [120, 120, 1000, 700], 'Color', 'w', ...
       'ToolBar', 'none', 'MenuBar', 'none');

sat_min = min(satisfaction);
sat_max = max(satisfaction);
n_cmap = 256;
hot_cmap = flipud(hot(n_cmap));

hold on;

% Pareto前沿连线
[coverage_sorted, idx_sort] = sort(coverage_pct);
sat_sorted = satisfaction(idx_sort);
plot(coverage_sorted, sat_sorted, '-', 'Color', [0.55 0.55 0.55], ...
     'LineWidth', 1.5, 'HandleVisibility', 'off');

% 散点 + 标签 (与点同Y高度, 不上下偏移)
dx_r = 1.5;   % 右侧标注偏移
dx_l = -1.5;  % 左侧标注偏移

for i = 1:n_rows
    t = (satisfaction(i) - sat_min) / (sat_max - sat_min);
    color_idx = max(1, min(n_cmap, round(t * (n_cmap - 1) + 1)));
    pt_color = hot_cmap(color_idx, :);
    scatter(coverage_pct(i), satisfaction(i), 160, pt_color, 'filled', ...
            'MarkerEdgeColor', [0.25 0.25 0.25], 'LineWidth', 1);

    % 标注方向: 默认右侧; 高密度尾部偶数位标左侧
    if i >= n_rows - 5 && mod(i, 2) == 0
        dx = dx_l;
        ha = 'right';
    else
        dx = dx_r;
        ha = 'left';
    end

    text(coverage_pct(i) + dx, satisfaction(i), labels{i}, ...
         'FontSize', 8.5, 'FontWeight', 'bold', ...
         'Color', [0.05 0.05 0.05], ...
         'HorizontalAlignment', ha, 'VerticalAlignment', 'middle');
end

% 最优高亮 P19 (最高覆盖率)
topsis_idx = 18;
scatter(coverage_pct(topsis_idx), satisfaction(topsis_idx), 280, ...
        'r', 'p', 'LineWidth', 2.2);

hold off;

% 坐标轴
xlabel('覆盖率 (%)', 'FontSize', 13, 'FontWeight', 'bold');
ylabel('满意度', 'FontSize', 13, 'FontWeight', 'bold');
title('Pareto 前沿：覆盖率 vs 满意度', 'FontSize', 15, 'FontWeight', 'bold');

xlim([35, 92]);
ylim([0.894, 0.992]);
grid on;
set(gca, 'GridAlpha', 0.2, 'FontSize', 11);
box on;

% 图例
legend({'非支配解', '最优方案 (P19)'}, ...
       'Location', 'southwest', 'FontSize', 10, 'Box', 'off');

% 左下信息
annotation('textbox', [0.145, 0.155, 0.28, 0.10], ...
    'String', sprintf('Pareto解: %d个\n覆盖率: %.1f%% – %.1f%%\n满意度: %.4f – %.4f', ...
    n_rows, min(coverage_pct), max(coverage_pct), ...
    min(satisfaction), max(satisfaction)), ...
    'FontSize', 9, 'Color', [0.35 0.35 0.35], ...
    'EdgeColor', [0.7 0.7 0.7], 'BackgroundColor', [1 1 1 0.7], ...
    'FitBoxToText', 'on');

% 保存
out_path = fullfile(out_dir, 'q2_pareto_front.png');
exportgraphics(gcf, out_path, 'Resolution', 300);
fprintf('已保存: %s\n', out_path);
fprintf('Pareto前沿共 %d 个解\n', n_rows);
