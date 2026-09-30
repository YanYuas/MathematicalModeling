%% 遗传算法 MATLAB 代码模板
% 求 f(x) = x * sin(10*pi*x) + 2 在 [-1, 2] 上的最大值
% 二进制编码 + 轮盘赌选择 + 单点交叉 + 位翻转变异

clear; clc; close all;

%% 参数设置
pop_size = 50;          % 种群大小
max_iter = 200;         % 最大迭代次数
gene_length = 20;       % 每个变量的基因长度
n_dim = 1;              % 变量维度
total_length = n_dim * gene_length;  % 总基因长度
crossover_rate = 0.8;   % 交叉概率
mutation_rate = 0.01;   % 变异概率
bounds = [-1, 2];       % 变量范围

%% 目标函数
% 注意：这里写函数句柄，也可以单独写函数文件
fitness_fun = @(x) x * sin(10 * pi * x) + 2;

%% 初始化种群
% 每个个体是一个二进制行向量
population = randi([0, 1], pop_size, total_length);

%% 主循环
best_history = zeros(max_iter, 1);
best_individual = [];
best_score = -inf;

for gen = 1:max_iter
    % 解码并计算适应度
    scores = zeros(pop_size, 1);
    for i = 1:pop_size
        x = decode(population(i, :), gene_length, n_dim, bounds);
        scores(i) = fitness_fun(x);
    end
    
    % 记录最优
    [current_best, best_idx] = max(scores);
    if current_best > best_score
        best_score = current_best;
        best_individual = population(best_idx, :);
    end
    best_history(gen) = best_score;
    
    % 轮盘赌选择
    scores_shifted = scores - min(scores) + 1e-6;  % 确保为正
    probs = scores_shifted / sum(scores_shifted);
    cum_probs = cumsum(probs);
    new_population = zeros(pop_size, total_length);
    for i = 1:pop_size
        r = rand();
        idx = find(cum_probs >= r, 1);
        new_population(i, :) = population(idx, :);
    end
    population = new_population;
    
    % 单点交叉
    for i = 1:2:pop_size
        if rand() < crossover_rate
            point = randi([1, total_length - 1]);
            parent1 = population(i, :);
            parent2 = population(min(i+1, pop_size), :);
            population(i, :) = [parent1(1:point), parent2(point+1:end)];
            population(min(i+1, pop_size), :) = [parent2(1:point), parent1(point+1:end)];
        end
    end
    
    % 位翻转变异
    mutation_mask = rand(pop_size, total_length) < mutation_rate;
    population = xor(population, mutation_mask);
    
    % 每20代输出
    if mod(gen, 20) == 0
        fprintf('第%3d代: 最优值 = %.6f\n', gen, best_score);
    end
end

%% 结果
best_x = decode(best_individual, gene_length, n_dim, bounds);
fprintf('\n========== 遗传算法结果 ==========\n');
fprintf('最优解: x = %.6f\n', best_x);
fprintf('最优值: f(x) = %.6f\n', best_score);

%% 绘制收敛曲线
figure;
plot(best_history, 'b-', 'LineWidth', 1.5);
xlabel('迭代次数');
ylabel('最优值');
title('遗传算法收敛曲线');
grid on;
saveas(gcf, 'GA_MATLAB_convergence.png');

%% 解码函数
function x = decode(chromosome, gene_length, n_dim, bounds)
    x = zeros(1, n_dim);
    for i = 1:n_dim
        gene = chromosome((i-1)*gene_length+1 : i*gene_length);
        int_val = bin2dec(num2str(gene));
        low = bounds(1);
        high = bounds(2);
        x(i) = low + int_val / (2^gene_length - 1) * (high - low);
    end
end

%% ========== 使用MATLAB自带GA工具箱 ==========
% 如果安装了Global Optimization Toolbox，可以直接用ga函数
% 
% fitness_fun = @(x) -(x * sin(10*pi*x) + 2);  % ga求最小，取负
% lb = -1; ub = 2;
% options = optimoptions('ga', 'PopulationSize', 50, 'MaxGenerations', 200);
% [x, fval] = ga(fitness_fun, 1, [], [], [], [], lb, ub, [], options);
% fprintf('工具箱结果: x=%.6f, f(x)=%.6f\n', x, -fval);
