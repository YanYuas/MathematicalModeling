% ============================================================
% 三类老人马尔可夫状态转移关系图（完整版）
% ============================================================
clear; close all; clc;

figure('Position',[150,150,1020,540],'ToolBar','none','Color','w');
hold on; axis off;
xlim([0, 16]); ylim([0, 8.5]);
daspect([1 1 1]);

% ---- 配色 ----
c1 = [55,120,210]/255;   % 自理 蓝
c2 = [235,150,45]/255;   % 半失能 橙
c3 = [190,60,60]/255;    % 失能 红

% ---- 参数值 ----
d_val     = 0.05;
P_alpha   = 0.045;
P_beta    = 0.10;

% ---- 三个状态框 ----
w = 3; h = 1.6;
y0 = 3.5;

% 自理 X1
x1 = 1;
rectangle('Position',[x1,y0,w,h],'Curvature',0.25,'LineWidth',2.2,...
    'FaceColor',c1,'EdgeColor',c1*0.7);
text(x1+w/2,y0+h*0.65,'X_{1,i}(t)','FontSize',14,'Interpreter','tex',...
    'HorizontalAlignment','center','Color','w','FontWeight','bold');
text(x1+w/2,y0+h*0.22,'自理老人','FontSize',11,'HorizontalAlignment','center','Color','w');

% 半失能 X2
x2 = 6;
rectangle('Position',[x2,y0,w,h],'Curvature',0.25,'LineWidth',2.2,...
    'FaceColor',c2,'EdgeColor',c2*0.7);
text(x2+w/2,y0+h*0.65,'X_{2,i}(t)','FontSize',14,'Interpreter','tex',...
    'HorizontalAlignment','center','Color','w','FontWeight','bold');
text(x2+w/2,y0+h*0.22,'半失能老人','FontSize',11,'HorizontalAlignment','center','Color','w');

% 失能 X3
x3 = 11;
rectangle('Position',[x3,y0,w,h],'Curvature',0.25,'LineWidth',2.2,...
    'FaceColor',c3,'EdgeColor',c3*0.7);
text(x3+w/2,y0+h*0.65,'X_{3,i}(t)','FontSize',14,'Interpreter','tex',...
    'HorizontalAlignment','center','Color','w','FontWeight','bold');
text(x3+w/2,y0+h*0.22,'失能老人','FontSize',11,'HorizontalAlignment','center','Color','w');

% ---- 转移箭头：自理 -> 半失能 (P_alpha) ----
ax1 = x1+w; ay1 = y0+h*0.5;
ax2 = x2;   ay2 = y0+h*0.5;
draw_arrow(ax1, ay1, ax2, ay2, 'k', 2.5);
text((ax1+ax2)/2, ay1+0.65, 'P_{\alpha} = 0.045', 'FontSize',13, 'FontWeight','bold',...
    'HorizontalAlignment','center');

% ---- 转移箭头：半失能 -> 失能 (P_beta) ----
bx1 = x2+w; by1 = y0+h*0.5;
bx2 = x3;   by2 = y0+h*0.5;
draw_arrow(bx1, by1, bx2, by2, 'k', 2.5);
text((bx1+bx2)/2, by1+0.65, 'P_{\beta} = 0.10', 'FontSize',13, 'FontWeight','bold',...
    'HorizontalAlignment','center');

% ---- U：年均新增入口（只进入自理）----
top_y = y0 + h + 1.2;
cx_u = x1 + w/2;
draw_arrow(cx_u, top_y, cx_u, y0+h, [0,0.45,0], 2.5);
text(cx_u, top_y+0.55, 'U = 0.07', 'FontSize',13, 'FontWeight','bold',...
    'HorizontalAlignment','center','Color',[0,0.35,0]);
text(cx_u, top_y+0.1, '(年均新增率)', 'FontSize',9,...
    'HorizontalAlignment','center','Color',[0.3,0.3,0.3]);

% ---- 死亡出口 ----
death_y = 2.8;
x_left  = x1 + w/2;
x_mid   = x2 + w/2;
x_right = x3 + w/2;
for cx = [x_left, x_mid, x_right]
    plot([cx, cx], [y0, death_y], '--','LineWidth',1.8,'Color',[0.5,0.5,0.5]);
end
plot([x_left, x_right], [death_y, death_y], '--','LineWidth',1.8,'Color',[0.5,0.5,0.5]);
text((x_left+x_right)/2, death_y-0.45, 'd = 0.05  (年均自然死亡率)', 'FontSize',12,...
    'FontWeight','bold','HorizontalAlignment','center','Color',[0.4,0.4,0.4]);

% ---- 自环（保留概率）----
% X1 自环：左侧
ret_x1 = (1-d_val)*(1-P_alpha);
draw_self_loop(x1, y0, w, h, 'left', c1, ...
    sprintf('(1-d)(1-P_\\alpha) = %.4f', ret_x1));

% X2 自环：上方
ret_x2 = (1-d_val)*(1-P_beta);
draw_self_loop(x2, y0, w, h, 'top', c2, ...
    sprintf('(1-d)(1-P_\\beta) = %.4f', ret_x2));

% X3 自环：右侧
ret_x3 = (1-d_val);
draw_self_loop(x3, y0, w, h, 'right', c3, ...
    sprintf('(1-d) = %.2f', ret_x3));

hold off;

% ============================================================
% 局部函数：画箭头
% ============================================================
function draw_arrow(x1, y1, x2, y2, color, lw)
    plot([x1,x2],[y1,y2],'-','LineWidth',lw,'Color',color);
    dx = x2-x1; dy = y2-y1;
    L = sqrt(dx^2+dy^2);
    if L>0
        ux = dx/L; uy = dy/L;
        aw = 0.38; ah = 0.28;
        px = x2 - ah*ux; py = y2 - ah*uy;
        nx = -uy*aw/2; ny = ux*aw/2;
        patch([x2, px+nx, px-nx],[y2, py+ny, py-ny],color,'EdgeColor','none');
    end
end

% ============================================================
% 局部函数：画自环（半圆弧，圆心在盒子边缘）
% ============================================================
function draw_self_loop(x, y, w, h, side, color, label_str)
    r = 0.55;  % 环的半径

    switch side
        case 'left'
            center_x = x;
            center_y = y + h/2;
            th = linspace(pi/2, 3*pi/2, 50);
            arc_x = center_x + r*cos(th);
            arc_y = center_y + r*sin(th);
            text_x = center_x - r - 0.3;
            text_y = center_y;
            text_align = 'right';
        case 'top'
            center_x = x + w/2;
            center_y = y + h;
            th = linspace(0, pi, 50);
            arc_x = center_x + r*cos(th);
            arc_y = center_y + r*sin(th);
            text_x = center_x;
            text_y = center_y + r + 0.35;
            text_align = 'center';
        case 'right'
            center_x = x + w;
            center_y = y + h/2;
            th = linspace(-pi/2, pi/2, 50);
            arc_x = center_x + r*cos(th);
            arc_y = center_y + r*sin(th);
            text_x = center_x + r + 0.35;
            text_y = center_y;
            text_align = 'left';
    end

    % 画弧线
    plot(arc_x, arc_y, '-', 'LineWidth', 2.2, 'Color', color);

    % 画箭头（弧线中点处）
    arr_idx = round(length(th) * 0.5);
    arr_x = arc_x(arr_idx); arr_y = arc_y(arr_idx);
    arr_dx = arc_x(arr_idx+1) - arc_x(arr_idx-1);
    arr_dy = arc_y(arr_idx+1) - arc_y(arr_idx-1);

    L_arr = sqrt(arr_dx^2 + arr_dy^2);
    if L_arr > 0
        ux = arr_dx/L_arr; uy = arr_dy/L_arr;
        aw = 0.22; ah = 0.18;
        px = arr_x - ah*ux; py = arr_y - ah*uy;
        nx = -uy*aw/2; ny = ux*aw/2;
        patch([arr_x, px+nx, px-nx], [arr_y, py+ny, py-ny], color, 'EdgeColor','none');
    end

    % 标签
    text(text_x, text_y, label_str, 'FontSize', 9.5, 'FontWeight','bold',...
        'HorizontalAlignment', text_align, 'Color', color*0.7);
end
