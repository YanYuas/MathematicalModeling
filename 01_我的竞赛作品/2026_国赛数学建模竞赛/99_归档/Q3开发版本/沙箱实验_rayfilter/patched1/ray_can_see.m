% ========================================================================
% ray_can_see —— 声线过滤判据（沙箱实验）
%
% 问题：某频道只在格点 A 被听到过 1 次（示向度 theta，附件2 §7.2）。
%       现在机器狗在格点 p，还要不要测这个频道？
%       交会定位要 **2 个**观测（triangulate_source 只读前两条），
%       所以只有 p 能给出第 2 个观测时，这一次测量才有价值。
%
% 判据（保守）：
%   源必落在「自 A 沿 theta 的射线 ∩ 圆域」这一段上（它在 A 处被听到，
%   而干扰源在目标区域内）。示向度含 ±eps 误差 ⇒ 源可偏离轴线，
%   距 A 为 L 处横偏 ≤ L·sin(eps)。
%   若 p 到该射线段的最近距离 > R_sensor + L·sin(eps)，
%   则 p 与**任何**候选源的距离都 > R_sensor ⇒ 此处不可能有第 2 个观测。
%
% 正确性（单边）：
%   只要 |p − 真源| ≤ R_sensor，就有 dist(p,锥) ≥ d − L·sin(eps) 且
%   dist(p,锥) ≤ |p − 真源| ⇒ d ≤ R_sensor + L·sin(eps) ⇒ **必放行**。
%   即：过滤**永不**丢掉真正的第 2 个观测。反向不要求（允许保守、少跳）。
%   回归见 test_ray_filter.m。
%
% 依赖的假设：干扰源位于半径 R_domain 的圆域内（策略的覆盖设计已默认此假设）。
%   若源可能在域外，改用变体1（L = 2·R_domain，不依赖该假设，但更保守）。
% ========================================================================

function tf = ray_can_see(from_pos, theta_deg, at_pos, config)
    u = [cosd(theta_deg), sind(theta_deg)];
    % 变体1：L 取整条直径，**不依赖射线-圆域出口长度**。
    % 变体2 用出口长度更强，但被 test_ray_filter 证伪（出口长度随偏角变化，
    % 用中心射线的出口长度去界定偏角射线上源的位置是不成立的）。
    L = 2 * config.R_domain;
    d = point_seg_dist(at_pos, from_pos, from_pos + L * u);
    spread = L * sind(config.epsilon_deg);
    tf = d <= config.R_sensor + spread;
end

% 自 a（在圆内）沿单位方向 u 射出，与圆 |x| = R 的正向交点距离。
function L = ray_exit_len(a, u, R)
    b = dot(a, u);
    c = dot(a, a) - R^2;
    disc = b^2 - c;
    if disc <= 0
        L = R;                      % 数值兜底（a 在圆内时 disc > 0，走不到这里）
    else
        L = -b + sqrt(disc);
    end
    L = max(L, 0);
end

% 点到线段 [a, b] 的最近距离
function d = point_seg_dist(p, a, b)
    ab = b - a;
    denom = dot(ab, ab);
    if denom <= 0
        d = norm(p - a);
        return;
    end
    tt = max(0, min(1, dot(p - a, ab) / denom));
    d = norm(p - (a + tt * ab));
end
