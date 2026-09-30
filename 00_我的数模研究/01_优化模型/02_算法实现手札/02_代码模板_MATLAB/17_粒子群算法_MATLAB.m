%% 粒子群算法 MATLAB 代码模板
% 求 Rosenbrock 函数 f(x,y) = (1-x)^2 + 100*(y-x^2)^2 的最小值
% 理论最优：(1, 1), f=0

clear; clc; close all;

%% 参数设置
pop_size = 30;          % 粒子数量
max_iter = 200;         % 最大迭代次数
n_dim = 2;              % 变量维度
w = 0.7;                % 惯性权重
c1 = 1.5;               % 个体学习因子
c2 = 1.5;               % 社会学习因子
bounds = [-5, 5];       % 变量范围（所有维度相同）

%% 目标函数
fitness_fun = @(x) (1 - x(1))^2 + 100 * (x(2) - x(1)^2)^2;

%% 初始化
% 位置
positions = bounds(1) + rand(pop_size, n_dim) * (bounds(2) - bounds(1));
% 速度（范围的20%）
v_max = (bounds(2) - bounds(1)) * 0.2;
velocities = -v_max + 2 * v_max * rand(pop_size, n_dim);

% 适应度
scores = arrayfun(@(i) fitness_fun(positions(i, :)), 1:pop_size)';

% 个体最优
pbest_pos = positions;
pbest_score = scores;

% 全局最优
[gbest_score, gbest_idx] = min(scores);
gbest_pos = positions(gbest_idx, :);

%% 主循环
history = zeros(max_iter, 1);

for iter = 1:max_iter
    % 更新速度
    r1 = rand(pop_size, n_dim);
    r2 = rand(pop_size, n_dim);
    velocities = w * velocities + ...
                 c1 * r1 .* (pbest_pos - positions) + ...
                 c2 * r2 .* (gbest_pos - positions);
    
    % 限制速度
    velocities = max(-v_max, min(v_max, velocities));
    
    % 更新位置
    positions = positions + velocities;
    
    % 边界处理
    positions = max(bounds(1), min(bounds(2), positions));
    
    % 评估
    scores = arrayfun(@(i) fitness_fun(positions(i, :)), 1:pop_size)';
    
    % 更新个体最优
    update_mask = scores < pbest_score;
    pbest_pos(update_mask, :) = positions(update_mask, :);
    pbest_score(update_mask) = scores(update_mask);
    
    % 更新全局最优
    [current_best, best_idx] = min(scores);
    if current_best < gbest_score
        gbest_score = current_best;
        gbest_pos = positions(best_idx, :);
    end
    
    history(iter) = gbest_score;
    
    if mod(iter, 20) == 0
        fprintf('迭代%3d: 最优值 = %.6f\n', iter, gbest_score);
    end
end

%% 结果
fprintf('\n========== 粒子群算法结果 ==========\n');
fprintf('最优解: x = %.6f, y = %.6f\n', gbest_pos(1), gbest_pos(2));
fprintf('最优值: f(x,y) = %.6f\n', gbest_score);
fprintf('理论最优: (1, 1), f=0\n');

%% 绘制收敛曲线
figure;
semilogy(history, 'b-', 'LineWidth', 1.5);  % 对数坐标
xlabel('迭代次数');
ylabel('最优值（对数坐标）');
title('粒子群算法收敛曲线（Rosenbrock函数）');
grid on;
saveas(gcf, 'PSO_MATLAB_convergence.png');

%% ========== 使用MATLAB自带粒子群工具箱 ==========
% fitness_fun = @(x) (1-x(1))^2 + 100*(x(2)-x(1)^2)^2;
% options = optimoptions('particleswarm', ...
%     'SwarmSize', 30, ...
%     'MaxIterations', 200, ...
%     'InertiaRange', [0.4, 0.9]);
% lb = [-5, -5]; ub = [5, 5];
% [x, fval] = particleswarm(fitness_fun, 2, lb, ub, options);
% fprintf('工具箱结果: x=%.6f, y=%.6f, f=%.6f\n', x(1), x(2), fval);

%% ========== 惯性权重线性递减策略 ==========
% w_max = 0.9; w_min = 0.4;
% for iter = 1:max_iter
%     w = w_max - (w_max - w_min) * iter / max_iter;
%     % ... 其余不变
% end
% 优点：前期全局搜索强，后期局部搜索强
