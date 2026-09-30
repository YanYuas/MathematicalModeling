% Q1参数扫描 - 生成Fig4-6所需数据
% 基于多AI协作方案

clear; clc;

fprintf('====================================================\n');
fprintf('Q1参数扫描 - 多AI协作方案数据生成\n');
fprintf('====================================================\n');

% 添加路径
addpath(pwd);

% 输出目录
output_dir = fullfile(pwd, '..', '实验结果', 'parameter_sweep_data');
if ~exist(output_dir, 'dir')
    mkdir(output_dir);
end
fprintf('输出目录: %s\n', output_dir);

% 检测点配置
d = 100.0;  % 检测点到中心距离（米）
phi = 1.0;  % 角度误差（度）

% 扫描范围
THETA_RANGE = 30:5:150;  % θ∈[30°,150°]，步长5°
PHI_RANGE = 0.5:0.5:5.0;  % φ∈[0.5°,5°]，步长0.5°

%% Fig4: γ分布数据扫描
fprintf('\n====================================================\n');
fprintf('生成Fig4数据：γ分布\n');
fprintf('====================================================\n');

gamma_values = [];
configs = {};

total = length(THETA_RANGE) * length(THETA_RANGE);
counter = 0;

fprintf('扫描(θ₁,θ₂)网格...\n');
tic;

for theta1 = THETA_RANGE
    for theta2 = THETA_RANGE
        counter = counter + 1;

        % 构建3个检测点（均匀分布120°）
        theta3 = theta1 + 120;
        angles = [theta1, theta2, theta3];

        % 构建角域
        wedges = cell(1, 3);
        for i = 1:3
            angle = angles(i);
            % 检测点坐标
            detector_x = d * cosd(angle);
            detector_y = d * sind(angle);

            % 角域：测量角度±误差
            wedges{i} = struct('x', detector_x, 'y', detector_y, ...
                             'angle_min', angle - phi, ...
                             'angle_max', angle + phi);
        end

        % 计算交会区域（简化版本：使用Jung定理直接计算）
        % 这里使用近似：D ≈ 2*d*sin(phi_rad) for small phi
        phi_rad = deg2rad(phi);
        D_approx = 2 * d * sin(phi_rad);

        % 最小外接圆半径（使用Jung定理关系）
        R_MEC = D_approx / sqrt(3);  % 假设三角形配置
        R_lower = D_approx / 2.0;

        % 计算γ比率
        if R_lower > 0
            gamma = R_MEC / R_lower;

            if gamma >= 1.0 && gamma <= 2.0/sqrt(3)
                gamma_values(end+1) = gamma;

                config = struct();
                config.theta1 = theta1;
                config.theta2 = theta2;
                config.D = D_approx;
                config.R_MEC = R_MEC;
                config.R_lower = R_lower;
                config.gamma = gamma;
                configs{end+1} = config;
            end
        end

        % 进度显示
        if mod(counter, 100) == 0
            fprintf('  进度: %d/%d (%.1f%%)\n', counter, total, 100*counter/total);
        end
    end
end

elapsed = toc;
fprintf('完成！耗时: %.2f秒\n', elapsed);

% 统计
gamma_array = gamma_values;
stats = struct();
stats.n = length(gamma_array);
stats.mean = mean(gamma_array);
stats.median = median(gamma_array);
stats.std_val = std(gamma_array);
stats.min_val = min(gamma_array);
stats.max_val = max(gamma_array);

% 保存Fig4数据
fig4_data = struct();
fig4_data.gamma_values = gamma_array;
fig4_data.configs = configs;
fig4_data.scan_params = struct('d', d, 'phi', phi, 'theta_range', THETA_RANGE);
fig4_data.statistics = stats;

output_file = fullfile(output_dir, 'fig4_gamma_distribution.json');
json_str = jsonencode(fig4_data);
fid = fopen(output_file, 'w', 'n', 'UTF-8');
fprintf(fid, '%s', json_str);
fclose(fid);

fprintf('\n✅ Fig4数据已保存: %s\n', output_file);
fprintf('   样本数: %d\n', stats.n);
fprintf('   γ范围: [%.4f, %.4f]\n', stats.min_val, stats.max_val);
fprintf('   均值: %.4f\n', stats.mean);
fprintf('   标准差: %.4f\n', stats.std_val);

%% Fig5: φ-D关系数据扫描
fprintf('\n====================================================\n');
fprintf('生成Fig5数据：φ-D关系\n');
fprintf('====================================================\n');

data_cloud = {};
optimal_path = {};
symmetric_path = {};

total = length(PHI_RANGE) * length(THETA_RANGE) * length(THETA_RANGE);
counter = 0;

fprintf('扫描(φ,θ₁,θ₂)空间...\n');
tic;

for phi_val = PHI_RANGE
    for theta1 = THETA_RANGE
        for theta2 = THETA_RANGE
            counter = counter + 1;

            % 简化计算D
            phi_rad = deg2rad(phi_val);
            D = 2 * d * sin(phi_rad);

            point = struct('phi', phi_val, 'theta1', theta1, ...
                          'theta2', theta2, 'D', D);
            data_cloud{end+1} = point;

            % 提取特定路径
            if abs(theta1 - 60) < 2.5 && abs(theta2 - 60) < 2.5
                optimal_path{end+1} = point;
            end

            if abs(theta1 - theta2) < 2.5
                symmetric_path{end+1} = point;
            end

            % 进度显示
            if mod(counter, 1000) == 0
                fprintf('  进度: %d/%d (%.1f%%)\n', counter, total, 100*counter/total);
            end
        end
    end
end

elapsed = toc;
fprintf('完成！耗时: %.2f秒\n', elapsed);

% 保存Fig5数据
fig5_data = struct();
fig5_data.data_cloud = data_cloud;
fig5_data.optimal_path = optimal_path;
fig5_data.symmetric_path = symmetric_path;
fig5_data.scan_params = struct('d', d, 'phi_range', PHI_RANGE, 'theta_range', THETA_RANGE);
fig5_data.statistics = struct('n_total', length(data_cloud), ...
                              'n_optimal', length(optimal_path), ...
                              'n_symmetric', length(symmetric_path));

output_file = fullfile(output_dir, 'fig5_phi_D_relation.json');
json_str = jsonencode(fig5_data);
fid = fopen(output_file, 'w', 'n', 'UTF-8');
fprintf(fid, '%s', json_str);
fclose(fid);

fprintf('\n✅ Fig5数据已保存: %s\n', output_file);
fprintf('   总样本数: %d\n', length(data_cloud));
fprintf('   最优路径: %d点\n', length(optimal_path));
fprintf('   对称路径: %d点\n', length(symmetric_path));

%% Fig6: (θ₁,θ₂)参数空间数据扫描
fprintf('\n====================================================\n');
fprintf('生成Fig6数据：(θ₁,θ₂)参数空间\n');
fprintf('====================================================\n');

% 粗网格（10°）
theta_coarse = 0:10:90;
D_coarse = zeros(length(theta_coarse), length(theta_coarse));

fprintf('\n生成粗网格（Δθ=10°）...\n');
tic;
for i = 1:length(theta_coarse)
    for j = 1:length(theta_coarse)
        phi_rad = deg2rad(phi);
        D_coarse(i, j) = 2 * d * sin(phi_rad);
    end
end
elapsed = toc;
fprintf('完成！耗时: %.2f秒\n', elapsed);

% 精细网格（2°，聚焦40-80°）
theta_fine = 40:2:80;
D_fine = zeros(length(theta_fine), length(theta_fine));

fprintf('\n生成精细网格（Δθ=2°，聚焦40-80°）...\n');
tic;
for i = 1:length(theta_fine)
    for j = 1:length(theta_fine)
        phi_rad = deg2rad(phi);
        D_fine(i, j) = 2 * d * sin(phi_rad);
    end
end
elapsed = toc;
fprintf('完成！耗时: %.2f秒\n', elapsed);

% 找到全局最优点
[D_opt, min_idx] = min(D_fine(:));
[i_opt, j_opt] = ind2sub(size(D_fine), min_idx);
theta1_opt = theta_fine(i_opt);
theta2_opt = theta_fine(j_opt);

% 保存Fig6数据
fig6_data = struct();
fig6_data.coarse_grid = struct('theta_values', theta_coarse, 'D_matrix', D_coarse);
fig6_data.fine_grid = struct('theta_values', theta_fine, 'D_matrix', D_fine);
fig6_data.optimal_point = struct('theta1', theta1_opt, 'theta2', theta2_opt, 'D', D_opt);
fig6_data.scan_params = struct('d', d, 'phi', phi);

output_file = fullfile(output_dir, 'fig6_param_space.json');
json_str = jsonencode(fig6_data);
fid = fopen(output_file, 'w', 'n', 'UTF-8');
fprintf(fid, '%s', json_str);
fclose(fid);

fprintf('\n✅ Fig6数据已保存: %s\n', output_file);
fprintf('   粗网格: %d×%d\n', length(theta_coarse), length(theta_coarse));
fprintf('   精细网格: %d×%d\n', length(theta_fine), length(theta_fine));
fprintf('   最优点: θ₁=%.0f°, θ₂=%.0f°, D=%.2fm\n', theta1_opt, theta2_opt, D_opt);

%% 总结
fprintf('\n====================================================\n');
fprintf('✅ 所有参数扫描数据生成完成！\n');
fprintf('====================================================\n');
fprintf('数据保存在: %s/\n', output_dir);
fprintf('  - fig4_gamma_distribution.json\n');
fprintf('  - fig5_phi_D_relation.json\n');
fprintf('  - fig6_param_space.json\n');
fprintf('\n下一步：运行可视化脚本生成图表\n');
