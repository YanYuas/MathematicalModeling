function source_info = triangulate_source(observations, config)
%TRIANGULATE_SOURCE 由两个观测的角域交会定位干扰源。
%   source_info = TRIANGULATE_SOURCE(observations, config)
%   只取前两个观测构造角域，求交后截断到目标圆域，再取最小包围圆。
%   观测不足两个、或交会/截断失败时返回 []（由调用方决定是否等待更多观测）。
%
%   输出字段: channel / L / c_star / R_MEC / D / discovered_at

    source_info = [];
    if numel(observations) < 2
        return;
    end

    try
        obs1 = observations(1);
        obs2 = observations(2);
        if ~isfield(obs1, 'position') || ~isfield(obs2, 'position')
            return;
        end

        wedge1 = struct('station', [obs1.position(1), obs1.position(2)], ...
                        'theta_deg', obs1.svd_deg, ...
                        'epsilon_deg', config.epsilon_deg);
        wedge2 = struct('station', [obs2.position(1), obs2.position(2)], ...
                        'theta_deg', obs2.svd_deg, ...
                        'epsilon_deg', config.epsilon_deg);

        L = Q1_geometry.intersect_wedges([wedge1; wedge2]);
        if isempty(L)
            return;
        end

        L = clip_to_domain(L, config.R_domain);
        if isempty(L)
            return;
        end

        [c_star, R_MEC] = Q1_geometry.minimum_enclosing_circle(L);
        D = Q1_geometry.polygon_diameter(L);

        source_info = struct();
        source_info.channel       = obs1.channel;
        source_info.L             = L;
        source_info.c_star        = c_star;
        source_info.R_MEC         = R_MEC;
        source_info.D             = D;
        source_info.discovered_at = [obs1.position_id, obs2.position_id];
    catch
        source_info = [];
    end
end


function L_clipped = clip_to_domain(L, R)
%CLIP_TO_DOMAIN 把多边形与圆域 D(0,R) 求交。
%   必须是真正的多边形求交 —— 只丢掉圆外顶点会改变形状（细长交会区会被削成
%   开链甚至两点，进而使 R_MEC 假性偏小）。详见《Q3 调优经验与补丁记录》P-7。
%   圆的边界用外切正多边形，半径放大 1/cos(pi/N)，以免误删圆内点。

    if size(L, 1) < 3
        L_clipped = L;
        return;
    end

    N = 720;
    th = (0:N - 1)' * (2 * pi / N);
    Rc = R / cos(pi / N);
    circ = [Rc * cos(th), Rc * sin(th)];

    try
        p = intersect( ...
            polyshape(L(:, 1), L(:, 2), 'Simplify', false, 'KeepCollinearPoints', true), ...
            polyshape(circ(:, 1), circ(:, 2), 'Simplify', false, 'KeepCollinearPoints', true), ...
            'KeepCollinearPoints', true);
    catch
        % 求交失败时退回"只保留圆内顶点"，宁可粗糙也不要中断本局
        L_clipped = L(sqrt(sum(L.^2, 2)) <= R + 1e-9, :);
        return;
    end

    if isempty(p) || all(area(p) <= 1e-12)
        L_clipped = zeros(0, 2);
        return;
    end

    % 两凸扇区交圆域理论上只有一个连通块；出现多块时取面积最大者，避免拼出假多边形
    if numel(p) > 1
        [~, k] = max(area(p));
        p = p(k);
    end

    L_clipped = p.Vertices;
end
