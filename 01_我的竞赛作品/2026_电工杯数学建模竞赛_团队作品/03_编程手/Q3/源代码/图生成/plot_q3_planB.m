% ============================================================
% Q3 方案B: 组合面板图 (2张)
% 图B1: 3.2综合 2×2面板 (定价+利润+满意度)  图B2: 3.3可及性
% ============================================================
clear; close all; clc;

% ---- 数据 ----
services = {'助餐','日间照料','上门护理','康复理疗','助浴'};
benchmark = [10, 20, 30, 28, 25];
optimal   = [8.57, 17.15, 25.72, 24.00, 21.43];
drop_pct = (optimal - benchmark) ./ benchmark * 100;

stations  = {'C(中型)','D(中型)','G(大型)'};
revenue   = [1033.6, 1029.2, 1535.1];
direct    = [980.9,  976.5,  1467.2];
gross     = [52.7,   52.7,   68.0];
subsidy   = [65.7,   65.7,   94.9];
fixed     = [116.8,  116.8,  160.6];
depr      = [1.6,    1.6,    2.3];

comm_names = {'B','C','G','A','D','H','E','F','I','J'};
sta_asgn   = {'C','C','C','D','D','D','G','G','G','G'};
s1_c = [0.120,0.200,0.180,0.120,0.200,0.200,0.180,0.180,0.180,0.150];
s2_c = repmat(0.150, 1, 10);
s3_c = repmat(0.500, 1, 10);
tot_s = [0.770,0.850,0.830,0.770,0.850,0.850,0.830,0.830,0.830,0.800];

types = {'自理','半失能','失能'};
aff_pct = [100.0, 93.1, 37.4];
fulfill = [100.0, 99.7, 93.7];
pop_t = [4981, 1471, 1125];
sub_day = [1.61, 3.12, 4.06];

% ============================================================
% 图B1: 3.2综合 2×2
% ============================================================
figure('Position', [30, 30, 1400, 900], 'Color', 'w', ...
       'ToolBar', 'none', 'MenuBar', 'none');
tiledlayout(2, 2, 'TileSpacing', 'compact', 'Padding', 'compact');

% 左上: 定价对比
nexttile;
x = 1:5; w = 0.32;
hold on;
b1 = bar(x-w/2, benchmark, w, 'FaceColor', [0.30 0.50 0.75], 'EdgeColor', 'none');
b2 = bar(x+w/2, optimal,   w, 'FaceColor', [0.92 0.52 0.25], 'EdgeColor', 'none');
for i=1:5
    text(x(i), max(benchmark(i),optimal(i))+1.5, sprintf('%.1f%%',drop_pct(i)), ...
         'FontSize',8,'HorizontalAlignment','center','Color',[0.6 0.2 0.2]);
end
hold off;
set(gca,'XTick',x,'XTickLabel',services,'FontSize',9);
ylabel('元/次','FontSize',10); title('(a) 最优定价 vs 基准价','FontSize',12,'FontWeight','bold');
legend([b1 b2],{'基准价','最优定价'},'FontSize',8,'Box','off');
grid on; ylim([0,35]);

% 右上: 利润瀑布 (单图汇总三站)
nexttile;
bar_data = [revenue', direct', subsidy', fixed'+depr'];
b_all = bar(bar_data, 'stacked');
b_all(1).FaceColor = [0.25 0.55 0.70];  % 收入
b_all(2).FaceColor = [0.85 0.35 0.25];  % 支出
b_all(3).FaceColor = [0.30 0.65 0.40];  % 补贴
b_all(4).FaceColor = [0.60 0.60 0.60];  % 成本
hold on;
for i=1:3
    net_val = revenue(i)-direct(i)+subsidy(i)-fixed(i)-depr(i);
    text(i, revenue(i)+subsidy(i)+5, sprintf('净利≈%.1f万',net_val), ...
         'FontSize',9,'FontWeight','bold','HorizontalAlignment','center');
end
hold off;
set(gca,'XTickLabel',stations,'FontSize',9);
ylabel('万元/年','FontSize',10); title('(b) 年度收支构成','FontSize',12,'FontWeight','bold');
legend({'服务收入','直接支出','政府补贴','运营+折旧'},'FontSize',8,'Box','off');
grid on;

% 下方: 满意度分解 (跨2列)
nexttile([1 2]);
y_data = [s1_c; s2_c; s3_c]';
b_sat = bar(y_data, 'stacked', 'BarWidth', 0.62);
b_sat(1).FaceColor = [0.25 0.45 0.72]; b_sat(1).EdgeColor = 'none';
b_sat(2).FaceColor = [0.92 0.52 0.30]; b_sat(2).EdgeColor = 'none';
b_sat(3).FaceColor = [0.42 0.62 0.35]; b_sat(3).EdgeColor = 'none';
hold on;
for i=1:10
    text(i, tot_s(i)+0.015, sprintf('%.3f',tot_s(i)), 'FontSize',8,'FontWeight','bold','HorizontalAlignment','center');
    text(i, 0.03, ['\bf' sta_asgn{i}], 'FontSize',8,'HorizontalAlignment','center','Color',[1 1 1]);
end
hold off;
set(gca,'XTick',1:10,'XTickLabel',comm_names,'FontSize',9);
ylabel('满意度','FontSize',10); title('(c) 各小区满意度分解  S1(距离)+S2(利用率)+S3(价格)','FontSize',12,'FontWeight','bold');
ylim([0,0.92]);
legend({'S1距离(0.2)','S2利用率(0.3)','S3价格(0.5)'},'Location','southoutside','Orientation','horizontal','FontSize',9,'Box','off');
grid on;

sgtitle('Q3.2 定价优化综合结果', 'FontSize', 16, 'FontWeight', 'bold');
exportgraphics(gcf, 'c:/Users/29845/Desktop/Q3图/图B1_3.2综合面板.png', 'Resolution', 300);
fprintf('B1 saved\n');

% ============================================================
% 图B2: 3.3 可及性 (同方案A图4, 单独)
% ============================================================
figure('Position', [80, 80, 900, 560], 'Color', 'w', ...
       'ToolBar', 'none', 'MenuBar', 'none');
x = 1:3; w = 0.5;
c_t = [0.25 0.55 0.70; 0.92 0.55 0.25; 0.80 0.25 0.25];

yyaxis left; hold on;
for i=1:3
    bar(x(i), aff_pct(i), w, 'FaceColor', c_t(i,:), 'EdgeColor', 'none', 'FaceAlpha', 0.85);
    text(x(i), aff_pct(i)+3, sprintf('%.1f%%',aff_pct(i)), 'FontSize',11,'FontWeight','bold','HorizontalAlignment','center','Color',c_t(i,:));
end
ylabel('可负担比例 (%)','FontSize',12); ylim([0,115]); set(gca,'YColor',[0.2 0.2 0.2]);

yyaxis right;
plot(x, fulfill, 'ko-', 'LineWidth', 2.5, 'MarkerSize', 12, 'MarkerFaceColor', [0.15 0.15 0.15]);
for i=1:3
    text(x(i), fulfill(i)-1.5, sprintf('%.1f%%',fulfill(i)), 'FontSize',9,'FontWeight','bold','HorizontalAlignment','center');
end
ylabel('需求满足率 (%)','FontSize',12); ylim([90,102]); set(gca,'YColor',[0.15 0.15 0.15]);
hold off;

set(gca,'XTick',x,'XTickLabel',types,'FontSize',12,'FontWeight','bold');
title('三类老人服务可及性 — 失能老人仅37.4%可负担','FontSize',14,'FontWeight','bold');
for i=1:3
    text(x(i), 95-i*2, sprintf('%.0f人 | 补贴%.0f元/年',pop_t(i),sub_day(i)*365), ...
         'FontSize',8.5,'HorizontalAlignment','center','Color',[0.45 0.45 0.45]);
end
text(3, 38, '\bf ← 悬崖式落差!','FontSize',11,'Color',[0.7 0.15 0.15],'HorizontalAlignment','center');
grid on; box on;

exportgraphics(gcf, 'c:/Users/29845/Desktop/Q3图/图B2_3.3可及性.png', 'Resolution', 300);
fprintf('B2 saved\n');
fprintf('===== 方案B完成 =====\n');
