%% 模拟退火算法 MATLAB 代码模板
% 求 f(x) = x * sin(10*pi*x) + 2 在 [-1, 2] 上的最大值

clear; clc; close all;

%% 参数设置
initial_temp = 100;     % 初始温度
cooling_rate = 0.99;    % 降温系数
min_temp = 1e-4;        % 最低温度
max_iter = 500;         % 最大迭代次数
step_size = 0.1;        % 邻域搜索步长
bounds = [-1, 2];       % 变量范围

%% 目标函数
fitness_fun = @(x) x * sin(10 * pi * x) + 2;

%% 初始化
current = bounds(1) + rand() * (bounds(2) - bounds(1));
current_val = fitness_fun(current);
best = current;
best_val = current_val;

T = initial_temp;
history = [];
temp_history = [];

%% 主循环
iteration = 0;
while T > min_temp && iteration < max_iter
    iteration = iteration + 1;
    
    % 生成新解（高斯扰动）
    new_solution = current + randn() * step_size;
    new_solution = max(bounds(1), min(bounds(2), new_solution));  % 边界处理
    new_val = fitness_fun(new_solution);
    
    % Metropolis准则
    delta_E = new_val - current_val;  % 最大化：正的更好
    if delta_E > 0
        % 新解更好，接受
        current = new_solution;
        current_val = new_val;
    else
        % 新解更差，以概率接受
        prob = exp(delta_E / T);
        if rand() < prob
            current = new_solution;
            current_val = new_val;
        end
    end
    
    % 更新最优
    if current_val > best_val
        best = current;
        best_val = current_val;
    end
    
    % 降温
    T = T * cooling_rate;
    
    history(end+1) = best_val;
    temp_history(end+1) = T;
    
    if mod(iteration, 50) == 0
        fprintf('迭代%4d: 温度=%.4f, 最优值=%.6f\n', iteration, T, best_val);
    end
end

%% 结果
fprintf('\n========== 模拟退火结果 ==========\n');
fprintf('最优解: x = %.6f\n', best);
fprintf('最优值: f(x) = %.6f\n', best_val);
fprintf('迭代次数: %d\n', iteration);

%% 绘图
figure;
subplot(1, 2, 1);
plot(history, 'b-', 'LineWidth', 1.5);
xlabel('迭代次数');
ylabel('最优值');
title('收敛曲线');
grid on;

subplot(1, 2, 2);
plot(temp_history, 'r-', 'LineWidth', 1.5);
xlabel('迭代次数');
ylabel('温度');
title('温度下降曲线');
grid on;

saveas(gcf, 'SA_MATLAB_result.png');

%% ========== 使用MATLAB自带模拟退火工具箱 ==========
% fitness_fun = @(x) -(x * sin(10*pi*x) + 2);  % 求最小
% options = optimoptions('simulannealbnd', ...
%     'InitialTemperature', 100, ...
%     'CoolingFcn', @temperature_exp, ...
%     'MaxIterations', 500);
% [x, fval] = simulannealbnd(fitness_fun, 0, -1, 2, options);
% fprintf('工具箱结果: x=%.6f, f(x)=%.6f\n', x, -fval);
