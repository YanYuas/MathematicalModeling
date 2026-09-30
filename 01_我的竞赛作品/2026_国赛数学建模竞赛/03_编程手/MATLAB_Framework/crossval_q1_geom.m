% ========================================================================
% crossval_q1_geom -- Q1 几何的跨实现交叉验证（MATLAB 侧）
% MATLAB 侧 `Q1_geometry.intersect_wedges` 用 polyshape 布尔求交；
% Python 侧 `q1_main.py` 用射线两两求交 + 角域过滤 + Andrew 凸包。
% 本脚本对同一批楔形配置算出 (R_MEC, D, area, nv)，交给 Python 驱动逐位比对。
% 本版同时输出原始与截断两套结果（Python 侧做同样处理、两组分别比对）：

function crossval_q1_geom(cases_path, out_path)
    C = jsondecode(fileread(cases_path));
    R = C.R_domain;
    n = numel(C.cases);
    out = struct('name', {}, ...
        'raw_R', {}, 'raw_D', {}, 'raw_area', {}, 'raw_nv', {}, 'raw_empty', {}, ...
        'clip_R', {}, 'clip_D', {}, 'clip_nv', {}, 'clip_empty', {});
    for i = 1:n
        cs = C.cases(i);
        st = cs.stations;
        th = cs.thetas(:);
        ep = cs.eps(:);
        wedges = struct('station', {}, 'theta_deg', {}, 'epsilon_deg', {});
        for k = 1:size(st, 1)
            wedges(k).station = st(k, :);
            wedges(k).theta_deg = th(k);
            wedges(k).epsilon_deg = ep(k);
        end

        L = Q1_geometry.intersect_wedges(wedges);        % 原始交（MATLAB 侧有 5000 m 边界）
        rec = struct('name', cs.name, ...
            'raw_R', NaN, 'raw_D', NaN, 'raw_area', NaN, 'raw_nv', 0, 'raw_empty', isempty(L), ...
            'clip_R', NaN, 'clip_D', NaN, 'clip_nv', 0, 'clip_empty', true);
        if ~isempty(L)
            [~, r0] = Q1_geometry.minimum_enclosing_circle(L);
            rec.raw_R = r0;
            rec.raw_D = Q1_geometry.polygon_diameter(L);
            x = L(:, 1); y = L(:, 2);
            rec.raw_area = abs(sum(x .* circshift(y, -1) - circshift(x, -1) .* y)) / 2;
            rec.raw_nv = size(L, 1);

            % 与 triangulate_source 里的 clip_to_domain 完全一致：只保留圆域内的顶点
            d = sqrt(sum(L .^ 2, 2));
            Lc = L(d <= R + 1e-9, :);
            if ~isempty(Lc)
                [~, rc] = Q1_geometry.minimum_enclosing_circle(Lc);
                rec.clip_R = rc;
                rec.clip_D = Q1_geometry.polygon_diameter(Lc);
                rec.clip_nv = size(Lc, 1);
                rec.clip_empty = false;
            end
        end
        out(i) = rec;
    end
    fid = fopen(out_path, 'w');
    if fid <= 0
        error('crossval_q1_geom: 无法写入 %s', out_path);
    end
    fprintf(fid, '%s', jsonencode(out));
    fclose(fid);
    fprintf('MATLAB 侧完成 %d 个案例 -> %s\n', n, out_path);
end
