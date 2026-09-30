% ============================================================
% 问题一：小区 I,J（1×2排列）
% ============================================================
clear; close all; clc;

d=0.05; lam=0.07; P_alpha=0.045; P_beta=0.10;
P=[(1-d)*(1-P_alpha)+lam, lam, lam; (1-d)*P_alpha, (1-d)*(1-P_beta), 0; 0, (1-d)*P_beta, (1-d)];

raw_all=[504,168,64; 456,144,56];
names_all={'I','J'};

c_self=[55,120,210]/255; c_semi=[235,150,45]/255; c_disab=[190,60,60]/255;

figure('Position',[100, 100, 1100, 275],'ToolBar','none');

for c=1:2
    N=raw_all(c,:)';
    results=zeros(3,6);
    results(:,1)=N;
    for t=1:5, N=round(P*N); results(:,t+1)=N; end

    self=results(1,:); semi=results(2,:); disab=results(3,:);
    total=self+semi+disab;

    subplot(1,2,c);
    h=area(0:5,[self',semi',disab'],'LineWidth',0.5);
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

    title(['小区 ',names_all{c}],'FontSize',13);
    xlabel('年份','FontSize',11);
    if c==1, ylabel('人数','FontSize',11); end
    xticks(0:5); xlim([0,5]); grid on;
end

sgtitle('小区 I–J 三类老人数量变化 (第0–5年末)','FontSize',14,'FontWeight','bold');

ax_bottom=axes('Position',[0.25,0.01,0.5,0.05],'Visible','off'); hold(ax_bottom,'on');
p1=patch(ax_bottom,NaN,NaN,c_self,'EdgeColor','none');
p2=patch(ax_bottom,NaN,NaN,c_semi,'EdgeColor','none');
p3=patch(ax_bottom,NaN,NaN,c_disab,'EdgeColor','none');
legend(ax_bottom,[p1,p2,p3],{'自理','半失能','失能'},...
    'Orientation','horizontal','FontSize',12,'Box','off','Location','north');
