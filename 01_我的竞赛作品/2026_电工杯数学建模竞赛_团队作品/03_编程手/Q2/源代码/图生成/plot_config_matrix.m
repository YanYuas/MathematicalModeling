% ============================================================
% 问题二 站点配置矩阵 (美化版)
% 数据: q2_pareto_results.csv
% 风格: 暖色系, 专业学术
% ============================================================
clear; close all; clc;

data_dir = fileparts(mfilename('fullpath'));
if isempty(data_dir), data_dir = pwd; end
parent_dir = fileparts(data_dir);
csv_path = fullfile(parent_dir, '问题二最终结果', 'enum_pareto_results.csv');
out_dir = fullfile(parent_dir, '问题二图测试');
if ~exist(out_dir, 'dir'), mkdir(out_dir); end

% ---- 读取 ----
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

comm_names = {'A','B','C','D','E','F','G','H','I','J'};
scale_names = {'小型','中型','大型'};
config_matrix = zeros(n_rows, 10);

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

% ---- 暖色配色 (对标热力图风格) ----
% 无站: 浅灰白, 小: 淡黄, 中: 暖橙, 大: 深红
cell_colors = [
    0.96 0.96 0.95;   % 无站 米白
    1.00 0.89 0.55;   % 小型 淡金黄
    1.00 0.65 0.30;   % 中型 暖橙
    0.85 0.35 0.25;   % 大型 深砖红
];

figure('Position', [80, 80, 1060, 850], 'Color', 'w', ...
       'ToolBar', 'none', 'MenuBar', 'none');

imagesc(config_matrix, [0, 3]);
colormap(gca, cell_colors);
hold on;

% 细网格线 (浅灰, 不抢眼)
for x = 0.5:1:10.5
    plot([x x], [0.5 n_rows+0.5], 'Color', [0.85 0.85 0.85], 'LineWidth', 0.8);
end
for y = 0.5:1:(n_rows+0.5)
    plot([0.5 10.5], [y y], 'Color', [0.85 0.85 0.85], 'LineWidth', 0.8);
end

% 站规模文字
scale_txt = {'', '小', '中', '大'};
txt_colors = {[], [0.25 0.25 0.25], [1 1 1], [1 1 1]};
for i = 1:n_rows
    for j = 1:10
        val = config_matrix(i, j);
        if val > 0
            text(j, i, scale_txt{val+1}, 'FontSize', 8.5, 'FontWeight', 'bold', ...
                 'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle', ...
                 'Color', txt_colors{val+1});
        end
    end
end

% 方案指标 (右)
for i = 1:n_rows
    info_str = sprintf('C=%.1f%%  S=%.4f  %d站 %d万', ...
                       coverage_pct(i), satisfaction(i), n_stations(i), costs(i));
    text(10.7, i, info_str, 'FontSize', 7.5, ...
         'HorizontalAlignment', 'left', 'VerticalAlignment', 'middle', ...
         'Color', [0.25 0.25 0.25]);
end

% 最优行标记 (枚举P19)
topsis_row = 19;
% 浅色行高亮
patch([0.3 10.6 10.6 0.3], ...
      [topsis_row-0.5 topsis_row-0.5 topsis_row+0.5 topsis_row+0.5], ...
      [1 0.85 0.75], 'FaceAlpha', 0.15, 'EdgeColor', 'none');
% 右侧星标
text(10.55, topsis_row, '\bf\ast', 'FontSize', 16, 'Color', [0.8 0.25 0.15], ...
     'HorizontalAlignment', 'center', 'VerticalAlignment', 'middle');

hold off;

set(gca, 'XTick', 1:10, 'XTickLabel', comm_names, ...
         'YTick', 1:n_rows, 'YTickLabel', labels, ...
         'FontSize', 10, 'YDir', 'reverse', 'TickLength', [0 0]);
xlabel('小区', 'FontSize', 12, 'FontWeight', 'bold');
ylabel('方案', 'FontSize', 12, 'FontWeight', 'bold');
title('Pareto最优方案 — 站点选址与规模配置', 'FontSize', 15, 'FontWeight', 'bold');

% 图例
hold on;
leg_items = [];
for k = 1:3
    leg_items(k) = plot(nan, nan, 's', 'MarkerSize', 14, ...
                        'MarkerFaceColor', cell_colors(k+1,:), ...
                        'MarkerEdgeColor', [0.5 0.5 0.5]);
end
legend(leg_items, {'小型(18万/1000人日)', '中型(32万/2000人日)', '大型(45万/3000人日)'}, ...
       'Location', 'southoutside', 'Orientation', 'horizontal', ...
       'FontSize', 9, 'Box', 'off');
hold off;

% 保存
out_path = fullfile(out_dir, 'q2_config_matrix.png');
exportgraphics(gcf, out_path, 'Resolution', 300);
fprintf('已保存: %s\n', out_path);
