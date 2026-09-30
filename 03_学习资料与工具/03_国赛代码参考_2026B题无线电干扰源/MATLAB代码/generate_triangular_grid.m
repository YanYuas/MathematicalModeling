% generate_triangular_grid -- 三角格布点（中心 + 六边形层）
% 生成间距 d 的三角格并按圆域裁剪；extend_for_Q4 时额外保留一圈外扩环带。
% 外扩宽度取 margin = d（不是 d/sqrt(3)）：Q4 的 surrounding 条件用三最近邻，
% 第三近邻可达 d。
% 注：Q4 的实际路径走 Q4_extensions.generate_extended_grid，本分支只服务直调场景。

function P = generate_triangular_grid(params)
    d = params.d;                          % 网格间距 [m]
    R = params.R_domain;                   % 圆域半径 [m]
    extend_for_Q4 = params.extend_for_Q4;  % 是否外扩环带

    a1 = [d, 0];
    a2 = [d/2, sqrt(3)*d/2];

    margin = d;
    max_coord = R + margin;
    n_max = ceil(max_coord / d) + 1;

    % 生成格点
    points = [];
    for i = -n_max:n_max
        for j = -n_max:n_max
            p = i * a1 + j * a2;
            r = norm(p);

            % 圆域裁剪
            if r <= R
                points = [points; p];
            end

            % Q4 外扩环带
            if extend_for_Q4 && r > R && r <= R + margin
                points = [points; p];
            end
        end
    end

    % 去重（欧氏距离 < 1e-6）
    P = unique(points, 'rows', 'stable');

    fprintf('[网格] d=%.1f m, 生成 %d 个检测点', d, size(P, 1));
    if extend_for_Q4
        fprintf(' (含 Q4 外扩环带)');
    end
    fprintf('\n');
end
