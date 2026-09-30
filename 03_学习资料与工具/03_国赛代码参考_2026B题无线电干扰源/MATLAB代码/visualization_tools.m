% visualization_tools -- 可视化工具集
% 生成论文所需图表的静态方法集合（检测点网格、覆盖、交会区域等）。

classdef visualization_tools
    methods (Static)
        %% 1. 检测点网格可视化
        function plot_detection_grid(P, d, R_domain)
            figure('Name', sprintf('检测点网格 (d=%dm)', d));

            plot(P(:,1), P(:,2), 'bo', 'MarkerSize', 10, 'LineWidth', 2);
            hold on;

            % 圆域边界
            theta = linspace(0, 2*pi, 100);
            plot(R_domain * cos(theta), R_domain * sin(theta), 'r-', 'LineWidth', 2);

            % 原点
            plot(0, 0, 'r*', 'MarkerSize', 15, 'LineWidth', 2);

            axis equal;
            grid on;
            xlabel('x (m)');
            ylabel('y (m)');
            title(sprintf('检测点网格 (d=%dm, n=%d)', d, size(P,1)));
            legend('检测点', '圆域边界', '原点', 'Location', 'best');
        end

        %% 2. 定位区域可视化
        function plot_localization(S1, theta1, S2, theta2, L, c_star, R_MEC)
            figure('Name', '交会定位');

            % 定位区域
            if ~isempty(L)
                fill(L(:,1), L(:,2), [0.8 0.9 1], 'EdgeColor', 'b', 'LineWidth', 2);
                hold on;
            end

            % 检测点
            plot(S1(1), S1(2), 'rs', 'MarkerSize', 12, 'LineWidth', 2);
            plot(S2(1), S2(2), 'rs', 'MarkerSize', 12, 'LineWidth', 2);

            % 方向线
            r_line = 100;
            plot([S1(1), S1(1) + r_line*cosd(theta1)], ...
                 [S1(2), S1(2) + r_line*sind(theta1)], 'r--', 'LineWidth', 1.5);
            plot([S2(1), S2(1) + r_line*cosd(theta2)], ...
                 [S2(2), S2(2) + r_line*sind(theta2)], 'r--', 'LineWidth', 1.5);

            % MEC
            if ~isempty(c_star)
                theta = linspace(0, 2*pi, 100);
                plot(c_star(1) + R_MEC * cos(theta), ...
                     c_star(2) + R_MEC * sin(theta), 'g-', 'LineWidth', 2);
                plot(c_star(1), c_star(2), 'go', 'MarkerSize', 10, 'LineWidth', 2);
            end

            axis equal;
            grid on;
            xlabel('x (m)');
            ylabel('y (m)');
            title('交会定位与最小包围圆');
            legend('定位区域', '检测点', '观测方向', '最小包围圆', '圆心', ...
                   'Location', 'best');
        end

        %% 3. 清除策略对比图
        function plot_clear_strategy
            figure('Name', '清除策略对比');

            R_MEC_range = linspace(0, 200, 100);

            direct = (R_MEC_range <= 20);
            sweep = (R_MEC_range > 20) & (R_MEC_range <= 84.0369);
            homing = (R_MEC_range > 84.0369);

            hold on;
            area(R_MEC_range, direct * 100, 'FaceColor', [0.8 1 0.8], 'EdgeColor', 'none');
            area(R_MEC_range, sweep * 50, 'FaceColor', [1 1 0.8], 'EdgeColor', 'none');
            area(R_MEC_range, homing * 25, 'FaceColor', [1 0.8 0.8], 'EdgeColor', 'none');

            % 拐点标记
            plot([20 20], [0 100], 'r--', 'LineWidth', 2);
            plot([84.0369 84.0369], [0 100], 'r--', 'LineWidth', 2);

            xlabel('R_{MEC} (m)');
            ylabel('相对效率');
            title('三路清除策略');
            legend('直接清除 (<=20m)', '扫掠清除 (20-84m)', 'Homing逼近 (>84m)', ...
                   'Location', 'best');
            grid on;
        end

        %% 4. 时间消耗对比图
        function plot_time_comparison
            figure('Name', '时间消耗对比');

            d_values = [1000, 1500];
            n_detect = [13, 8];
            t_detect = n_detect * 5;  % 假设每点 5s

            bar(d_values, t_detect);
            xlabel('网格间距 d (m)');
            ylabel('检测时间 (s)');
            title('双轨网格时间对比');
            grid on;

            for i = 1:length(d_values)
                text(d_values(i), t_detect(i) + 2, sprintf('%d点', n_detect(i)), ...
                     'HorizontalAlignment', 'center');
            end
        end

        %% 5. 下界对照图
        function plot_lower_bound(actual_time, lower_bound)
            figure('Name', '移动时间下界对照');

            categories = {'实际移动时间', '理论下界'};
            times = [actual_time, lower_bound];

            bar(times);
            set(gca, 'XTickLabel', categories);
            ylabel('时间 (s)');
            title('移动时间下界验证');
            grid on;

            % 数值标注
            for i = 1:length(times)
                text(i, times(i) + 20, sprintf('%.1f s', times(i)), ...
                     'HorizontalAlignment', 'center');
            end

            % 下界参考线
            hold on;
            plot([0.5 2.5], [lower_bound lower_bound], 'r--', 'LineWidth', 2);
            legend('实际值', '下界', 'Location', 'best');
        end

        %% 6. Q4 外扩环带可视化
        function plot_Q4_ring(P_base, P_extended, R_domain)
            figure('Name', 'Q4 外扩环带');

            P_ring = setdiff(P_extended, P_base, 'rows');

            plot(P_base(:,1), P_base(:,2), 'bo', 'MarkerSize', 10, 'LineWidth', 2);
            hold on;
            plot(P_ring(:,1), P_ring(:,2), 'rs', 'MarkerSize', 10, 'LineWidth', 2);

            % 圆域边界
            theta = linspace(0, 2*pi, 100);
            plot(R_domain * cos(theta), R_domain * sin(theta), 'k--', 'LineWidth', 1.5);

            % 外扩边界
            margin = 1000 / sqrt(3);
            R_outer = R_domain + margin;
            plot(R_outer * cos(theta), R_outer * sin(theta), 'r--', 'LineWidth', 1.5);

            axis equal;
            grid on;
            xlabel('x (m)');
            ylabel('y (m)');
            title('Q4 外扩环带');
            legend('基础格点', '环带格点', '圆域边界', '外扩边界', ...
                   'Location', 'best');
        end

        %% 7. 批量导出所有图表
        function export_all_figures(output_dir)
            if nargin < 1
                output_dir = './figures';
            end

            if ~exist(output_dir, 'dir')
                mkdir(output_dir);
            end

            fig_list = findobj('Type', 'figure');
            for i = 1:length(fig_list)
                fig = fig_list(i);
                fig_name = get(fig, 'Name');
                if isempty(fig_name)
                    fig_name = sprintf('figure_%d', i);
                end

                % 保存为 PNG
                filename = fullfile(output_dir, [fig_name, '.png']);
                saveas(fig, filename);
                fprintf('  已保存: %s\n', filename);
            end

            fprintf(' 所有图表已导出到 %s\n', output_dir);
        end
    end
end
