function P = generate_radial_grid(d_inner, R_domain, r_outer, phase_inner, phase_outer)
%GENERATE_RADIAL_GRID 生成径向布点集（Q3 用；三角格的替代档）。
%   P = GENERATE_RADIAL_GRID(d_inner, R_domain, r_outer)
%   P = GENERATE_RADIAL_GRID(d_inner, R_domain, r_outer, phase_inner, phase_outer)
%   形态：中心 1 点 + 内环 6 点（半径 d_inner）+ 外环 6 点（半径 r_outer），
%   两环默认错开 30度（填角，显著改善覆盖）。
%   本档的收益来自巡回长度：13 点集的开放巡回由 r_outer 决定，

    if nargin < 4 || isempty(phase_inner), phase_inner = 0;      end
    if nargin < 5 || isempty(phase_outer), phase_outer = pi / 6; end

    if r_outer > R_domain
        error('外环半径 %.1f 超出目标圆域 %.1f', r_outer, R_domain);
    end
    if r_outer < d_inner
        error('外环半径 %.1f 小于内环 %.1f', r_outer, d_inner);
    end

    ang_in  = phase_inner + (0:5)' * pi / 3;
    ang_out = phase_outer + (0:5)' * pi / 3;

    P = [ 0, 0;
          d_inner * cos(ang_in),  d_inner * sin(ang_in);
          r_outer * cos(ang_out), r_outer * sin(ang_out) ];

    P = unique(P, 'rows', 'stable');

    fprintf('[网格] 径向布点：中心 + 6@%.1f(相 %.0f度) + 6@%.1f(相 %.0f度) -> %d 点\n', ...
        d_inner, phase_inner * 180 / pi, r_outer, phase_outer * 180 / pi, size(P, 1));
end
