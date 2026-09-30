%% 图4：全区域服务需求占比（环形图）
clear; clc; close all;

% --- 数据 ---
services = {'助餐','日间照料','上门护理','康复理疗','助浴','紧急救助'};

N5 = [
    521, 150, 114;
    436, 130, 106;
    669, 199, 150;
    391, 115,  94;
    567, 168, 129;
    345, 101,  74;
    626, 185, 142;
    413, 123,  91;
    533, 159, 120;
    480, 141, 105;
];

demand_pp = [
    14,    20,  22;
    8,     14,  18;
    0,      6,  12;
    2,      4,   6;
    0,      2,   4;
    0.15,   1,   3;
];

svc_totals = zeros(1, 6);
for k = 1:6
    for i = 1:10
        svc_totals(k) = svc_totals(k) + sum(N5(i,:) .* demand_pp(k,:));
    end
end

[svc_totals, idx] = sort(svc_totals, 'descend');
services = services(idx);
total = sum(svc_totals);

% --- 配色（6种低饱和度专业色） ---
colors = [
    0.85 0.33 0.30;   % 红 — 助餐
    0.96 0.65 0.20;   % 橙 — 日间照料
    0.20 0.55 0.75;   % 蓝 — 康复护理
    0.35 0.65 0.35;   % 绿 — 健康管理
    0.60 0.45 0.70;   % 紫 — 助浴
    0.50 0.50 0.50;   % 灰 — 精神慰藉
];

% --- 环形图 ---
figure('Position', [100, 100, 900, 600], 'Color', 'w');
p = pie(svc_totals);
title(sprintf('全区域理论月服务需求占比（总计 %.0f 次/月）', total), ...
    'FontSize', 14, 'FontWeight', 'bold');

% 上色
patches = findobj(p, 'Type', 'Patch');
for k = 1:length(patches)
    patches(k).FaceColor = colors(k, :);
    patches(k).EdgeColor = 'w';
    patches(k).LineWidth = 1.5;
end

% 标签改百分比（字体加大）
texts = findobj(p, 'Type', 'Text');
for i = 1:length(texts)
    texts(i).FontSize = 14;
    texts(i).FontWeight = 'bold';
    texts(i).Color = [0.25 0.25 0.25];
end

% 图例（服务名换行 + 数值）
lgd_labels = cell(1,6);
for k = 1:6
    lgd_labels{k} = sprintf('%s\n%.0f 次/月 (%.1f%%)', ...
        services{k}, svc_totals(k), svc_totals(k)/total*100);
end
lgd = legend(lgd_labels, 'Location', 'eastoutside', 'FontSize', 11, 'Box', 'off');
title(lgd, '服务项目', 'FontSize', 11);

saveas(gcf, '图4_服务需求占比.png');
fprintf('图4 已保存\n');
