%% Q1 主图修正版（图2 / 图4）——全部数值实时计算，替换硬编码错误坐标
%  修正要点：
%    旧版图2/图4 使用 vertices = [(299.127,499.237) ...]，区域尺寸仅 1.745 x 2.526 m，
%    与标注 D = 39.598 m 自相矛盾（旧"直径"线段实际只有 3.07 m）。
%    本脚本由 q1_geo 内核现算真实顶点：D = 39.5983 m, R_MEC = 19.7992 m, gamma = 1.000000。
clear; clc; close all;
addpath(pwd);

C.ink      = [28 28 28]/255;
C.slate    = [91 107 115]/255;
C.paper    = [247 244 238]/255;
C.field    = [197 212 224]/255;
C.geometry = [44 74 110]/255;
C.ochre    = [196 123 43]/255;
C.rust     = [140 58 42]/255;
C.sage     = [79 111 92]/255;
set(0,'DefaultAxesFontName','Microsoft YaHei');
set(0,'DefaultTextFontName','Microsoft YaHei');
set(0,'DefaultAxesFontSize',10);

outdir = fullfile(pwd,'..','实验结果','figs');
if ~exist(outdir,'dir'), mkdir(outdir); end

%% ---------------- 基准算例（与论文一致） ----------------
S1 = [0 0];  S2 = [600 0];  G = [300 500];  epsDeg = 1;
[poly, bounded, isEmpty] = q1_geo('regionFromSource', [S1; S2], G, epsDeg);
assert(~isEmpty && bounded, '基准算例区域应为有界非空');
[D, R, cen, gamma] = q1_geo('polyStats', poly);
[dmax, ip, jq] = pairMax_(poly);
fprintf('基准算例：顶点数 %d, D = %.6f m, R_MEC = %.6f m, 圆心 (%.4f, %.4f), gamma = %.6f\n', ...
        size(poly,1), D, R, cen(1), cen(2), gamma);
fprintf('  顶点坐标：\n');
for i = 1:size(poly,1), fprintf('    V%d = (%.4f, %.4f)\n', i, poly(i,1), poly(i,2)); end
fprintf('  直径对：V%d(%.3f,%.3f) - V%d(%.3f,%.3f)\n', ip, poly(ip,1), poly(ip,2), jq, poly(jq,1), poly(jq,2));
fprintf('  Jung 检验：D/2 = %.6f <= R_MEC = %.6f <= D/sqrt(3) = %.6f -> %d\n', ...
        D/2, R, D/sqrt(3), (D/2 - 1e-9 <= R) && (R <= D/sqrt(3) + 1e-9));

%% ============ 图2（修正版）：两站交会定位区域构造 ============
fig = figure('Position',[80 80 1220 560],'Color',C.paper,'PaperPositionMode','auto');

% ---- (a) 全局几何 ----
ax1 = subplot(1,2,1); set(ax1,'Color',C.paper); hold(ax1,'on');
Rw = 700;
for s = 1:2
    if s == 1, S = S1; else, S = S2; end
    T = G;
    b = atan2(T(2)-S(2), T(1)-S(1));
    aa = linspace(b-epsDeg*pi/180, b+epsDeg*pi/180, 60);
    xs = [S(1), S(1)+Rw*cos(aa), S(1)];
    ys = [S(2), S(2)+Rw*sin(aa), S(2)];
    patch(xs, ys, C.field, 'FaceAlpha',0.55,'EdgeColor','none');
    for sg = [-1 1]
        plot(ax1,[S(1) S(1)+Rw*cos(b+sg*epsDeg*pi/180)],[S(2) S(2)+Rw*sin(b+sg*epsDeg*pi/180)],'--','Color',C.geometry,'LineWidth',1.1);
    end
end
plot(ax1,[S1(1) G(1)],[S1(2) G(2)],':','Color',C.slate,'LineWidth',1);
plot(ax1,[S2(1) G(1)],[S2(2) G(2)],':','Color',C.slate,'LineWidth',1);
plot(ax1,poly([1:end 1],1),poly([1:end 1],2),'-','Color',C.rust,'LineWidth',3);
plot(ax1,S1(1),S1(2),'s','MarkerSize',11,'MarkerFaceColor',C.geometry,'MarkerEdgeColor',C.ink);
plot(ax1,S2(1),S2(2),'s','MarkerSize',11,'MarkerFaceColor',C.geometry,'MarkerEdgeColor',C.ink);
plot(ax1,G(1),G(2),'p','MarkerSize',16,'MarkerFaceColor',C.rust,'MarkerEdgeColor',C.ink);
text(ax1,10,-60,'S_1 (0, 0)','Color',C.ink,'FontSize',11);
text(ax1,545,-60,'S_2 (600, 0)','Color',C.ink,'FontSize',11);
text(ax1,345,560,'真源 G (300, 500)','Color',C.rust,'FontSize',11,'FontWeight','bold');
plot(ax1,[318 342],[508 552],'-','Color',C.rust,'LineWidth',0.8);
text(ax1,345,430,{'定位区域 L（40 m 量级）','放大见 (b)'},'Color',C.rust,'FontSize',10,'FontWeight','bold');
plot(ax1,[330 318],[452 488],'-','Color',C.rust,'LineWidth',0.8);
text(ax1,80,300,'角域 W_1（2epsilon = 2°）','Color',C.geometry,'FontSize',10);
text(ax1,400,205,'角域 W_2','Color',C.geometry,'FontSize',10);
xlim(ax1,[-130 760]); ylim(ax1,[-130 700]); axis(ax1,'equal');
xlabel(ax1,'X 坐标 (m)'); ylabel(ax1,'Y 坐标 (m)');
title(ax1,'(a) 两站交会全局几何（真实比例）','FontSize',13,'FontWeight','bold');
grid(ax1,'on'); set(ax1,'GridAlpha',0.15); box(ax1,'on');

% ---- (b) 区域放大 ----
ax2 = subplot(1,2,2); set(ax2,'Color',C.paper); hold(ax2,'on');
patch(poly(:,1),poly(:,2),C.field,'FaceAlpha',0.45,'EdgeColor','none');
% 边界射线（沿多边形各边方向延伸，展示 θ±1° 边界）
for i = 1:size(poly,1)
    A = poly(i,:); B = poly(mod(i,size(poly,1))+1,:);
    u = (B-A)/norm(B-A);
    plot(ax2,[A(1)-45*u(1) B(1)+45*u(1)],[A(2)-45*u(2) B(2)+45*u(2)],'-','Color',C.geometry,'LineWidth',1.2);
end
th = linspace(0,2*pi,400);
plot(ax2,cen(1)+R*cos(th), cen(2)+R*sin(th),'--','Color',C.sage,'LineWidth',2);
plot(ax2,[poly(ip,1) poly(jq,1)],[poly(ip,2) poly(jq,2)],'-','Color',C.ochre,'LineWidth',3.2);
plot(ax2,poly(ip,1),poly(ip,2),'o','MarkerSize',8,'MarkerFaceColor',C.ochre,'MarkerEdgeColor',C.ink);
plot(ax2,poly(jq,1),poly(jq,2),'o','MarkerSize',8,'MarkerFaceColor',C.ochre,'MarkerEdgeColor',C.ink);
plot(ax2,cen(1),cen(2),'+','MarkerSize',13,'LineWidth',2,'Color',C.sage);
plot(ax2,G(1),G(2),'p','MarkerSize',15,'MarkerFaceColor',C.rust,'MarkerEdgeColor',C.ink);
for i = 1:size(poly,1)
    text(ax2,poly(i,1)+0.7,poly(i,2)+0.8,sprintf('V%d (%.3f, %.3f)',i,poly(i,1),poly(i,2)),'FontSize',8.6,'Color',C.ink);
end
text(ax2,300-40,500.6,sprintf('真源 G\n(300.000, 500.000)'),'FontSize',9,'Color',C.rust,'FontWeight','bold');
text(ax2,300+1.2,(poly(ip,2)+poly(jq,2))/2,sprintf('D = %.3f m',D),'FontSize',11,'Color',C.ochre,'FontWeight','bold');
text(ax2,276.2,473.0,{'最小包围圆（虚线）','R_{MEC} = 19.799 m','\gamma = 1.000000（下界取等）'}, ...
     'FontSize',9,'Color',C.sage,'FontWeight','bold','BackgroundColor','w','EdgeColor',C.sage,'Margin',4, ...
     'VerticalAlignment','bottom');
text(ax2,276.2,527.0,{'四条实线为 	heta_1pm1°、	heta_2pm1°','边界射线（即区域各边）'},'FontSize',9,'Color',C.geometry, ...
     'BackgroundColor','w','EdgeColor',C.geometry,'Margin',4,'VerticalAlignment','top');
xlim(ax2,[275 325]); ylim(ax2,[472 528]); axis(ax2,'equal');
xlabel(ax2,'X 坐标 (m)'); ylabel(ax2,'Y 坐标 (m)');
title(ax2,sprintf('(b) 定位区域 L 放大：D = %.2f m，R_{MEC} = %.2f m',D,R),'FontSize',13,'FontWeight','bold');
grid(ax2,'on'); set(ax2,'GridAlpha',0.15); box(ax2,'on');
noToolbar_(fig);
print(fig, fullfile(outdir,'Q1_MAIN_02_交会定位区域构造_v2.png'), '-dpng','-r300');
fprintf('已保存 图2 修正版\n');

%% ============ 图4（修正版）：Jung 夹逼图 ============
fig4 = figure('Position',[60 60 1500 520],'Color',C.paper,'PaperPositionMode','auto');

% (a) 基准算例
axa = subplot(1,3,1); set(axa,'Color',C.paper); hold(axa,'on');
patch(poly(:,1),poly(:,2),C.field,'FaceAlpha',0.45,'EdgeColor','none');
plot(axa,poly([1:end 1],1),poly([1:end 1],2),'-','Color',C.geometry,'LineWidth',1.5);
th = linspace(0,2*pi,500);
plot(axa,cen(1)+(D/2)*cos(th), cen(2)+(D/2)*sin(th),'-','Color',C.sage,'LineWidth',3.2);
plot(axa,cen(1)+(D/sqrt(3))*cos(th), cen(2)+(D/sqrt(3))*sin(th),'--','Color',C.slate,'LineWidth',1.6);
plot(axa,[poly(ip,1) poly(jq,1)],[poly(ip,2) poly(jq,2)],'-','Color',C.ochre,'LineWidth',2.4);
plot(axa,cen(1),cen(2),'+','MarkerSize',13,'LineWidth',2,'Color',C.ink);
plot(axa,poly(ip,1),poly(ip,2),'o','MarkerSize',7,'MarkerFaceColor',C.ochre,'MarkerEdgeColor',C.ink);
plot(axa,poly(jq,1),poly(jq,2),'o','MarkerSize',7,'MarkerFaceColor',C.ochre,'MarkerEdgeColor',C.ink);
text(axa,300+1.5,500.5,sprintf('D = %.3f m',D),'FontSize',10,'Color',C.ochre,'FontWeight','bold','Rotation',90);
text(axa,278.5,525.5,{'下界取等（基准算例）','D/2 = R_{MEC} = 19.799 m','\gamma = 1.000000','D/\surd3 = 22.862 m（含余量）'}, ...
     'FontSize',8.5,'Color',C.ink,'BackgroundColor','w','EdgeColor',C.sage,'Margin',4,'VerticalAlignment','top');
xlim(axa,[278 322]); ylim(axa,[474 526]); axis(axa,'equal');
xlabel(axa,'X 坐标 (m)'); ylabel(axa,'Y 坐标 (m)');
title(axa,'(a) 基准算例：\gamma = 1（下界取等）','FontSize',12,'FontWeight','bold');
grid(axa,'on'); set(axa,'GridAlpha',0.15); box(axa,'on');

% (b) 等边三角形（上界取等）
axb = subplot(1,3,2); set(axb,'Color',C.paper); hold(axb,'on');
a3 = 100; A = [0 0]; B = [a3 0]; Cc = [a3/2 a3*sqrt(3)/2];
patch([A(1) B(1) Cc(1)],[A(2) B(2) Cc(2)],C.field,'FaceAlpha',0.35,'EdgeColor','none');
plot(axb,[A(1) B(1) Cc(1) A(1)],[A(2) B(2) Cc(2) A(2)],'-','Color',C.geometry,'LineWidth',2);
th = linspace(0,2*pi,400);
plot(axb,a3/2+(a3/2)*cos(th), 0+(a3/2)*sin(th),'--','Color',C.rust,'LineWidth',1.8);
plot(axb,a3/2+(a3/sqrt(3))*cos(th), a3/(2*sqrt(3))+(a3/sqrt(3))*sin(th),'-','Color',C.sage,'LineWidth',2.4);
plot(axb,[A(1) B(1)],[A(2) B(2)],'-','Color',C.ochre,'LineWidth',2.4);
plot(axb,Cc(1),Cc(2),'o','MarkerSize',9,'MarkerFaceColor',C.rust,'MarkerEdgeColor',C.ink);
text(axb,-6,-9,'A','FontSize',12,'FontWeight','bold'); text(axb,101,-9,'B','FontSize',12,'FontWeight','bold');
text(axb,53,89,'C','FontSize',12,'FontWeight','bold');
text(axb,4,26,{'C 落在直径圆外','\angleACB = 60° < 90°'},'FontSize',9,'Color',C.rust,'FontWeight','bold', ...
     'BackgroundColor','w','EdgeColor',C.rust,'Margin',3);
text(axb,6,66,{'外接圆 R = D/\surd3 = 57.735 覆盖','直径圆 R = D/2 = 50 不覆盖'},'FontSize',8.6,'Color',C.ink, ...
     'BackgroundColor','w','EdgeColor',C.slate,'Margin',3);
xlim(axb,[-15 118]); ylim(axb,[-25 112]); axis(axb,'equal');
title(axb,'(b) 等边三角形：\gamma = 2/\surd3（上界取等）','FontSize',12,'FontWeight','bold');
grid(axb,'on'); set(axb,'GridAlpha',0.15); box(axb,'on');

% (c) gamma 标尺
axc = subplot(1,3,3); set(axc,'Color',C.paper); hold(axc,'on');
plot(axc,[1.0 1.17],[0 0],'-','Color',C.ink,'LineWidth',1.5);
patch([1.0 1.01 1.01 1.0],[ -0.06 -0.06 0.06 0.06],C.field,'FaceAlpha',0.7,'EdgeColor','none');
marks = [1.000000, 1.01, 2/sqrt(3)];
labs  = {{'1.000000','基准算例','（下界取等）'},{'1.010','论文实测界','\gamma \leq 1.01'},{'1.154701','等边三角形','（上界取等）'}};
cols  = {C.sage, C.geometry, C.rust};
hgt   = [0.16 0.28 0.16];
for i = 1:3
    x = marks(i);
    plot(axc,[x x],[-0.10 0.10],'-','Color',cols{i},'LineWidth',2.2);
    text(axc,x,hgt(i),labs{i},'FontSize',9,'Color',cols{i},'FontWeight','bold', ...
         'HorizontalAlignment','center','BackgroundColor','w','EdgeColor',cols{i},'Margin',3);
end
text(axc,1.005,-0.185,'本题族实测区间（\gamma \leq 1.01）','FontSize',8.5,'Color',C.geometry, ...
     'HorizontalAlignment','center');
text(axc,1.0824,-0.185,'本题族不可达区间','FontSize',8.5,'Color',C.slate,'HorizontalAlignment','center');
plot(axc,[1.01 1.154701],[-0.135 -0.135],':','Color',C.slate,'LineWidth',1);
text(axc,1.0,0.42,'Jung 夹逼： D/2 \leq R_{MEC} \leq D/\surd3   \Leftrightarrow   1 \leq \gamma \leq 2/\surd3', ...
     'FontSize',9.5,'Color',C.ink,'FontWeight','bold','HorizontalAlignment','left');
xlim(axc,[0.99 1.18]); ylim(axc,[-0.28 0.50]); axis(axc,'off');
title(axc,'(c) \gamma 值域标尺','FontSize',12,'FontWeight','bold');
noToolbar_(fig4);
print(fig4, fullfile(outdir,'Q1_MAIN_04_Jung夹逼图_v2.png'), '-dpng','-r300');
fprintf('已保存 图4 修正版\n');

%% 辅助
function noToolbar_(f)
axs = findall(f,'Type','axes');
for k = 1:numel(axs)
    try, axs(k).Toolbar.Visible = 'off'; catch, end
end
drawnow;
end

function [dmax, ip, jq] = pairMax_(P)
dmax = -1; ip = 1; jq = 1;
for i = 1:size(P,1)
    for j = i+1:size(P,1)
        d = norm(P(i,:)-P(j,:));
        if d > dmax, dmax = d; ip = i; jq = j; end
    end
end
end
