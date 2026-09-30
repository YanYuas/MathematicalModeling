%% 线性规划 MATLAB 代码模板
% 使用 linprog 求解
% 标准形式：min f^T x  s.t. A*x <= b, Aeq*x = beq, lb <= x <= ub
% 注意：linprog 求最小值，求最大值时 f 取负

clear; clc;

%% 例题：生产计划问题
% max 3*x1 + 5*x2
% s.t. x1 + 2*x2 <= 8
%      2*x1 + x2 <= 10
%      x1, x2 >= 0

f = [-3; -5];  % 目标函数系数（取负求最大）
A = [1 2; 2 1];  % 不等式约束系数
b = [8; 10];     % 不等式约束右端
Aeq = [];        % 等式约束（无）
beq = [];
lb = [0; 0];     % 下界
ub = [inf; inf]; % 上界

% 求解
options = optimoptions('linprog', 'Display', 'iter');
[x, fval, exitflag, output] = linprog(f, A, b, Aeq, beq, lb, ub, options);

fprintf('========== 线性规划求解结果 ==========\n');
fprintf('最优解: x1 = %.4f, x2 = %.4f\n', x(1), x(2));
fprintf('最大利润: %.4f 元\n', -fval);
fprintf('迭代次数: %d\n', output.iterations);

%% 通用函数
% function [x, fval] = solve_lp(f, A, b, Aeq, beq, lb, ub, maximize)
%     if nargin < 8, maximize = false; end
%     if maximize, f = -f; end
%     [x, fval] = linprog(f, A, b, Aeq, beq, lb, ub);
%     if maximize, fval = -fval; end
% end

%% 运输问题示例
fprintf('\n========== 运输问题 ==========\n');

% 3个产地，4个销地
supply = [10; 20; 30];
demand = [15; 15; 15; 15];
cost = [8 7 5 6; 4 3 6 5; 7 5 4 3];

% 构建目标函数（12个变量）
f_trans = cost(:);

% 产量约束
Aeq_trans = zeros(7, 12);
beq_trans = [supply; demand];
for i = 1:3
    Aeq_trans(i, (i-1)*4+1:i*4) = 1;
end
for j = 1:4
    Aeq_trans(3+j, j:4:12) = 1;
end

lb_trans = zeros(12, 1);

[x_trans, fval_trans] = linprog(f_trans, [], [], Aeq_trans, beq_trans, lb_trans);

fprintf('最小总运费: %.2f\n', fval_trans);
fprintf('运输方案:\n');
for i = 1:3
    for j = 1:4
        val = x_trans((i-1)*4 + j);
        if val > 1e-6
            fprintf('  产地%d -> 销地%d: %.2f\n', i, j, val);
        end
    end
end
