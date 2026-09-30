%% Q1 新增数据类图件（图5.1-6 γ分布 / 图5.1-7 φ–D曲线 / 图5.1-8 参数空间四类分区）
%  全部数据由 q1_geo 内核实时计算，不使用任何硬编码结果。
clear; clc; close all;
addpath(pwd);
C.ink=[28 28 28]/255; C.slate=[91 107 115]/255; C.paper=[247 244 238]/255;
C.field=[197 212 224]/255; C.geometry=[44 74 110]/255; C.ochre=[196 123 43]/255;
C.rust=[140 58 42]/255; C.sage=[79 111 92]/255;
set(0,'DefaultAxesFontName','Microsoft YaHei');
set(0,'DefaultTextFontName','Microsoft YaHei');
outdir = fullfile(pwd,'..','实验结果','figs');
if ~exist(outdir,'dir'), mkdir(outdir); end
rng(20260911);

%% ===================== 图5.1-6：γ 分布（随机配置扫描） =====================
N = 6000; epsDeg = 1;
Gam = []; Nn = []; Nv = [];
for k = 1:N
    n = 2 + mod(k,3);                      % n = 2,3,4 个检测站
    Rc = 200 + 1300*rand;
    ang = 2*pi*(0:n-1)'/n + 0.3*rand;
    S = [Rc*cos(ang), Rc*sin(ang)];
    S = S + 0.25*Rc*(rand(size(S))-0.5);
    Gs = 1.8*Rc*(rand(1,2)-0.5);
    [poly,bounded,isEmpty] = q1_geo('regionFromSource', S, Gs, epsDeg);
    if isEmpty || ~bounded, continue; end
    [D,R,~,gm] = q1_geo('polyStats', poly);
    if D < 1e-9 || ~isfinite(gm), continue; end
    Gam(end+1,1) = gm; Nn(end+1,1) = n; Nv(end+1,1) = size(poly,1); %#ok<SAGROW>
end
fprintf('γ 扫描：样本 %d 组（n=2/3/4，ε=%g°）\n', numel(Gam), epsDeg);
fprintf('  min=%.9f  max=%.9f  median=%.9f  mean=%.9f\n', min(Gam), max(Gam), median(Gam), mean(Gam));
fprintf('  γ≡1（|γ-1|<1e-9）占比 = %.2f%%\n', 100*mean(Gam <= 1+1e-9));
assert(min(Gam) >= 1-1e-9, 'Jung 下界被违反：实现有误');
assert(max(Gam) <= 2/sqrt(3)+1e-9, 'Jung 上界被违反：实现有误');
exactShare = 100*mean(Gam <= 1+1e-9);
gmax = max(Gam)-1;

fig = figure('Position',[80 80 1300 500],'Color',C.paper,'PaperPositionMode','auto');
ax1 = subplot(1,2,1); set(ax1,'Color',C.paper); hold(ax1,'on');
xvals = max(Gam-1, 1e-9);
edges = logspace(-9, log10(max(2e-3, 2*gmax)), 45);
histogram(xvals, edges, 'FaceColor', C.geometry, 'EdgeColor','none');
set(ax1,'XScale','log'); yl = ylim(ax1);
plot(ax1,[1e-2 1e-2],[0 yl(2)],'--','Color',C.rust,'LineWidth',1.6);
text(ax1,1.05e-2, yl(2)*0.86, {'论文实测界','\gamma \leq 1.01（仍有余量）'},'FontSize',9.5,'Color',C.rust,'FontWeight','bold');
plot(ax1,[gmax gmax],[0 yl(2)],'-','Color',C.ochre,'LineWidth',1.6);
text(ax1,gmax*1.15, yl(2)*0.55, sprintf('实测最大\n\\gamma-1 = %.2e',gmax),'FontSize',8.6,'Color',C.ochre,'FontWeight','bold');
text(ax1,1.6e-9, yl(2)*0.93, {sprintf('\\gamma \\equiv 1（精确取等）占 %.1f%%',exactShare), ...
     sprintf('样本 %d 组；n=2/3/4，\\epsilon=%g°', numel(Gam), epsDeg)},'FontSize',9.5,'Color',C.ink);
xlabel(ax1,'\gamma - 1 = R_{MEC}/(D/2) - 1   （对数刻度）');
ylabel(ax1,'配置组数');
title(ax1,'(a) 定位区域族的 \gamma 分布（Jung 缺口）','FontSize',12.5,'FontWeight','bold');
box(ax1,'on'); grid(ax1,'on'); set(ax1,'GridAlpha',0.15);

ax2 = subplot(1,2,2); set(ax2,'Color',C.paper); hold(ax2,'on');
ns = [2 3 4]; mx = zeros(1,3); md = zeros(1,3); cnt = zeros(1,3);
for i = 1:3
    sel = Nn == ns(i);
    cnt(i) = sum(sel); mx(i) = max(Gam(sel))-1; md(i) = median(Gam(sel))-1;
end
b = bar(1:3, mx, 0.55, 'FaceColor', C.geometry, 'EdgeColor', C.ink, 'LineWidth',0.8); %#ok<NASGU>
ylabel(ax2,'max(\gamma-1)');
set(ax2,'YScale','log'); hold(ax2,'on');
plot(ax2,[1 3],[2/sqrt(3)-1, 2/sqrt(3)-1],'--','Color',C.rust,'LineWidth',1.6);
plot(ax2,[1 3],[0.01 0.01],':','Color',C.slate,'LineWidth',1.6);
text(ax2,1.0,2/sqrt(3)-1,'Jung 理论上界 2/\surd3-1 = 0.1547（等边三角形，本题族不可达）','FontSize',8.6,'Color',C.rust,'FontWeight','bold','VerticalAlignment','bottom');
text(ax2,1.0,0.01,'论文实测界 0.01','FontSize',8.6,'Color',C.slate,'VerticalAlignment','bottom');
for i = 1:3
    text(ax2,i,mx(i)*1.35,sprintf('%.2e',mx(i)),'FontSize',8.6,'Color',C.ink,'HorizontalAlignment','center');
    text(ax2,i,mx(i)*0.35,sprintf('n=%d\n%d 组',ns(i),cnt(i)),'FontSize',8.6,'Color','w','HorizontalAlignment','center');
end
ylim(ax2,[1e-6 1]); xlim(ax2,[0.4 3.6]);
set(ax2,'XTick',1:3,'XTickLabel',{'n=2 站','n=3 站','n=4 站'});
xlabel(ax2,'检测站数量'); title(ax2,'(b) 各站数下的最大缺口（Jung 上界不可达）','FontSize',12.5,'FontWeight','bold');
box(ax2,'on'); grid(ax2,'on'); set(ax2,'GridAlpha',0.15);
noToolbar_(fig);
print(fig, fullfile(outdir,'Q1_EXT_06_gamma分布.png'),'-dpng','-r300');
fprintf('已保存 图5.1-6 γ 分布图\n');

%% ===================== 图5.1-7：φ–D 曲线 =====================
L = 600; S1 = [-L/2 0]; S2 = [L/2 0]; epsDeg = 1;
hs = logspace(log10(30), log10(3000), 80);
phi = zeros(size(hs)); Dv = phi; Tv = phi; Th = phi;
for i = 1:numel(hs)
    Gs = [0 hs(i)];
    [poly,bounded,isEmpty] = q1_geo('regionFromSource',[S1;S2],Gs,epsDeg);
    assert(~isEmpty && bounded, 'φ-D 扫描出现空/无界区域');
    Dv(i) = q1_geo('diameter', poly);
    if size(poly,1) >= 4
        d1 = norm(poly(1,:)-poly(3,:)); d2 = norm(poly(2,:)-poly(4,:));
        Tv(i) = min(d1,d2);
    else
        Tv(i) = Dv(i);
    end
    phi(i) = 2*atand((L/2)/hs(i));
    Th(i) = L*sind(2*epsDeg)/sind(phi(i));      % 理论式（精确）
end
devD = abs(Dv-Th)./Th; devT = abs(Tv-Th)./Th;
fprintf('φ–D：max|D-理论|/理论 = %.3e, max|横向跨距-理论|/理论 = %.3e\n', max(devD(phi>92)), max(devT(phi<88)));

fig2 = figure('Position',[80 80 1300 500],'Color',C.paper,'PaperPositionMode','auto');
axa = subplot(1,2,1); set(axa,'Color',C.paper); hold(axa,'on');
plot(axa,phi,Dv,'-','Color',C.ochre,'LineWidth',2.4);
plot(axa,phi,Tv,'-','Color',C.geometry,'LineWidth',1.8);
plot(axa,phi,Th,'--','Color',C.sage,'LineWidth',2.2);
plot(axa,[90 90],[0 1.2*max(Dv)],':','Color',C.slate,'LineWidth',1.2);
text(axa,91,1.12*max(Dv),'\phi = 90°','FontSize',9.5,'Color',C.slate,'FontWeight','bold');
text(axa,25,0.30*max(Dv),{'直径 D（实测）'},'FontSize',10,'Color',C.ochre,'FontWeight','bold');
text(axa,25,0.20*max(Dv),{'横向跨距 T（实测）'},'FontSize',10,'Color',C.geometry,'FontWeight','bold');
text(axa,25,0.10*max(Dv),{'理论式 L sin2\epsilon / sin\phi'},'FontSize',10,'Color',C.sage,'FontWeight','bold');
text(axa,100,0.55*max(Dv),{'\phi < 90°：T = L sin2\epsilon/sin\phi（精确）','\phi > 90°：D = L sin2\epsilon/sin\phi（精确）','\phi = 90° 时 D 取最小值'}, ...
     'FontSize',9,'Color',C.ink,'BackgroundColor','w','EdgeColor',C.slate,'Margin',4);
xlabel(axa,'交会角 \phi (°)'); ylabel(axa,'定位区域跨度 (m)');
title(axa,'(a) 直径 D、横向跨距 T 与理论式（基线 L = 600 m，\epsilon = 1°）','FontSize',12,'FontWeight','bold');
grid(axa,'on'); set(axa,'GridAlpha',0.15); box(axa,'on'); xlim(axa,[min(phi) max(phi)]);

axb = subplot(1,2,2); set(axb,'Color',C.paper); hold(axb,'on');
semilogy(axb,phi,max(devD,1e-17),'o-','Color',C.ochre,'MarkerSize',3,'LineWidth',1.4);
semilogy(axb,phi,max(devT,1e-17),'s-','Color',C.geometry,'MarkerSize',3,'LineWidth',1.4);
plot(axb,[90 90],[1e-17 1],':','Color',C.slate,'LineWidth',1.2);
text(axb,20,3e-3,{'|D - 理论| / 理论'},'FontSize',10,'Color',C.ochre,'FontWeight','bold');
text(axb,20,2e-9,{'|T - 理论| / 理论'},'FontSize',10,'Color',C.geometry,'FontWeight','bold');
text(axb,92,1e-13,{'两条曲线在各自区间降至机器精度（\sim10^{-16}）','说明理论式为精确式而非近似式'}, ...
     'FontSize',8.8,'Color',C.ink,'BackgroundColor','w','EdgeColor',C.slate,'Margin',4);
xlabel(axb,'交会角 \phi (°)'); ylabel(axb,'相对偏差（对数刻度）');
ylim(axb,[1e-17 1]); xlim(axb,[min(phi) max(phi)]);
title(axb,'(b) 与理论式的相对偏差','FontSize',12,'FontWeight','bold');
grid(axb,'on'); set(axb,'GridAlpha',0.15); box(axb,'on');
noToolbar_(fig2);
print(fig2, fullfile(outdir,'Q1_EXT_07_phi_D曲线.png'),'-dpng','-r300');
fprintf('已保存 图5.1-7 φ–D 曲线\n');

%% ===================== 图5.1-8：(θ1,θ2) 参数空间四类分区 =====================
dt = 2; tv = 0:dt:360-dt;
m = numel(tv);
Code = zeros(m,m);
for i = 1:m
    for j = 1:m
        th1 = tv(i)*pi/180; th2 = tv(j)*pi/180;
        dirs = [cos(th1) sin(th1); cos(th2) sin(th2)];
        [poly,bounded,isEmpty] = q1_geo('regionFromDirs',[S1;S2],dirs,epsDeg);
        if isEmpty, Code(i,j) = 1;
        elseif ~bounded, Code(i,j) = 2;
        elseif size(poly,1) <= 3, Code(i,j) = 3;
        else, Code(i,j) = 4;
        end
    end
end
names = {'空（数据矛盾）','无界（近平行）','三角形（退化）','四边形（正常）'};
share = zeros(1,4);
for c = 1:4, share(c) = 100*mean(Code(:) == c); end
fprintf('参数空间四类占比：'); fprintf('%s %.1f%%  ', names{1}, share(1));
for c = 2:4, fprintf('%s %.1f%%  ', names{c}, share(c)); end
fprintf('\n');
% 各类代表点（取离类重心最近的网格点）
reps = zeros(4,2);
for c = 1:4
    [ii,jj] = find(Code == c);
    if isempty(ii), continue; end
    ii0 = median(ii); jj0 = median(jj);
    [~, k0] = min((ii - ii0).^2 + (jj - jj0).^2);   % 取离类重心最近的网格点（保证整数索引）
    reps(c,:) = [ii(k0), jj(k0)];
end
cmap = [0.86 0.86 0.84; C.ochre; C.sage; C.geometry];
fig3 = figure('Position',[60 60 1400 560],'Color',C.paper,'PaperPositionMode','auto');
axm = axes('Parent',fig3,'Position',[0.055 0.13 0.40 0.76]); hold(axm,'on');
imagesc(tv, tv, Code); set(axm,'YDir','normal');
colormap(axm, cmap); caxis(axm,[0.5 4.5]);
xlabel(axm,'\theta_1 (°)  —— 检测站 S_1 的示向度'); ylabel(axm,'\theta_2 (°)  —— 检测站 S_2 的示向度');
title(axm,'(a) (θ_1, θ_2) 平面四类分区（站距 600 m，ε = 1°）','FontSize',12,'FontWeight','bold');
plot(axm, 59.036, 120.964, 'p','MarkerSize',15,'MarkerFaceColor',C.rust,'MarkerEdgeColor','w','LineWidth',1);
text(axm, 66, 128, '基准算例 (59.04°, 120.96°)','Color','w','FontSize',9,'FontWeight','bold');
axis(axm,[0 360 0 360]); box(axm,'on'); set(axm,'XTick',0:60:360,'YTick',0:60:360);
hleg = gobjects(1,4);
for c = 1:4, hleg(c) = patch(axm, NaN, NaN, cmap(c,:), 'EdgeColor','none'); end
legend(hleg, names, 'Location','northoutside','Orientation','horizontal','FontSize',9,'Box','off');
% 右侧 2x2 代表配置小图
panelPos = [0.53 0.56 0.20 0.34; 0.77 0.56 0.20 0.34; 0.53 0.11 0.20 0.34; 0.77 0.11 0.20 0.34];
for c = 1:4
    axk = axes('Parent',fig3,'Position',panelPos(c,:)); hold(axk,'on');
    if all(reps(c,:) == 0)
        axis(axk,'off'); continue;
    end
    t1 = tv(reps(c,1))*pi/180; t2 = tv(reps(c,2))*pi/180;
    dirs = [cos(t1) sin(t1); cos(t2) sin(t2)];
    [poly,bounded,isEmpty] = q1_geo('regionFromDirs',[S1;S2],dirs,epsDeg);
    Rw = 700;
    for s = 1:2
        if s == 1, Ss = S1; u = dirs(1,:); else, Ss = S2; u = dirs(2,:); end
        b = atan2(u(2),u(1));
        aa = linspace(b-epsDeg*pi/180, b+epsDeg*pi/180, 40);
        patch([Ss(1), Ss(1)+Rw*cos(aa), Ss(1)], [Ss(2), Ss(2)+Rw*sin(aa), Ss(2)], C.field, 'FaceAlpha',0.6,'EdgeColor','none');
    end
    if ~isEmpty
        patch(poly(:,1), poly(:,2), cmap(Code(reps(c,1),reps(c,2)),:), 'FaceAlpha',0.9,'EdgeColor',C.ink,'LineWidth',1);
    end
    plot(axk, S1(1), S1(2),'s','MarkerSize',7,'MarkerFaceColor',C.geometry,'MarkerEdgeColor',C.ink);
    plot(axk, S2(1), S2(2),'s','MarkerSize',7,'MarkerFaceColor',C.geometry,'MarkerEdgeColor',C.ink);
    xlim(axk,[-800 800]); ylim(axk,[-800 800]); axis(axk,'equal'); axis(axk,'off');
    title(axk, sprintf('%s\n(θ_1=%g°, θ_2=%g°)', names{c}, tv(reps(c,1)), tv(reps(c,2))), 'FontSize',8.5);
    text(axk,-780,-700,'S_1','FontSize',8,'Color',C.ink); text(axk, 720,-700,'S_2','FontSize',8,'Color',C.ink);
end
noToolbar_(fig3);
print(fig3, fullfile(outdir,'Q1_EXT_08_参数空间四类分区.png'),'-dpng','-r300');
fprintf('已保存 图5.1-8 参数空间四类分区\n');

%% 辅助
function noToolbar_(f)
axs = findall(f,'Type','axes');
for k = 1:numel(axs)
    try, axs(k).Toolbar.Visible = 'off'; catch, end
end
drawnow;
end
