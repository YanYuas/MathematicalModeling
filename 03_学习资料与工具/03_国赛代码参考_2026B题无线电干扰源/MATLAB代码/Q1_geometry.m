% Q1_geometry -- 角域交会定位的几何内核
% 静态方法：角域求交（半平面/扇形布尔交）、最小包围圆（Welzl）、凸包、
% 多边形直径、点集去重等。Q1 与 Q3/Q4 共用同一套。

classdef Q1_geometry
    methods (Static)
        %% 角域求交：多个 {station, theta_deg, epsilon_deg} 的交集凸多边形
        function L = intersect_wedges(wedges)
            % 输入: wedges - 角域数组
            % 输出: L - 交集凸多边形顶点 (N×2)

            if isempty(wedges)
                L = [];
                return;
            end

            % 每个角域转成扇形多边形，逐个与当前区域求布尔交
            R_large = 5000;  % 初始"全平面"的半径
            result_poly = polyshape(R_large * [-1 1 1 -1], R_large * [-1 -1 1 1]);

            for i = 1:length(wedges)
                w = wedges(i);

                theta_min = w.theta_deg - w.epsilon_deg;
                theta_max = w.theta_deg + w.epsilon_deg;

                n_points = 50;  % 弧线采样点数
                angles = linspace(deg2rad(theta_min), deg2rad(theta_max), n_points);

                x_sector = [w.station(1), w.station(1) + R_large * cos(angles)];
                y_sector = [w.station(2), w.station(2) + R_large * sin(angles)];

                result_poly = intersect(result_poly, polyshape(x_sector, y_sector));
            end

            if result_poly.NumRegions == 0
                L = [];
            else
                L = [result_poly.Vertices(:,1), result_poly.Vertices(:,2)];
                if size(L, 1) > 1
                    L = Q1_geometry.unique_points(L, 1e-6);
                end
            end
        end

        %% 最小包围圆（Welzl 算法）
        function [c_star, R_MEC] = minimum_enclosing_circle(points)
            % 输入: points - 点集 (N×2)
            % 输出: c_star 圆心 [x,y]；R_MEC 半径

            if isempty(points)
                c_star = [0, 0];
                R_MEC = inf;
                return;
            end

            if size(points, 1) == 1
                c_star = points(1, :);
                R_MEC = 0;
                return;
            end

            % Welzl 递归算法
            P = points;
            [c_star, R_MEC] = Q1_geometry.welzl_recursive(P, [], size(P, 1));
        end

        %% 3. 凸多边形直径
        function [D, p1, p2] = polygon_diameter(points)
            % 输入: points - 凸多边形顶点 (Nx2)
            % 输出: D - 直径
            %       p1, p2 - 直径端点

            if size(points, 1) < 2
                D = 0;
                p1 = [];
                p2 = [];
                return;
            end

            % 暴力法 O(n^2) - 对于小规模问题足够
            n = size(points, 1);
            D = 0;
            p1 = points(1, :);
            p2 = points(1, :);

            for i = 1:n
                for j = i+1:n
                    dist = norm(points(i, :) - points(j, :));
                    if dist > D
                        D = dist;
                        p1 = points(i, :);
                        p2 = points(j, :);
                    end
                end
            end
        end

        %% 4. 点在角域内判定
        function inside = point_in_wedge(p, w)
            % 输入: p - 点 [x, y]
            %       w - 角域结构
            % 输出: inside - 是否在角域内

            dp = p - w.station;
            angle = atan2d(dp(2), dp(1));

            % 归一化到 [0, 360)
            angle = mod(angle, 360);
            theta_min = mod(w.theta_deg - w.epsilon_deg, 360);
            theta_max = mod(w.theta_deg + w.epsilon_deg, 360);

            % 判断（处理跨0度情况）
            if theta_min <= theta_max
                inside = (angle >= theta_min) && (angle <= theta_max);
            else
                inside = (angle >= theta_min) || (angle <= theta_max);
            end
        end

        %% 辅助函数

        % Welzl 递归核心
        function [c, r] = welzl_recursive(P, R, n)
            % P: 剩余点集
            % R: 边界点集
            % n: 剩余点数

            % 基础情况
            if n == 0 || length(R) == 3
                [c, r] = Q1_geometry.min_circle_trivial(R);
                return;
            end

            % 随机选一个点
            idx = randi(n);
            p = P(idx, :);

            % 交换到末尾
            P([idx, n], :) = P([n, idx], :);

            % 递归：不包含 p 的最小圆
            [c, r] = Q1_geometry.welzl_recursive(P, R, n-1);

            % 如果 p 在圆内，返回
            if norm(p - c) <= r + 1e-9
                return;
            end

            % p 在圆外，p 必在边界上
            R_new = [R; p];
            [c, r] = Q1_geometry.welzl_recursive(P, R_new, n-1);
        end

        % 0/1/2/3 点的最小包围圆
        function [c, r] = min_circle_trivial(R)
            n = size(R, 1);

            if n == 0
                c = [0, 0];
                r = 0;
            elseif n == 1
                c = R(1, :);
                r = 0;
            elseif n == 2
                c = (R(1, :) + R(2, :)) / 2;
                r = norm(R(1, :) - R(2, :)) / 2;
            else  % n == 3
                % 三点的外接圆
                [c, r] = Q1_geometry.circumcircle(R(1,:), R(2,:), R(3,:));
            end
        end

        % 三点外接圆
        function [c, r] = circumcircle(p1, p2, p3)
            ax = p1(1); ay = p1(2);
            bx = p2(1); by = p2(2);
            cx = p3(1); cy = p3(2);

            D = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by));

            if abs(D) < 1e-10
                % 三点共线，退化为两点
                [c, r] = Q1_geometry.min_circle_trivial([p1; p2]);
                return;
            end

            ux = ((ax^2 + ay^2) * (by - cy) + (bx^2 + by^2) * (cy - ay) + (cx^2 + cy^2) * (ay - by)) / D;
            uy = ((ax^2 + ay^2) * (cx - bx) + (bx^2 + by^2) * (ax - cx) + (cx^2 + cy^2) * (bx - ax)) / D;

            c = [ux, uy];
            r = norm(p1 - c);
        end

        % 点集去重
        function unique_pts = unique_points(points, tol)
            if size(points, 1) <= 1
                unique_pts = points;
                return;
            end

            unique_pts = points(1, :);
            for i = 2:size(points, 1)
                p = points(i, :);
                is_duplicate = false;
                for j = 1:size(unique_pts, 1)
                    if norm(p - unique_pts(j, :)) < tol
                        is_duplicate = true;
                        break;
                    end
                end
                if ~is_duplicate
                    unique_pts = [unique_pts; p];
                end
            end
        end
    end
end
