function cmp_grid_second_nearest
%CMP_GRID_SECOND_NEAREST 核对脚本：三角格 vs 径向档(1000,1500) 的两项指标。
%   输出"1-覆盖半径"与"第 2 近邻最大值"（含最坏点位置），用于验证换布点档
%   是否动到了这两项。一次性核对用，不属于主流程。
    R = 1800; step = 25;
    [X, Y] = meshgrid(-R:step:R, -R:step:R);
    S = [X(:), Y(:)];
    S = S(sum(S.^2, 2) <= R^2, :);
    % 边界环带加密（与 check_coverage 同法）
    th = linspace(0, 2*pi, 720);
    for rv = 1750:5:1800
        S = [S; rv*cos(th)', rv*sin(th)']; %#ok<AGROW>
    end
    fprintf('采样点 %d\n', size(S, 1));

    A = generate_triangular_grid(struct('d', 1000, 'R_domain', R, 'extend_for_Q4', false));
    B = generate_radial_grid(1000, R, 1500);
    fprintf('三角格 %d 点 | 径向档 %d 点\n', size(A,1), size(B,1));

    for k = 1:2
        if k == 1, P = A; nm = '三角格(d=1000)'; else, P = B; nm = '径向(1000,1500)'; end
        d1 = inf(size(S,1),1); d2 = inf(size(S,1),1);
        for i = 1:size(S,1)
            dd = sort(sqrt(sum((P - S(i,:)).^2, 2)));
            d1(i) = dd(1); d2(i) = dd(2);
        end
        [m1, i1] = max(d1); [m2, i2] = max(d2);
        fprintf('%-18s 1-覆盖半径 %.4f @ (%.1f, %.1f) | 第2近邻max %.4f @ (%.1f, %.1f)\n', ...
            nm, m1, S(i1,1), S(i1,2), m2, S(i2,1), S(i2,2));
    end
end
