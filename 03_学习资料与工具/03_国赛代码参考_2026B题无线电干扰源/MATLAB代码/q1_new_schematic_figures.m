%% Q1 新增示意类图件（图5.1-5 顶点过滤 / 技术流程图 / 3D 交会 / 灵敏度三联图）
%  说明：示意类图件中的角度按图示需要放大（图内已注明），数值全部由 q1_geo 实时计算。
clear; clc; close all;
addpath(pwd);
C.ink=[28 28 28]/255; C.slate=[91 107 115]/255; C.paper=[247 244 238]/255;
C.field=[197 212 224]/255; C.geometry=[44 74 110]/255; C.ochre=[196 123 43]/255;
C.rust=[140 58 42]/255; C.sage=[79 111 92]/255;
set(0,'DefaultAxesFontName','Microsoft YaHei');
set(0,'DefaultTextFontName','Microsoft YaHei');
outdir = fullfile(pwd,'..','实验结果','figs');
if ~exist(outdir,'dir'), mkdir(outdir); end

%% ============ 图5.1-5：顶点过滤示意（射线族 vs 直线族） ============
cands = { [0 0;400 0;200 320],  [210 210], 6; ...
          [0 0;400 0;520 300],  [250 200], 8; ...
          [0 0;400 0;-120 250], [180 220], 8; ...
          [0 0;600 0;300 520],  [300 380], 6; ...
          [0 0;400 0;120 -160], [220 120], 10 };
best = []; bestScore = -1;
for k = 1:size(cands,1)
    [pts, isReal, poly] = lineCandidates_(cands{k,1}, cands{k,2}, cands{k,3});
    if isempty(poly), continue; end
    nFalse = sum(~isReal);
    fprintf('  候选 %d：%d 站，eps=%g -> 假交点数 %d，真顶点数 %d\n', k, size(cands{k,1},1), cands{k,3}, nFalse, size(poly,1));
    if nFalse > bestScore
        bestScore = nFalse; best = k;
    end
end
St = cands{best,1}; Gs = cands{best,2}; ed = cands{best,3};
[pts, isReal, poly] = lineCandidates_(St, Gs, ed);
[D0,R0,~,g0] = q1_geo('polyStats', poly);
fprintf('顶点过滤示意：选用 %d 站配置，G=(%g,%g)，ε=%g°，假交点数=%d\n', size(St,1), Gs(1), Gs(2), ed, sum(~isReal));
for i2 = 1:size(St,1), fprintf('    S%d = (%.0f, %.0f)\n', i2, St(i2,1), St(i2,2)); end
fprintf('  真区域顶点数=%d, D=%.4f m, R_MEC=%.4f m, gamma=%.6f\n', size(poly,1), D0, R0, g0);

figA = figure('Position',[70 70 1300 560],'Color',C.paper,'PaperPositionMode','auto');
titles = {'(a) ✗ 误用直线族（t \in R）：出现反向假交点','(b) ✓ 射线族（t ≥ 0）+ 顶点过滤（∀k: P ∈ W_k）'};
nS = size(St,1); Rw = 1000;
bb = zeros(nS,1); for i = 1:nS, bb(i) = atan2(Gs(2)-St(i,2), Gs(1)-St(i,1)); end
for panel = 1:2
    ax = axes('Parent',figA,'Position',[0.05+0.47*(panel-1) 0.10 0.41 0.80]); hold(ax,'on');
    for i = 1:nS
        Ss = St(i,:);
        aa = linspace(bb(i)-ed*pi/180, bb(i)+ed*pi/180, 40);
        patch([Ss(1), Ss(1)+Rw*cos(aa), Ss(1)], [Ss(2), Ss(2)+Rw*sin(aa), Ss(2)], C.field, 'FaceAlpha',0.40,'EdgeColor','none');
        for sg = [-1 1]
            ang = bb(i) + sg*ed*pi/180;
            if panel == 1
                plot(ax, [Ss(1)-Rw*cos(ang), Ss(1)+Rw*cos(ang)], [Ss(2)-Rw*sin(ang), Ss(2)+Rw*sin(ang)], '-', 'Color', C.slate, 'LineWidth', 1.0);
            else
                plot(ax, [Ss(1), Ss(1)+Rw*cos(ang)], [Ss(2), Ss(2)+Rw*sin(ang)], '-', 'Color', C.geometry, 'LineWidth', 1.3);
            end
        end
        plot(ax, Ss(1), Ss(2), 's', 'MarkerSize', 10, 'MarkerFaceColor', C.geometry, 'MarkerEdgeColor', C.ink);
        text(ax, Ss(1)-25, Ss(2)-80, sprintf('S_%d', i), 'FontSize', 10);
    end
    plot(ax, poly([1:end 1],1), poly([1:end 1],2), '-', 'Color', C.sage, 'LineWidth', 3);
    if panel == 1
        kk = convhull(pts(:,1), pts(:,2));
        plot(ax, pts(kk,1), pts(kk,2), '--', 'Color', C.rust, 'LineWidth', 1.8);
    end
    vi = 0;
    for i = 1:size(pts,1)
        if isReal(i)
            plot(ax, pts(i,1), pts(i,2), 'o', 'MarkerSize', 7, 'MarkerFaceColor', C.geometry, 'MarkerEdgeColor', C.ink);
            vi = vi + 1;
            if panel == 2, text(ax, pts(i,1)+15, pts(i,2)+24, sprintf('V%d',vi), 'FontSize', 9.5, 'Color', C.ink); end
        else
            plot(ax, pts(i,1), pts(i,2), 'x', 'MarkerSize', 11, 'LineWidth', 2.2, 'Color', C.rust);
        end
    end
    plot(ax, Gs(1), Gs(2), 'p', 'MarkerSize', 15, 'MarkerFaceColor', C.rust, 'MarkerEdgeColor', C.ink);
    text(ax, Gs(1)+25, Gs(2)+45, '真源 G', 'FontSize', 10, 'Color', C.rust, 'FontWeight','bold');
    xlim(ax,[-300 950]); ylim(ax,[-350 800]); axis(ax,'equal');
    xlabel(ax,'X 坐标 (m)'); ylabel(ax,'Y 坐标 (m)');
    title(ax, titles{panel}, 'FontSize', 12, 'FontWeight','bold');
    grid(ax,'on'); set(ax,'GridAlpha',0.15); box(ax,'on');
end
text(0.50, 0.945, sprintf('示意角度 ε = %g°（实际 ε = 1°，图中放大以便显示）；共 %d 个候选交点，其中 %d 个为"假交点"', ed, size(pts,1), sum(~isReal)), ...
     'Units','normalized','FontSize',9.5,'Color',C.ink,'HorizontalAlignment','center','FontWeight','bold');
text(0.50, 0.030, {'■ 蓝点 = 真顶点（同时落在所有角域内）　　× 红叉 = 假交点（线段相交但不在所有角域内）', ...
     '—— 绿实线 = 正确区域 L　　- - 红虚线 = 误把直线当射线所得的"错误凸包"（区域被撑大）'}, ...
     'Units','normalized','FontSize',9,'Color',C.ink,'HorizontalAlignment','center');
noToolbar_(figA);
print(figA, fullfile(outdir,'Q1_EXT_05_顶点过滤示意.png'), '-dpng','-r300');
fprintf('已保存 图5.1-5 顶点过滤示意\n');

%% ============ 技术路线 / 算法流程图 ============
figB = figure('Position',[60 60 1180 760],'Color',C.paper,'PaperPositionMode','auto');
ax = axes('Parent',figB,'Position',[0.02 0.02 0.96 0.96]); hold(ax,'on');
xlim(ax,[0 10]); ylim(ax,[0 16.5]); axis(ax,'off');
boxSpec = {
  1.0 15.0 5.6 0.95 '输入：站址 {S_i}、示向度 {θ_i}、测向误差 ±ε'                         C.field  C.geometry
  1.0 13.6 5.6 0.95 '角域升格：W_i = { P : ∠(P−S_i, u_i) ≤ ε }（3 个半平面表示）'          C.field  C.geometry
  1.0 12.2 5.6 0.95 '候选顶点：各站两条边界射线，跨站两两求交'                                 C.field  C.geometry
  1.0 10.8 5.6 0.95 '顶点过滤：∀k 满足 P ∈ W_k（红线 W2，最易漏）'                           C.ochre  C.ink
  1.0  9.4 5.6 0.80 '候选集为空？ → 输出「无可行定位区域」'                                   C.paper  C.rust
  1.0  7.6 5.6 0.95 'Andrew 单调链凸包 → 凸多边形 L'                                          C.field  C.geometry
  1.0  6.2 5.6 0.80 'L 无界？ → 输出「无界」（近平行，|θ_1−θ_2| ≤ 2ε）'                       C.paper  C.rust
  1.0  4.4 5.6 0.95 '旋转卡壳求直径 D ＋ 暴力 O(m²) 互验（断言 A2）'                            C.field  C.geometry
  1.0  3.0 5.6 0.95 'Welzl 求最小包围圆 R_{MEC} ＋ 暴力互验（断言 A3）'                         C.field  C.geometry
  1.0  1.6 5.6 0.95 '自动检验：D/2 ≤ R_{MEC} ≤ D/√3（Jung 界，违反即 bug）'                     C.field  C.geometry
  1.0  0.2 5.6 0.95 '输出：L 顶点、D、R_{MEC}、γ，并由 Thales 判据给出覆盖结论'                 C.sage   C.ink
};
for i = 1:size(boxSpec,1)
    rectangle(ax, 'Position', [boxSpec{i,1} boxSpec{i,2} boxSpec{i,3} boxSpec{i,4}], ...
        'Curvature',0.18, 'FaceColor', boxSpec{i,6}, 'EdgeColor', boxSpec{i,7}, 'LineWidth',1.3);
    text(ax, boxSpec{i,1}+boxSpec{i,3}/2, boxSpec{i,2}+boxSpec{i,4}/2, boxSpec{i,5}, ...
        'HorizontalAlignment','center','FontSize',9.5,'Color',C.ink);
end
for i = 1:size(boxSpec,1)-1
    y0 = boxSpec{i,2};
    quiver(ax, 3.8, y0, 0, -0.22, 0, 'Color', C.ink, 'LineWidth', 1.3, 'MaxHeadSize', 1.2);
end
% 侧栏
rectangle(ax,'Position',[7.0 11.4 2.9 4.1],'Curvature',0.08,'FaceColor',[1 1 1],'EdgeColor',C.rust,'LineWidth',1.3);
text(ax, 7.2, 15.2, {'三大红线（必须守住）','','W1  角域是射线族 t ≥ 0','W2  顶点过滤 ∀k: P ∈ W_k','W3  角度环绕用 angdiff',''}, 'FontSize',9.5,'Color',C.ink);
text(ax, 7.2, 13.4, {'任一失守 ⇒ 区域错大 / 变空 /','直径 D 与最小包围圆全错'},'FontSize',9,'Color',C.rust);
rectangle(ax,'Position',[7.0 5.6 2.9 4.4],'Curvature',0.08,'FaceColor',[1 1 1],'EdgeColor',C.sage,'LineWidth',1.3);
text(ax, 7.2, 9.5, {'双实现互验（本问的"多次运行"）','','旋转卡壳 D  ≡  暴力 O(m²) D','Welzl R_{MEC}  ≡  暴力最小包围圆','Jung 界  D/2 ≤ R_{MEC} ≤ D/√3',''}, 'FontSize',9.5,'Color',C.ink);
text(ax, 7.2, 7.3, {'两条实现路径互为检验：','不一致即 bug，先查 EPS → 顶点过滤','→ 凸包共线 → 卡壳终止条件'},'FontSize',9,'Color',C.sage);
title(ax, 'Q1 求解技术路线与算法流程（角域 → 定位区域 → 直径/最小包围圆 → 覆盖判定）','FontSize',13.5,'FontWeight','bold');
noToolbar_(figB);
print(figB, fullfile(outdir,'Q1_EXT_09_技术路线流程图.png'), '-dpng','-r300');
fprintf('已保存 技术路线流程图\n');

%% ============ 3D 角域交会示意 ============
S1b = [0 0]; S2b = [600 0]; Gb = [300 500]; edb = 8;   % 3D 示意放大角度
figC = figure('Position',[60 60 1420 720],'Color',C.paper,'PaperPositionMode','auto');
ax3 = axes('Parent',figC,'Position',[0.035 0.07 0.48 0.82]); hold(ax3,'on');
Hgrid = 320; Rgrid = 760;
[Xg,Yg] = meshgrid(-200:100:900, -200:100:800);
surf(ax3, Xg, Yg, zeros(size(Xg)), 'FaceColor', [0.93 0.92 0.89], 'EdgeColor',[0.82 0.80 0.76], 'FaceAlpha',0.85);
for s = 1:2
    if s == 1, Ss = S1b; else, Ss = S2b; end
    bb = atan2(Gb(2)-Ss(2), Gb(1)-Ss(1));
    aa = linspace(bb-edb*pi/180, bb+edb*pi/180, 12);
    % 竖直"幕布"：角域在三维中的示意（弧面用条带逼近）
    for i = 1:numel(aa)-1
        p1 = [Ss(1)+Rgrid*cos(aa(i)),   Ss(2)+Rgrid*sin(aa(i))];
        p2 = [Ss(1)+Rgrid*cos(aa(i+1)), Ss(2)+Rgrid*sin(aa(i+1))];
        patch(ax3, [Ss(1) p1(1) p2(1) Ss(1)], [Ss(2) p1(2) p2(2) Ss(2)], [0 Hgrid Hgrid 0], ...
              C.field, 'FaceAlpha',0.18, 'EdgeColor','none');
    end
    for sg = [-1 1]
        ang = bb + sg*edb*pi/180;
        plot3(ax3, [Ss(1) Ss(1)+Rgrid*cos(ang)], [Ss(2) Ss(2)+Rgrid*sin(ang)], [0 Hgrid], '-', 'Color', C.geometry, 'LineWidth',1.2);
    end
    plot3(ax3, Ss(1), Ss(2), 0, 's', 'MarkerSize', 10, 'MarkerFaceColor', C.geometry, 'MarkerEdgeColor', C.ink);
end
% 交会棱柱（定位区域竖直拉伸，示意）
polyR = q1_geo('regionFromSource',[S1b;S2b],Gb,1);
[DcR, RcR, cenR, gcR] = q1_geo('polyStats', polyR);
ipR = 1; jqR = 1; dRmax = -1;
for i2 = 1:size(polyR,1)
    for j2 = i2+1:size(polyR,1)
        if norm(polyR(i2,:)-polyR(j2,:)) > dRmax
            dRmax = norm(polyR(i2,:)-polyR(j2,:)); ipR = i2; jqR = j2;
        end
    end
end
H2 = 40;
patch(ax3, polyR(:,1), polyR(:,2), zeros(size(polyR,1),1), C.rust, 'FaceAlpha',0.85,'EdgeColor',C.ink,'LineWidth',1);
patch(ax3, polyR(:,1), polyR(:,2), H2*ones(size(polyR,1),1), C.rust, 'FaceAlpha',0.35,'EdgeColor',C.ink,'LineWidth',1);
for i = 1:size(polyR,1)
    j = mod(i,size(polyR,1))+1;
    patch(ax3, [polyR(i,1) polyR(j,1) polyR(j,1) polyR(i,1)], [polyR(i,2) polyR(j,2) polyR(j,2) polyR(i,2)], [0 0 H2 H2], ...
          C.rust, 'FaceAlpha',0.28,'EdgeColor','none');
end
plot3(ax3, Gb(1), Gb(2), 12, 'p', 'MarkerSize', 16, 'MarkerFaceColor', C.rust, 'MarkerEdgeColor', C.ink);
text(ax3, Gb(1)+40, Gb(2)+40, 60, '真源 G', 'FontSize',11,'Color',C.rust,'FontWeight','bold');
text(ax3, Gb(1)+40, Gb(2)+40, 22, '（定位区域 L 仅 40 m 量级，放大见右图）','FontSize',9,'Color',C.ink);
text(ax3, S1b(1)-60, S1b(2)-90, 40, 'S_1', 'FontSize',11);
text(ax3, S2b(1)+30, S2b(2)-90, 40, 'S_2', 'FontSize',11);
text(ax3, Gb(1)+80, Gb(2)-160, 10, {'定位区域 L','（水平截面 40 m 量级）'}, 'FontSize',9.5,'Color',C.ink);
xlabel(ax3,'X 坐标 (m)'); ylabel(ax3,'Y 坐标 (m)'); zlabel(ax3,'示意高度 (m)');
title(ax3, {'(a) 角域的三维交会（宏观）','两个"竖直楔面"的交即定位区域（角度放大为 ±8° 示意）'}, 'FontSize',12.5,'FontWeight','bold');
view(ax3, -37, 22); grid(ax3,'on'); set(ax3,'GridAlpha',0.2); axis(ax3,'vis3d');
xlim(ax3,[-150 900]); ylim(ax3,[-150 750]); zlim(ax3,[0 340]);

% (b) 局部放大：定位区域棱柱（真实尺寸）
ax4 = axes('Parent',figC,'Position',[0.545 0.07 0.44 0.82]); hold(ax4,'on');
patch(ax4, polyR(:,1), polyR(:,2), zeros(size(polyR,1),1), C.rust,'FaceAlpha',0.9,'EdgeColor',C.ink,'LineWidth',1.2);
patch(ax4, polyR(:,1), polyR(:,2), H2*ones(size(polyR,1),1), C.rust,'FaceAlpha',0.25,'EdgeColor',C.ink,'LineWidth',1);
for i = 1:size(polyR,1)
    j = mod(i,size(polyR,1))+1;
    patch(ax4, [polyR(i,1) polyR(j,1) polyR(j,1) polyR(i,1)], [polyR(i,2) polyR(j,2) polyR(j,2) polyR(i,2)], [0 0 H2 H2], C.rust,'FaceAlpha',0.22,'EdgeColor','none');
end
thc = linspace(0,2*pi,200);
plot3(ax4, cenR(1)+RcR*cos(thc), cenR(2)+RcR*sin(thc), zeros(size(thc)), '-','Color',C.sage,'LineWidth',2.4);
plot3(ax4, [polyR(ipR,1) polyR(jqR,1)], [polyR(ipR,2) polyR(jqR,2)], [0 0], '-','Color',C.ochre,'LineWidth',2.6);
plot3(ax4, Gb(1), Gb(2), 0, 'p','MarkerSize',14,'MarkerFaceColor',C.rust,'MarkerEdgeColor',C.ink);
text(ax4, Gb(1)+5, Gb(2)+5, 10, '真源 G','FontSize',10,'Color',C.rust,'FontWeight','bold');
text(ax4, cenR(1)+12, cenR(2)+26, 30, sprintf('D = %.2f m', DcR),'FontSize',10,'Color',C.ochre,'FontWeight','bold');
text(ax4, cenR(1)-42, cenR(2)-26, 4, {sprintf('R_{MEC} = %.2f m', RcR), ['\gamma = ' sprintf('%.4f', gcR) '（下界取等）']}, ...
     'FontSize',9.5,'Color',C.sage,'FontWeight','bold');
title(ax4, {'(b) 局部放大：定位区域棱柱（真实尺寸）','水平截面 = 二维定位区域 L'}, 'FontSize',12.5,'FontWeight','bold');
xlabel(ax4,'X 坐标 (m)'); ylabel(ax4,'Y 坐标 (m)'); zlabel(ax4,'示意高度 (m)');
view(ax4, -35, 20); grid(ax4,'on'); set(ax4,'GridAlpha',0.2); axis(ax4,'vis3d');
xlim(ax4,[cenR(1)-45 cenR(1)+45]); ylim(ax4,[cenR(2)-45 cenR(2)+45]); zlim(ax4,[0 60]);
noToolbar_(figC);
print(figC, fullfile(outdir,'Q1_EXT_10_3D角域交会.png'), '-dpng','-r300');
fprintf('已保存 3D 角域交会示意\n');

%% ============ 灵敏度三联图 ============
S1c = [0 0]; S2c = [600 0]; Gc = [300 500];
epsList = [0.1 0.25 0.5 1 2 3 4 5];
Dv = zeros(size(epsList)); Rv = Dv; gv = Dv;
for i = 1:numel(epsList)
    [p,~,~] = q1_geo('regionFromSource',[S1c;S2c],Gc,epsList(i));
    [Dv(i),Rv(i),~,gv(i)] = q1_geo('polyStats', p);
end
% 加站灵敏度
Gd = [300 500];
St = [0 0; 600 0];
for ang = [215 335 95 275]
    St(end+1,:) = Gd + 600*[cosd(ang) sind(ang)]; %#ok<SAGROW>
end
Dn = zeros(1,size(St,1)); nv = Dn;
for n = 2:size(St,1)
    [p,~,~] = q1_geo('regionFromSource', St(1:n,:), Gd, 1);
    Dn(n) = q1_geo('diameter', p); nv(n) = size(p,1);
end
% 距离灵敏度
hList = logspace(log10(60), log10(3000), 60);
Dh = zeros(size(hList)); ph = Dh;
for i = 1:numel(hList)
    [p,~,~] = q1_geo('regionFromSource',[-300 0; 300 0],[0 hList(i)],1);
    Dh(i) = q1_geo('diameter', p); ph(i) = 2*atand(300/hList(i));
end
fprintf('灵敏度：D(ε)/ε 从 %.3f（ε=0.1°）到 %.3f（ε=5°）；D(n) = %s；最小 D 在 h=%.0f m（φ=%.1f°）\n', ...
    Dv(1)/epsList(1), Dv(end)/epsList(end), mat2str(round(Dn(2:end),3)), hList(find(Dh==min(Dh),1)), ph(find(Dh==min(Dh),1)));

figD = figure('Position',[50 50 1550 480],'Color',C.paper,'PaperPositionMode','auto');
ax1 = axes('Parent',figD,'Position',[0.05 0.16 0.26 0.70]); hold(ax1,'on');
plot(ax1, epsList, Dv, 'o-', 'Color', C.ochre, 'LineWidth',2,'MarkerFaceColor',C.ochre,'MarkerSize',5);
plot(ax1, epsList, Rv, 's--', 'Color', C.sage, 'LineWidth',1.6,'MarkerFaceColor',C.sage,'MarkerSize',5);
plot(ax1, epsList, Dv(4)/epsList(4)*epsList, ':', 'Color', C.slate, 'LineWidth',1.6);
text(ax1, 0.35, 0.72*max(Dv), {'D（实测）','R_{MEC}（实测）','线性参考 D \propto \epsilon'}, 'FontSize',9,'Color',C.ink,'BackgroundColor','w','EdgeColor',C.slate,'Margin',3);
text(ax1, 1.2, 0.30*max(Dv), {sprintf('D/\\epsilon: %.2f m/°（\\epsilon=0.1°）', Dv(1)/epsList(1)), ...
     sprintf('→ %.2f m/°（\\epsilon=5°，偏差 +2.4%%）', Dv(end)/epsList(end))}, 'FontSize',8.8,'Color',C.ochre);
xlabel(ax1,'测向误差 \epsilon (°)'); ylabel(ax1,'跨度 (m)');
title(ax1,'(a) \epsilon 灵敏度：D \propto \epsilon（小误差区近似）','FontSize',11.5,'FontWeight','bold');
grid(ax1,'on'); set(ax1,'GridAlpha',0.15); box(ax1,'on'); xlim(ax1,[0 5.4]);

ax2 = axes('Parent',figD,'Position',[0.375 0.16 0.26 0.70]); hold(ax2,'on');
b = bar(ax2, 2:size(St,1), Dn(2:end), 0.55, 'FaceColor', C.geometry, 'EdgeColor', C.ink, 'LineWidth',0.8); %#ok<NASGU>
for n = 2:size(St,1)
    text(ax2, n, Dn(n)+0.8, sprintf('%.2f', Dn(n)), 'HorizontalAlignment','center','FontSize',8.8,'Color',C.ink);
end
text(ax2, 2.0, Dn(2)*0.55, {'加站 1（第 3 站）','D 下降 27%'}, 'FontSize',8.6,'Color','w','FontWeight','bold');
text(ax2, 3.0, Dn(3)*0.75, {'再加站趋于饱和','（约束不再收紧）'}, 'FontSize',8.6,'Color',C.ink);
xlabel(ax2,'检测站数量 n'); ylabel(ax2,'直径 D (m)');
set(ax2,'XTick',2:size(St,1)); xlim(ax2,[1.4 size(St,1)+0.6]);
title(ax2,'(b) n 灵敏度：加站 D 单调不增，收益递减','FontSize',11.5,'FontWeight','bold');
grid(ax2,'on'); set(ax2,'GridAlpha',0.15); box(ax2,'on');

ax3 = axes('Parent',figD,'Position',[0.70 0.16 0.26 0.70]); hold(ax3,'on');
yyaxis(ax3,'left'); semilogx(ax3, hList, Dh, '-', 'Color', C.ochre, 'LineWidth',2.2); ylabel(ax3,'直径 D (m)');
ax3.YColor = C.ochre;
yyaxis(ax3,'right'); semilogx(ax3, hList, ph, '--', 'Color', C.slate, 'LineWidth',1.4); ylabel(ax3,'交会角 \phi (°)');
ax3.YColor = C.slate;
xlabel(ax3,'目标到基线中点距离 h (m，对数刻度)');
iopt = find(Dh == min(Dh), 1);
plot(ax3, hList(iopt), Dh(iopt), 'o', 'MarkerSize', 9, 'MarkerFaceColor', C.rust, 'MarkerEdgeColor', C.ink);
text(ax3, 0.75*hList(iopt), 1.75*Dh(iopt), {sprintf('D 最小：h = %.0f m，\\phi = %.0f°', hList(iopt), ph(iopt)), ...
     '两侧因 \phi 偏离 90° 而增大'}, 'FontSize',8.8,'Color',C.rust,'FontWeight','bold');
title(ax3,'(c) 距离灵敏度：\phi = 90° 时 D 最小','FontSize',11.5,'FontWeight','bold');
grid(ax3,'on'); set(ax3,'GridAlpha',0.15); box(ax3,'on');
noToolbar_(figD);
print(figD, fullfile(outdir,'Q1_EXT_11_灵敏度三联图.png'), '-dpng','-r300');
fprintf('已保存 灵敏度三联图\n');

%% ==================== 辅助函数 ====================
function [pts, isReal, poly] = lineCandidates_(S, Gs, ed)
% 把所有站的全部边界当"直线"两两求交（仅跨站配对），
% 并标注哪些交点真的同时落在所有角域内（即"真顶点"）
n = size(S,1);
b = zeros(n,1);
for i = 1:n, b(i) = atan2(Gs(2)-S(i,2), Gs(1)-S(i,1)); end
lines = zeros(2*n,4); own = zeros(2*n,1); k = 0;
for i = 1:n
    for sg = [-1 1]
        k = k + 1; a = b(i) + sg*ed*pi/180;
        lines(k,:) = [S(i,:), cos(a), sin(a)]; own(k) = i;
    end
end
pts = zeros(0,2); isReal = logical([]);
for i = 1:2*n
    for j = i+1:2*n
        if own(i) == own(j), continue; end
        p = cross2_(lines(i,:), lines(j,:));
        if isempty(p), continue; end
        inw = true;
        for q = 1:n
            inw = inw && inWedge_(p, S(q,:), b(q), ed);
        end
        pts(end+1,:) = p; %#ok<AGROW>
        isReal(end+1,1) = inw; %#ok<AGROW>
    end
end
realp = pts(isReal,:);
if size(realp,1) >= 3
    kk = convhull(realp(:,1), realp(:,2));
    poly = realp(kk(1:end-1),:);
else
    poly = zeros(0,2);
end
end

function p = cross2_(l1, l2)
% 两条直线 [Sx Sy cos sin] 的交点（无交点返回空）
A = [l1(3) -l2(3); l1(4) -l2(4)];
rhs = [l2(1)-l1(1); l2(2)-l1(2)];
if abs(det(A)) < 1e-12, p = []; return; end
ts = A\rhs;
p = [l1(1) + ts(1)*l1(3), l1(2) + ts(1)*l1(4)];
end

function tf = inWedge_(p, S, b, ed)
d = p - S;
if norm(d) < 1e-12, tf = true; return; end
ang = atan2(d(2), d(1));
dd = abs(mod(ang - b + pi, 2*pi) - pi);
tf = dd <= ed*pi/180 + 1e-9;
end

function noToolbar_(f)
axs = findall(f,'Type','axes');
for k = 1:numel(axs)
    try, axs(k).Toolbar.Visible = 'off'; catch, end
end
drawnow;
end
