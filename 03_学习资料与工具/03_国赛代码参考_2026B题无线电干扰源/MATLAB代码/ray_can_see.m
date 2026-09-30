% ray_can_see —— 声线过滤判据
%
% 问题：某频道只在格点 A 被听到过 1 次（示向度 theta，附件2 §7.2）。
%       现在机器狗在格点 p，还要不要测这个频道？
%       交会定位要 2 个观测（triangulate_source 只读前两条），
%       所以只有 p 能给出第 2 个观测时，这一次测量才有价值。
%
% 判据（保守）：
%   源必落在自 A 沿 theta 的射线 ∩ 圆域这一段上（它在 A 处被听到，
%   而干扰源在目标区域内）。示向度含 ±eps 误差，源可偏离轴线，
%   距 A 为 L 处横偏 ≤ L·sin(eps)。
%   若 p 到该射线段的最近距离 > R_sensor + L·sin(eps)，
%   则 p 与任何候选源的距离都 > R_sensor，此处不可能有第 2 个观测。
%
% 正确性（单边）：
%   只要 |p − 真源| ≤ R_sensor，就有 dist(p,锥) ≥ d − L·sin(eps) 且
%   dist(p,锥) ≤ |p − 真源|，d ≤ R_sensor + L·sin(eps)，必放行。
%   即：过滤永不丢掉真正的第 2 个观测。反向不要求（允许保守、少跳）。
%   正确性由 test_ray_filter.m 覆盖。
%
% 依赖一条假设：干扰源位于半径 R_domain 的圆域内（覆盖设计本就默认此假设）。
%   L 取 2·R_domain，而不取射线到圆域的出口长度：出口长度随偏角变化 L(δ)，
%   用中心射线的 L(0) 界定偏角射线上源的位置不成立（6000 例抽样中 1 例违例）。
%   该取值不可简化；改动后必须重跑 test_ray_filter。

function tf = ray_can_see(from_pos, theta_deg, at_pos, config)
    u = [cosd(theta_deg), sind(theta_deg)];
    % L 取整条直径，不依赖射线-圆域出口长度：出口长度随偏角变化，
    % 用中心射线的出口长度界定偏角射线上源的位置不成立。
    L = 2 * config.R_domain;
    d = point_seg_dist(at_pos, from_pos, from_pos + L * u);
    spread = L * sind(config.epsilon_deg);
    tf = d <= config.R_sensor + spread;
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
