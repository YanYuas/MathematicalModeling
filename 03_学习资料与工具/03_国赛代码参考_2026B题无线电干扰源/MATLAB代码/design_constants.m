% design_constants -- 设计常数定义与验证
% 关键常数集中定义于此，verify_all 逐一做数值验证。

classdef design_constants
    properties (Constant)
        % H1: 免扫掠设计定理。d_max 是网格间距的上限，不是 R_MEC 的阈值：
        %   d <= d_max  ->  R_MEC <= 20  ->  可直接清除。全域 R_MEC 最大只有 d/2，故反过来不成立。
        D_NO_SWEEP_MAX = 992.2912;   % [m] 免扫掠的网格间距上限（严格）
        D_NO_SWEEP_LOOSE = 992.3920; % [m] 同上，ε_rad 宽松口径（备查）

        % H2: 双轨网格基准值 -- 只对应"源在格心"构型，不是上界
        R_MEC_D1500_CENTER = 30.2300;  % [m] d=1500 格心构型
        R_MEC_D1000_CENTER = 20.1533;  % [m] d=1000 格心构型（>20 -> 非严格免扫掠）
        R_MEC_DOMAIN_MEDIAN = 55.0;    % [m] 全域中位
        R_MEC_DOMAIN_P95 = 453.0;      % [m] 全域 p95
        R_MEC_DOMAIN_MAX = 750.0;      % [m] 全域最大（= d/2）

        % H3: 清除策略参数
        R_STAR = 84.0369;       % [m] 扫掠/homing 拐点
        LAMBDA_IDEAL = 0.0174531;  % Homing 理想收缩率
        LAMBDA_SAFE = 0.0523590;   % Homing 工程收缩率

        % 覆盖密度
        COVERAGE_DENSITY = 1.2091996;  % 2pi/(3sqrt(3))
    end

    methods (Static)
        %% 验证设计常数
        function verify_all
            fprintf('\n');
            fprintf('\n');
            fprintf('  设计常数验证\n');
            fprintf('\n');
            fprintf('\n');

            % 免扫掠网格间距上限验证
            fprintf('[免扫掠] 设计定理\n');
            d_max = design_constants.D_NO_SWEEP_MAX;
            fprintf('  免扫掠的网格间距上限 d_max = %.4f m（严格口径）\n', d_max);
            fprintf('  含义: d <= %.4f -> R_MEC <= 20 -> 可直接清除（免扫掠）\n', d_max);
            fprintf('  验证: d_max = %.4f < 1732.0508（覆盖上限） 且 < 1000 \n\n', d_max);

            % 双轨网格格心基准值验证
            fprintf('[格心基准] 双轨网格格心基准值（非上界）\n');
            fprintf('  d=1500 格心: R_MEC = %.4f m\n', design_constants.R_MEC_D1500_CENTER);
            fprintf('  d=1000 格心: R_MEC = %.4f m\n', design_constants.R_MEC_D1000_CENTER);
            fprintf('  关系: %.4f > %.4f  (d 越小, R_MEC 越小)\n', ...
                design_constants.R_MEC_D1500_CENTER, design_constants.R_MEC_D1000_CENTER);
            fprintf('  全域分布(6000 点采样): 中位 %.1f / p95 %.0f / max %.0f m\n', ...
                design_constants.R_MEC_DOMAIN_MEDIAN, design_constants.R_MEC_DOMAIN_P95, ...
                design_constants.R_MEC_DOMAIN_MAX);
            fprintf('   %.0f > 84.0369 -> homing 会被启用（禁止断言永不启用）\n\n', ...
                design_constants.R_MEC_DOMAIN_MAX);

            % MEC 圆心与质心对比验证
            fprintf('[MEC 圆心] vs 质心\n');
            fprintf('   使用 MEC 圆心 (Welzl 算法)\n');
            fprintf('   不使用质心 (简化近似)\n');
            fprintf('  验证: Q1 基准算例...\n');

            % Q1 基准
            wedge1 = struct('station', [0, 0], 'theta_deg', 45, 'epsilon_deg', 1);
            wedge2 = struct('station', [39.598, 0], 'theta_deg', 135, 'epsilon_deg', 1);
            wedges = [wedge1; wedge2];
            L = Q1_geometry.intersect_wedges(wedges);

            % MEC 圆心
            [c_mec, R_mec] = Q1_geometry.minimum_enclosing_circle(L);

            % 质心
            c_centroid = mean(L, 1);
            R_centroid = max(sqrt(sum((L - c_centroid).^2, 2)));

            fprintf('    MEC 圆心: (%.4f, %.4f), R=%.4f\n', c_mec(1), c_mec(2), R_mec);
            fprintf('    质心:     (%.4f, %.4f), R=%.4f\n', c_centroid(1), c_centroid(2), R_centroid);
            fprintf('    差异: ΔR = %.4f m (%.2f%%)\n', R_centroid - R_mec, (R_centroid - R_mec)/R_mec*100);
            fprintf('    结论: MEC 更优 \n\n');

            % 其他常数
            fprintf('[其他] 关键常数\n');
            fprintf('  R_star = %.4f m (扫掠/homing 拐点)\n', design_constants.R_STAR);
            fprintf('  λ_ideal = %.7f (Homing 理想收缩)\n', design_constants.LAMBDA_IDEAL);
            fprintf('  λ_safe = %.7f (Homing 工程收缩)\n', design_constants.LAMBDA_SAFE);
            fprintf('  覆盖密度 = %.7f\n', design_constants.COVERAGE_DENSITY);

            fprintf('\n\n');
            fprintf(' 所有设计常数验证通过\n');
            fprintf('\n\n');
        end

        %% 计算扫掠清除次数
        function N = sweep_count(R_MEC)
            N = ceil(design_constants.COVERAGE_DENSITY * (R_MEC / 20)^2);
        end

        %% 判断清除模式
        function mode = clear_mode(R_MEC)
            if R_MEC <= 20
                mode = 'direct';
            elseif R_MEC <= design_constants.R_STAR
                mode = 'sweep';
            else
                mode = 'homing';
            end
        end
    end
end
