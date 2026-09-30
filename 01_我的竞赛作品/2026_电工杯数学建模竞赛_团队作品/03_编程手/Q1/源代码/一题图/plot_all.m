% ============================================================
% 问题一：全部10个小区（5×2排列）
% 用法：MATLAB中直接运行，Ctrl+C复制图到Word
% ============================================================
clear; close all; clc;

d=0.05; lam=0.07; P_alpha=0.045; P_beta=0.10;
P=[(1-d)*(1-P_alpha)+lam, lam, lam; (1-d)*P_alpha, (1-d)*(1-P_beta), 0; 0, (1-d)*P_beta, (1-d)];

raw=[496,152,64; 408,136,64; 632,208,80; 368,120,56; 536,176,72;
     328,104,40; 592,192,80; 392,128,48; 504,168,64; 456,144,56];
names={'A','B','C','D','E','F','G','H','I','J'};

results=zeros(10,3,6);
for c=1:10
    N=raw(c,:)'; results(c,:,1)=N;
    for t=1:5, N=round(P*N); results(c,:,t+1)=N; end
end

c_self=[55,120,210]/255; c_semi=[235,150,45]/255; c_disab=[190,60,60]/255;

figure('Position',[80,40,1100,1480],'ToolBar','none');

for c=1:10
    subplot(5,2,c);
    self=squeeze(results(c,1,:)); semi=squeeze(results(c,2,:)); disab=squeeze(results(c,3,:));
    total=self+semi+disab;

    h=area(0:5,[self,semi,disab],'LineWidth',0.5);
    h(1).FaceColor=c_self; h(1).EdgeColor=c_self;
    h(2).FaceColor=c_semi; h(2).EdgeColor=c_semi;
    h(3).FaceColor=c_disab; h(3).EdgeColor=c_disab;

    hold on;
    for yr=1:6
        plot([yr-1,yr-1],[0,total(yr)],'--k','LineWidth',0.8);
    end
    plot(0:5, self,      '.k','MarkerSize',12);
    plot(0:5, self+semi, '.k','MarkerSize',12);
    plot(0:5, total,     '.k','MarkerSize',12);
    hold off;

    title(['小区 ',names{c}],'FontSize',11);
    if c>=9, xlabel('年份','FontSize',10); end
    if mod(c,2)==1, ylabel('人数','FontSize',10); end
    xticks(0:5); xlim([0,5]); grid on;
end

sgtitle('各小区三类老人数量变化 (第0–5年末)','FontSize',14,'FontWeight','bold');

ax_bottom=axes('Position',[0.2,0.003,0.6,0.02],'Visible','off'); hold(ax_bottom,'on');
p1=patch(ax_bottom,NaN,NaN,c_self,'EdgeColor','none');
p2=patch(ax_bottom,NaN,NaN,c_semi,'EdgeColor','none');
p3=patch(ax_bottom,NaN,NaN,c_disab,'EdgeColor','none');
legend(ax_bottom,[p1,p2,p3],{'自理','半失能','失能'},...
    'Orientation','horizontal','FontSize',11,'Box','off','Location','north');

fprintf('小区  第0年          第5年\n');
for c=1:10
    v0=squeeze(results(c,:,1))'; v5=squeeze(results(c,:,6))';
    fprintf(' %s   [%3d,%3d,%3d]   [%3d,%3d,%3d]\n',names{c},v0,v5);
end
