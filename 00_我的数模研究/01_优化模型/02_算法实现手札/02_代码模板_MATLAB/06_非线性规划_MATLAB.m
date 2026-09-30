%% 非线性规划 MATLAB 代码模板
% 使用 fmincon 求解
% min f(x)  s.t. A*x <= b, Aeq*x = beq, c(x) <= 0, ceq(x) = 0, lb <= x <= ub

clear; clc;

%% 例题1：基本非线性规划
fprintf('========== 非线性规划 ==========\n');

% 目标函数（写在函数里或匿名函数）
obj_fun = @(x) x(1)^2 + x(2)^2 - 4*x(1) - 6*x(2) + 10;

% 初始值
x0 = [1; 1];

% 线性约束：x1 + x2 <= 6
A = [1 1];
b = 6;
Aeq = [];
beq = [];

% 边界
lb = [0; 0];
ub = [inf; inf];

% 非线性约束（本例无）
nonlcon = [];

% 求解选项
options = optimoptions('fmincon', 'Display', 'iter', 'Algorithm', 'sqp');

[x, fval, exitflag, output] = fmincon(obj_fun, x0, A, b, Aeq, beq, lb, ub, nonlcon, options);

fprintf('最优解: x1 = %.4f, x2 = %.4f\n', x(1), x(2));
fprintf('最优值: %.4f\n', fval);
fprintf('迭代次数: %d\n', output.iterations);

%% 例题2：带非线性约束
fprintf('\n========== 带非线性约束 ==========\n');

obj_fun2 = @(x) -x(1)*x(2)*x(3);
x0_2 = [10; 10; 10];
A2 = [1 2 2];
b2 = 72;
lb2 = [0; 0; 0];

[x2, fval2] = fmincon(obj_fun2, x0_2, A2, b2, [], [], lb2, []);

fprintf('最优解: x1 = %.4f, x2 = %.4f, x3 = %.4f\n', x2(1), x2(2), x2(3));
fprintf('最大体积: %.4f\n', -fval2);

%% 非线性约束函数示例（需要单独写函数文件）
% function [c, ceq] = mycon(x)
%     c = [x(1)^2 + x(2)^2 - 25;    % 不等式约束 c <= 0
%          x(1)^2 - x(2)^2 - 1];
%     ceq = [];                      % 等式约束 ceq = 0
% end

%% 算法选择
% 'sqp' - 序列二次规划（默认，适合大多数问题）
% 'interior-point' - 内点法（适合大规模问题）
% 'trust-region-reflective' - 信赖域反射法（需要梯度）
% 'active-set' - 有效集法
