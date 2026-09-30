%% 整数规划 MATLAB 代码模板
% 使用 intlinprog 求解
% 标准形式：min f^T x  s.t. A*x <= b, Aeq*x = beq, lb <= x <= ub
% intcon 指定哪些变量是整数

clear; clc;

%% 例题1：指派问题
fprintf('========== 指派问题 ==========\n');

% 效率矩阵
cost = [3 8 9 4; 5 2 7 6; 9 5 4 8; 7 6 3 5];
n = size(cost, 1);

% 目标函数（16个变量，按行展开）
f = cost(:);

% 整数变量索引（全部为0-1变量）
intcon = 1:n*n;

% 约束：每人做一项工作
Aeq = zeros(2*n, n*n);
beq = ones(2*n, 1);
for i = 1:n
    Aeq(i, (i-1)*n+1:i*n) = 1;
end
for j = 1:n
    Aeq(n+j, j:n:n*n) = 1;
end

% 变量边界：0或1
lb = zeros(n*n, 1);
ub = ones(n*n, 1);

% 求解
[x, fval] = intlinprog(f, intcon, [], [], Aeq, beq, lb, ub);

fprintf('最小总时间: %.0f\n', fval);
fprintf('指派方案:\n');
for i = 1:n
    for j = 1:n
        if x((i-1)*n + j) > 0.5
            fprintf('  人%d -> 工作%d (时间%d)\n', i, j, cost(i,j));
        end
    end
end

%% 例题2：0-1背包问题
fprintf('\n========== 0-1背包问题 ==========\n');

weights = [2; 3; 4; 5; 6];
values = [3; 4; 5; 6; 7];
capacity = 10;
n_items = length(weights);

% 目标：最大化价值 → 最小化负价值
f_knap = -values;
intcon_knap = 1:n_items;

% 约束：总重量 <= 容量
A_knap = weights';
b_knap = capacity;

lb_knap = zeros(n_items, 1);
ub_knap = ones(n_items, 1);

[x_knap, fval_knap] = intlinprog(f_knap, intcon_knap, A_knap, b_knap, [], [], lb_knap, ub_knap);

fprintf('最大价值: %.0f\n', -fval_knap);
fprintf('选中物品:\n');
total_w = 0;
for i = 1:n_items
    if x_knap(i) > 0.5
        fprintf('  物品%d: 重量%d, 价值%d\n', i, weights(i), values(i));
        total_w = total_w + weights(i);
    end
end
fprintf('总重量: %d/%d\n', total_w, capacity);

%% 通用函数
% function [x, fval] = solve_ip(f, intcon, A, b, Aeq, beq, lb, ub, maximize)
%     if nargin < 9, maximize = false; end
%     if maximize, f = -f; end
%     [x, fval] = intlinprog(f, intcon, A, b, Aeq, beq, lb, ub);
%     if maximize, fval = -fval; end
% end
