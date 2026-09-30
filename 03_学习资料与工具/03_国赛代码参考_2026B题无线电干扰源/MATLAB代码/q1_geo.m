function varargout = q1_geo(action, varargin)
%Q1_GEO  Q1 几何内核：角域(半平面表示) -> 定位区域 -> 直径 D -> 最小包围圆 R_MEC
%   所有图件均由本内核现算，不使用硬编码数字。
%   约定：角域 W_i = { P : angle(P - S_i, u_i) <= eps }，用三个半平面 a*x+b*y <= c 表示。
%
%   用法：
%     [poly, bounded, isEmpty] = q1_geo('regionFromSource', S, G, epsDeg)
%     [poly, bounded, isEmpty] = q1_geo('regionFromDirs',   S, dirs, epsDeg)
%     [D, R, center, gamma]    = q1_geo('polyStats', poly)
%     D                        = q1_geo('diameter', poly)
%     [R, center]              = q1_geo('mec', poly)

switch action
    case 'regionFromSource'
        [varargout{1:3}] = regionFromSource_(varargin{:});
    case 'regionFromDirs'
        [varargout{1:3}] = regionFromDirs_(varargin{:});
    case 'polyStats'
        [varargout{1:4}] = polyStats_(varargin{:});
    case 'diameter'
        varargout{1} = diameter_(varargin{1});
    case 'mec'
        [varargout{1:2}] = mec_(varargin{1});
    otherwise
        error('q1_geo:unknownAction', '未知动作：%s', action);
end
end

% =====================================================================
function [poly, bounded, isEmpty] = regionFromSource_(S, G, epsDeg)
% 角域中心方向：由站址指向真源
n = size(S, 1);
dirs = zeros(n, 2);
for i = 1:n
    d = G - S(i, :);
    dirs(i, :) = d / norm(d);
end
[poly, bounded, isEmpty] = regionFromDirs_(S, dirs, epsDeg);
end

function [poly, bounded, isEmpty] = regionFromDirs_(S, dirs, epsDeg)
n = size(S, 1);
% 视场盒：随几何尺度自适应
scale = max([max(abs(S(:))), 1]) * 20;
if nargin < 3, epsDeg = 1; end
% 若有交汇中心，收紧视场盒
B = scale;
poly = [-B -B; B -B; B B; -B B];
tol = 1e-12 * B;
for i = 1:n
    u = dirs(i, :) / norm(dirs(i, :));
    Sx = S(i, 1); Sy = S(i, 2);
    te = tan(epsDeg * pi / 180);
    K = u(1) * Sy - u(2) * Sx;
    M = u(1) * Sx + u(2) * Sy;
    hps = [ -u(2) - te * u(1),  u(1) - te * u(2),  K - te * M; ...
             u(2) - te * u(1), -u(1) - te * u(2), -K - te * M; ...
            -u(1),             -u(2),             -M ];
    for k = 1:3
        poly = clipPoly_(poly, hps(k, :), tol);
        if isempty(poly)
            bounded = true; isEmpty = true; return;
        end
    end
end
% 去重
poly = dedup_(poly, 1e-9 * B);
% 有界性：顶点是否落在视场盒边界上
bounded = ~any(abs(abs(poly(:, 1)) - B) < 1e-6 * B | abs(abs(poly(:, 2)) - B) < 1e-6 * B);
isEmpty = isempty(poly);
end

function poly = clipPoly_(poly, hp, tol)
if isempty(poly), return; end
if nargin < 3, tol = 1e-12; end
n = size(poly, 1);
out = zeros(0, 2);
for i = 1:n
    A = poly(i, :);
    B = poly(mod(i, n) + 1, :);
    fa = hp(1) * A(1) + hp(2) * A(2) - hp(3);
    fb = hp(1) * B(1) + hp(2) * B(2) - hp(3);
    if fa <= tol
        out(end + 1, :) = A; %#ok<AGROW>
    end
    if (fa < -tol && fb > tol) || (fa > tol && fb < -tol)
        t = fa / (fa - fb);
        out(end + 1, :) = A + t * (B - A); %#ok<AGROW>
    end
end
poly = out;
end

function P = dedup_(P, tol)
if isempty(P), return; end
keep = true(size(P, 1), 1);
for i = 1:size(P, 1)
    if ~keep(i), continue; end
    for j = i + 1:size(P, 1)
        if keep(j) && norm(P(i, :) - P(j, :)) < tol
            keep(j) = false;
        end
    end
end
P = P(keep, :);
end

function D = diameter_(poly)
D = 0;
for i = 1:size(poly, 1)
    for j = i + 1:size(poly, 1)
        D = max(D, norm(poly(i, :) - poly(j, :)));
    end
end
end

function [R, c] = mec_(poly)
% 最小包围圆：候选 = 所有点对的直径圆 + 所有三点对的外接圆
m = size(poly, 1);
R = Inf; c = [0 0];
if m == 0, return; end
if m == 1, R = 0; c = poly(1, :); return; end
cands = zeros(0, 3);
for i = 1:m
    for j = i + 1:m
        cc = (poly(i, :) + poly(j, :)) / 2;
        cands(end + 1, :) = [cc, norm(poly(i, :) - cc)]; %#ok<AGROW>
    end
end
for i = 1:m
    for j = i + 1:m
        for k = j + 1:m
            a = poly(i, :); b = poly(j, :); cc0 = poly(k, :);
            d = 2 * (a(1) * (b(2) - cc0(2)) + b(1) * (cc0(2) - a(2)) + cc0(1) * (a(2) - b(2)));
            if abs(d) < 1e-14, continue; end
            ux = ((a(1)^2 + a(2)^2) * (b(2) - cc0(2)) + (b(1)^2 + b(2)^2) * (cc0(2) - a(2)) + (cc0(1)^2 + cc0(2)^2) * (a(2) - b(2))) / d;
            uy = ((a(1)^2 + a(2)^2) * (cc0(1) - b(1)) + (b(1)^2 + b(2)^2) * (a(1) - cc0(1)) + (cc0(1)^2 + cc0(2)^2) * (b(1) - a(1))) / d;
            cands(end + 1, :) = [ux, uy, hypot(a(1) - ux, a(2) - uy)]; %#ok<AGROW>
        end
    end
end
for t = 1:size(cands, 1)
    cc = cands(t, 1:2); rr = cands(t, 3);
    if ~isfinite(rr) || rr >= R, continue; end
    if all(vecnorm(poly - cc, 2, 2) <= rr + 1e-9)
        R = rr; c = cc;
    end
end
end

function [D, R, c, gamma] = polyStats_(poly)
D = diameter_(poly);
[R, c] = mec_(poly);
if D > 0, gamma = R / (D / 2); else, gamma = NaN; end
end
