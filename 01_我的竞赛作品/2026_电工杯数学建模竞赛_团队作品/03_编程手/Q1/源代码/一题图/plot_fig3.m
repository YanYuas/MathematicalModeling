%% 图3：小区 × 服务理论月需求热力图
clear; clc; close all;

% --- 数据 ---
communities = {'A','B','C','D','E','F','G','H','I','J'};
services = {'助餐','日间照料','上门护理','康复理疗','助浴','紧急救助'};

N5 = [    % 自理, 半失能, 失能
    521, 150, 114;  % A
    436, 130, 106;  % B
    669, 199, 150;  % C
    391, 115,  94;  % D
    567, 168, 129;  % E
    345, 101,  74;  % F
    626, 185, 142;  % G
    413, 123,  91;  % H
    533, 159, 120;  % I
    480, 141, 105;  % J
];

demand_pp = [    % 自理, 半失能, 失能
    14,    20,  22;   % 助餐
    8,     14,  18;   % 日间照料
    0,      6,  12;   % 康复护理
    2,      4,   6;   % 健康管理
    0,      2,   4;   % 助浴
    0.15,   1,   3;   % 精神慰藉
];

% 计算理论需求 (10×6)
demand = zeros(10, 6);
for i = 1:10
    for k = 1:6
        demand(i,k) = sum(N5(i,:) .* demand_pp(k,:));
    end
end

% --- 绘图 ---
fig = figure('Position', [100, 100, 900, 500]);
h = heatmap(services, flipud(communities'), round(flipud(demand)));
h.Title = '';
h.XLabel = '服务项目';
h.YLabel = '小区';
h.Colormap = flipud(hot);
h.CellLabelFormat = '%d';
h.ColorLimits = [0, 18000];
h.FontSize = 11;

% 保存
saveas(gcf, '图3_需求热力图.png');
fprintf('图3 已保存\n');
