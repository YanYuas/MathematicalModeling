% ============================================================
% 问题一：四张热力图（2×2）
% 竖轴：小区  横轴：年份  单位：人  带颜色标尺
% ============================================================
clear; close all; clc;

d=0.05; lam=0.07; P_alpha=0.045; P_beta=0.10;
P=[(1-d)*(1-P_alpha)+lam, lam, lam; (1-d)*P_alpha, (1-d)*(1-P_beta), 0; 0, (1-d)*P_beta, (1-d)];

raw=[496,152,64; 408,136,64; 632,208,80; 368,120,56; 536,176,72;
     328,104,40; 592,192,80; 392,128,48; 504,168,64; 456,144,56];
names={'A','B','C','D','E','F','G','H','I','J'};

n_comm=10; n_years=6;

data_self=zeros(n_comm,n_years); data_semi=zeros(n_comm,n_years);
data_dis=zeros(n_comm,n_years); data_total=zeros(n_comm,n_years);

for c=1:n_comm
    N=raw(c,:)';
    data_self(c,1)=N(1); data_semi(c,1)=N(2);
    data_dis(c,1)=N(3); data_total(c,1)=sum(N);
    for t=1:5
        N=round(P*N);
        data_self(c,t+1)=N(1); data_semi(c,t+1)=N(2);
        data_dis(c,t+1)=N(3); data_total(c,t+1)=sum(N);
    end
end

datasets={data_total, data_self, data_semi, data_dis};
titles={'老人总数','自理老人总数','半失能老人总数','失能老人总数'};

% 构建自定义colormap (256色，蓝色系)
n_cmap=256;
cmap=zeros(n_cmap,3);
for i=1:n_cmap
    t=(i-1)/(n_cmap-1);
    cmap(i,:)=[0.94-0.55*t^0.6, 0.95-0.48*t^0.5, 0.96-0.22*t^0.4];
end

fnames={'heatmaps/q1_total.png','heatmaps/q1_self.png','heatmaps/q1_semi.png','heatmaps/q1_dis.png'};

for k=1:4
    figure('Position',[100+30*k,80,620,680],'Color','w');
    data=datasets{k};
    vmin=min(data(:)); vmax=max(data(:));

    imagesc(data,[vmin,vmax]);
    colormap(gca,cmap);

    for i=1:n_comm
        for j=1:n_years
            val=data(i,j);
            text(j,i,num2str(val),'HorizontalAlignment','center',...
                'VerticalAlignment','middle','FontSize',9,'FontWeight','bold','Color',[0 0 0]);
        end
    end

    pbaspect([1.6 1 1]);

    set(gca,'XTick',1:n_years,'XTickLabel',{'0','1','2','3','4','5'},...
            'YTick',1:n_comm,'YTickLabel',names,'FontSize',10,...
            'YDir','normal');
    xlabel('年份','FontSize',12);
    ylabel('小区','FontSize',12);
    title(titles{k},'FontSize',14,'FontWeight','bold');

    cb=colorbar('eastoutside');
    cb.FontSize=10;
    ylabel(cb,'人数','FontSize',11);

    exportgraphics(gcf,fnames{k},'Resolution',200);
    fprintf('已保存: %s\n',fnames{k});
end
