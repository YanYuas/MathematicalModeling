function source_info = triangulate_source(observations, config)
%TRIANGULATE_SOURCE 由多个观测的角域交会定位干扰源。
%   source_info = TRIANGULATE_SOURCE(observations, config)
%   从"只取前两条观测"改为"用全部观测（上限 config.max_wedges）"。
%   原因：真机 6 局实测 T_vir 里移动占 74~78%，降 T̄ 必须降点数；而 25 点档把每源的
%   观测数压下来后，只用两条观测的 R_MEC 中位数从 25.5 m 涨到 36~52 m
%   -> homing/sweep 次数暴涨、8 种子里 2 局掉到 92.3%。
%   楔形交只会更紧：真源落在每一条楔形里 -> 多交一条只可能缩小 L（不会引入错误）。

    source_info = [];
    if numel(observations) < 2
        return;
    end

    if isfield(config, 'max_wedges') && ~isempty(config.max_wedges)
        n_use = min(numel(observations), config.max_wedges);
    else
        n_use = min(numel(observations), 6);
    end

    try
        obs = observations(1:n_use);

        wedges = repmat(struct('station', [0 0], 'theta_deg', 0, 'epsilon_deg', 1), n_use, 1);
        for i = 1:n_use
            if ~isfield(obs(i), 'position') || ~isfield(obs(i), 'svd_deg'), return; end
            wedges(i) = struct('station', [obs(i).position(1), obs(i).position(2)], ...
                               'theta_deg', obs(i).svd_deg, ...
                               'epsilon_deg', config.epsilon_deg);
        end

        L = Q1_geometry.intersect_wedges(wedges);
        if isempty(L)
            return;
        end

        L = clip_to_domain(L, config.R_domain);
        if isempty(L)
            return;
        end

        [c_star, R_MEC] = Q1_geometry.minimum_enclosing_circle(L);
        D = Q1_geometry.polygon_diameter(L);

        source_info = struct;
        source_info.channel       = obs(1).channel;
        source_info.L             = L;
        source_info.c_star        = c_star;
        source_info.R_MEC         = R_MEC;
        source_info.D             = D;
        source_info.n_wedges      = n_use;
        source_info.discovered_at = [obs.position_id];
    catch
        source_info = [];
    end
end


function L_clipped = clip_to_domain(L, R)
%CLIP_TO_DOMAIN 把多边形与圆域 D(0,R) 求交。
%   必须是真正的多边形求交 -- 只丢掉圆外顶点会改变形状（细长交会区会被削成
%   开链甚至两点，进而使 R_MEC 假性偏小）。。
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

    % 两凸扇区∩ 圆域理论上只有一个连通块；出现多块时取面积最大者，避免拼出假多边形
    if numel(p) > 1
        [~, k] = max(area(p));
        p = p(k);
    end

    L_clipped = p.Vertices;
end
