% ============================================================
% Q3 方案C: 论文精选 (3张)
% 图C1: 定价+利润合并  图C2: 满意度分解  图C3: 可及性
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
subsidy   = [65.7,   65.7,   94.9];
fixed     = [116.8,  116.8,  160.6];
depr      = [1.6,    1.6,    2.3];
net_profit = revenue - direct + subsidy - fixed - depr;

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
% 图C1: 定价+利润 合并 (上下子图)
% ============================================================
figure('Position', [60, 60, 950, 750], 'Color', 'w', ...
       'ToolBar', 'none', 'MenuBar', 'none');
tiledlayout(2, 1, 'TileSpacing', 'compact', 'Padding', 'compact');

% 上: 定价对比
nexttile;
x = 1:5; w = 0.35;
hold on;
b1 = bar(x-w/2, benchmark, w, 'FaceColor', [0.30 0.50 0.75], 'EdgeColor', 'none');
b2 = bar(x+w/2, optimal,   w, 'FaceColor', [0.92 0.52 0.25], 'EdgeColor', 'none');
for i=1:5
    text(x(i)-w/2, benchmark(i)+0.6, sprintf('%.0f',benchmark(i)), 'FontSize',9,'FontWeight','bold','HorizontalAlignment','center','Color',[0.25 0.40 0.65]);
    text(x(i)+w/2, optimal(i)+0.6, sprintf('%.2f',optimal(i)), 'FontSize',9,'FontWeight','bold','HorizontalAlignment','center','Color',[0.80 0.40 0.15]);
    text(x(i), max(benchmark(i),optimal(i))+2, sprintf('↓%.0f%%',-drop_pct(i)), 'FontSize',8.5,'HorizontalAlignment','center','Color',[0.65 0.15 0.15],'FontWeight','bold');
end
% 基准线
plot([0.3 5.7], [0 0], 'k-');  % dummy
yline(0);
hold off;
set(gca,'XTick',x,'XTickLabel',services,'FontSize',11);
ylabel('元/次','FontSize',12,'FontWeight','bold');
title('(a) 最优定价 vs 基准价 — 五项服务全面降价14.3%','FontSize',13,'FontWeight','bold');
legend([b1 b2],{'基准价','最优定价'},'Location','northeast','FontSize',10,'Box','off');
grid on; ylim([0, 36]);

% 下: 利润构成
nexttile;
x2 = 1:3; w2 = 0.6;
hold on;
b_rev = bar(x2, revenue, w2, 'FaceColor', [0.35 0.65 0.40], 'EdgeColor', 'none');
b_dir = bar(x2, -direct, w2, 'FaceColor', [0.85 0.35 0.25], 'EdgeColor', 'none');
b_sub = bar(x2, subsidy, w2, 'FaceColor', [0.25 0.50 0.80], 'EdgeColor', 'none');
b_fix = bar(x2, -(fixed+depr), w2, 'FaceColor', [0.55 0.55 0.55], 'EdgeColor', 'none');

for i=1:3
    plot([x2(i)-w2/2 x2(i)+w2/2], [revenue(i) revenue(i)], 'k-', 'LineWidth', 0.5);
    text(x2(i), revenue(i)+subsidy(i)+8, sprintf('净%.1f万',net_profit(i)), ...
         'FontSize',10,'FontWeight','bold','HorizontalAlignment','center');
end
% 零线
plot([0.3 3.7], [0 0], 'k-', 'LineWidth', 1.2);
hold off;
set(gca,'XTick',x2,'XTickLabel',stations,'FontSize',11);
ylabel('万元/年','FontSize',12,'FontWeight','bold');
title('(b) 年度收支构成 — 补贴填补运营缺口, 保本微利','FontSize',13,'FontWeight','bold');
legend({'服务收入','直接支出','政府补贴','运营+折旧'},'Location','northeast','FontSize',10,'Box','off');
grid on;

sgtitle('Q3.2 定价优化与利润分析', 'FontSize', 16, 'FontWeight', 'bold');
exportgraphics(gcf, 'c:/Users/29845/Desktop/Q3图/图C1_定价与利润.png', 'Resolution', 300);
fprintf('C1 saved\n');

% ============================================================
% 图C2: 满意度分解 (同方案A图3, 但更精致)
% ============================================================
figure('Position', [80, 80, 1050, 560], 'Color', 'w', ...
       'ToolBar', 'none', 'MenuBar', 'none');

y_data = [s1_c; s2_c; s3_c]';
b_sat = bar(y_data, 'stacked', 'BarWidth', 0.65);
b_sat(1).FaceColor = [0.25 0.45 0.72]; b_sat(1).EdgeColor = 'none';
b_sat(2).FaceColor = [0.92 0.52 0.30]; b_sat(2).EdgeColor = 'none';
b_sat(3).FaceColor = [0.42 0.62 0.35]; b_sat(3).EdgeColor = 'none';

hold on;
for i=1:10
    text(i, tot_s(i)+0.013, sprintf('%.3f',tot_s(i)), 'FontSize',8.5,'FontWeight','bold','HorizontalAlignment','center');
    text(i, 0.03, ['\bf' sta_asgn{i}], 'FontSize',9,'HorizontalAlignment','center','Color',[1 1 1]);
    % 价格满意度标注 (S3列)
    if s3_c(i) > 0.45
        text(i, 0.65, 'S3=1.00', 'FontSize',7.5,'HorizontalAlignment','center','Color',[1 1 1]);
    end
end
hold off;

set(gca,'XTick',1:10,'XTickLabel',comm_names,'FontSize',11,'FontWeight','bold');
xlabel('小区','FontSize',12,'FontWeight','bold');
ylabel('满意度','FontSize',12,'FontWeight','bold');
title('各小区满意度分解 — S3(价格)满分  S2(利用率)拖累总分至0.82', 'FontSize',14,'FontWeight','bold');
ylim([0, 0.90]);
grid on; set(gca, 'GridAlpha', 0.1, 'GridLineStyle', '--'); box on;

legend({'S1 距离满意度 (权重0.2)', 'S2 利用率满意度 (权重0.3)', 'S3 价格满意度 (权重0.5)'}, ...
       'Location', 'southoutside', 'Orientation', 'horizontal', 'FontSize', 10, 'Box', 'off');

text(0.012, 0.985, '\bf 关键发现:\rm 全降价14.3%→S3=1.0满分, 但利用↑→S2=0.5崩塌, 总满意度比Q2的0.90下降约0.08', ...
     'Units', 'normalized', 'FontSize', 9, 'Color', [0.3 0.3 0.3], 'VerticalAlignment', 'top');

exportgraphics(gcf, 'c:/Users/29845/Desktop/Q3图/图C2_满意度分解.png', 'Resolution', 300);
fprintf('C2 saved\n');

% ============================================================
% 图C3: 可及性 (同方案A图4)
% ============================================================
figure('Position', [80, 80, 900, 560], 'Color', 'w', ...
       'ToolBar', 'none', 'MenuBar', 'none');
x = 1:3; w = 0.5;
c_t = [0.25 0.55 0.70; 0.92 0.55 0.25; 0.80 0.25 0.25];

yyaxis left; hold on;
for i=1:3
    bar(x(i), aff_pct(i), w, 'FaceColor', c_t(i,:), 'EdgeColor', 'none', 'FaceAlpha', 0.85);
    text(x(i), aff_pct(i)+3.5, sprintf('%.1f%%',aff_pct(i)), 'FontSize',12,'FontWeight','bold','HorizontalAlignment','center','Color',c_t(i,:));
end
ylabel('可负担比例 (%)','FontSize',12,'FontWeight','bold'); ylim([0, 118]); set(gca,'YColor',[0.2 0.2 0.2]);

yyaxis right;
plot(x, fulfill, 'ks-', 'LineWidth', 2.5, 'MarkerSize', 12, 'MarkerFaceColor', [0.1 0.1 0.1]);
for i=1:3
    text(x(i), fulfill(i)-1.2, sprintf('%.1f%%',fulfill(i)), 'FontSize',9,'FontWeight','bold','HorizontalAlignment','center');
end
ylabel('需求满足率 (%)','FontSize',12,'FontWeight','bold'); ylim([90, 102]); set(gca,'YColor',[0.1 0.1 0.1]);
hold off;

set(gca,'XTick',x,'XTickLabel',types,'FontSize',13,'FontWeight','bold');
xlabel('老人类型','FontSize',12,'FontWeight','bold');
title('三类老人服务可及性 — 定价与补贴未能弥补失能老人悬崖', 'FontSize',13,'FontWeight','bold');

for i=1:3
    text(x(i), 95.5-i*1.5, sprintf('%.0f人 | 日补贴%.2f元',pop_t(i),sub_day(i)*365/365), ...
         'FontSize',9,'HorizontalAlignment','center','Color',[0.4 0.4 0.4]);
end

annotation('textarrow', [0.65 0.62], [0.32 0.25], 'String', '\bf 失能: 仅37.4%可负担!', ...
           'FontSize', 11, 'Color', [0.75 0.1 0.1], 'HeadWidth', 8, 'HeadLength', 6);

legend({'可负担比例', '', '', '需求满足率'}, 'Location', 'northeast', 'FontSize', 10, 'Box', 'off');
grid on; box on;

exportgraphics(gcf, 'c:/Users/29845/Desktop/Q3图/图C3_可及性分析.png', 'Resolution', 300);
fprintf('C3 saved\n');
fprintf('===== 方案C完成 =====\n');
