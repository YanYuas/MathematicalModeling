% ============================================================
% 问题二 综合结果图：Pareto前沿 + 站点配置矩阵
% 数据来源: q2_pareto_results.csv
% ============================================================
clear; close all; clc;

% ---- 路径 ----
data_dir = fileparts(mfilename('fullpath'));
if isempty(data_dir), data_dir = pwd; end
parent_dir = fileparts(data_dir);
csv_path = fullfile(parent_dir, '问题二最终结果', 'enum_pareto_results.csv');
out_dir = fullfile(parent_dir, '问题二图测试');
if ~exist(out_dir, 'dir'), mkdir(out_dir); end

% ---- 读取CSV ----
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
n_stations = zeros(n_rows, 1);
costs = zeros(n_rows, 1);
details = cell(n_rows, 1);

for i = 1:n_rows
    parts = strsplit(lines{i}, ',');
    coverage_pct(i) = str2double(parts{4}) * 100;
    satisfaction(i) = str2double(parts{5});
    n_stations(i) = str2double(parts{2});
    costs(i) = str2double(parts{3});
    labels{i} = parts{1};
    details{i} = parts{6};
end

% ---- 解析站点配置矩阵 (14方案 × 10小区) ----
comm_names = {'A','B','C','D','E','F','G','H','I','J'};
scale_names = {'小型','中型','大型'};
config_matrix = zeros(n_rows, 10);  % 0=无站, 1=小, 2=中, 3=大

for i = 1:n_rows
    parts = strsplit(details{i}, '-');
    for p = 1:length(parts)
        token = parts{p};
        comm_idx = find(strcmp(comm_names, token(1)));
        for s = 1:3
            if contains(token, scale_names{s})
                config_matrix(i, comm_idx) = s;
                break;
            end
        end
    end
end

% ---- 配色 ----
hot_cmap = flipud(hot(256));
config_colors = [1 1 1; 0.65 0.82 1.00; 1.00 0.73 0.42; 0.91 0.45 0.45];  % 无/小/中/大

% ============================================================
% 主图
% ============================================================
figure('Position', [50, 50, 1500, 950], 'Color', 'w', ...
       'ToolBar', 'none', 'MenuBar', 'none');
tiledlayout(1, 2, 'TileSpacing', 'compact', 'Padding', 'compact');

% ---- 左面板: Pareto前沿 ----
nexttile;
sat_min = min(satisfaction);
sat_max = max(satisfaction);
hold on;

[coverage_sorted, idx_sort] = sort(coverage_pct);
plot(coverage_sorted, satisfaction(idx_sort), '-', ...
     'Color', [0.55 0.55 0.55], 'LineWidth', 1.5, 'HandleVisibility', 'off');

for i = 1:n_rows
    t = (satisfaction(i) - sat_min) / (sat_max - sat_min);
    color_idx = max(1, min(256, round(t * 255 + 1)));
    pt_color = hot_cmap(color_idx, :);
    scatter(coverage_pct(i), satisfaction(i), 150, pt_color, 'filled', ...
            'MarkerEdgeColor', [0.25 0.25 0.25], 'LineWidth', 1);
end

dx_r = 1.5; dx_l = -1.5;
for i = 1:n_rows
    if i >= n_rows - 5 && mod(i, 2) == 0
        dx = dx_l; ha = 'right';
    else
        dx = dx_r; ha = 'left';
    end
    text(coverage_pct(i) + dx, satisfaction(i), labels{i}, ...
         'FontSize', 8.5, 'FontWeight', 'bold', ...
         'HorizontalAlignment', ha, 'VerticalAlignment', 'middle');
end

% 最优 P19 (最高覆盖率)
scatter(coverage_pct(19), satisfaction(19), 260, 'r', 'p', 'LineWidth', 2.2);

hold off;
xlabel('覆盖率 (%)', 'FontSize', 12, 'FontWeight', 'bold');
ylabel('满意度', 'FontSize', 12, 'FontWeight', 'bold');
title('Pareto 前沿', 'FontSize', 14, 'FontWeight', 'bold');
xlim([35, 92]); ylim([0.894, 0.992]);
grid on; set(gca, 'GridAlpha', 0.2, 'FontSize', 10); box on;
legend({'非支配解', '最优方案 (P19)'}, 'Location', 'southwest', 'FontSize', 9, 'Box', 'off');

% ---- 右面板: 站点配置矩阵 ----
nexttile;
imagesc(config_matrix, [0, 3]);
colormap(gca, config_colors);
hold on;

% 网格线
for x = 0.5:1:10.5
    plot([x x], [0.5 n_rows+0.5], 'k', 'LineWidth', 0.3);
end
for y = 0.5:1:(n_rows+0.5)
    plot([0.5 10.5], [y y], 'k', 'LineWidth', 0.3);
end

% 站规模标注
scale_symbols = {'', '小', '中', '大'};
for i = 1:n_rows
    for j = 1:10
        val = config_matrix(i, j);
        if val > 0
            if val == 1, clr = [0 0 0];
            else, clr = [1 1 1]; end
            text(j, i, scale_symbols{val+1}, ...
                 'FontSize', 7.5, 'FontWeight', 'bold', ...
                 'HorizontalAlignment', 'center', ...
                 'VerticalAlignment', 'middle', 'Color', clr);
        end
    end
end

% 右侧标注: 覆盖率 + 满意度 + 站点数
for i = 1:n_rows
    text(10.8, i, sprintf('%s  %.1f%%  S=%.3f  %d站%d万', ...
         labels{i}, coverage_pct(i), satisfaction(i), n_stations(i), costs(i)), ...
         'FontSize', 7.5, 'HorizontalAlignment', 'left', ...
         'VerticalAlignment', 'middle');
end

hold off;
set(gca, 'XTick', 1:10, 'XTickLabel', comm_names, ...
         'YTick', 1:n_rows, 'YTickLabel', labels, ...
         'FontSize', 9, 'YDir', 'reverse', 'TickLength', [0 0], ...
         'XAxisLocation', 'top');
xlabel('小区', 'FontSize', 11, 'FontWeight', 'bold');
ylabel('方案', 'FontSize', 11, 'FontWeight', 'bold');
title('站点配置矩阵 (小/中/大 = 站规模)', 'FontSize', 14, 'FontWeight', 'bold');

% ---- 保存 ----
out_path = fullfile(out_dir, 'q2_comprehensive.png');
exportgraphics(gcf, out_path, 'Resolution', 300);
fprintf('已保存: %s\n', out_path);
