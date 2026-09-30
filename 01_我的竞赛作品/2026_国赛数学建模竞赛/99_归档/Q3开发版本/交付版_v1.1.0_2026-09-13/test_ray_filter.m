% test_ray_filter —— 声线过滤的正确性回归（沙箱实验）
%
% 该过滤只有一条正确性要求：永不跳过真能给出第 2 个观测的格点。
% 保守（少跳）允许；激进（多跳）致命 —— 多跳会让频道拿不到第 2 个观测，
% 堕入阶段 C 的单方位 homing，甚至清不掉。
%
% 采样按真机条件：观测点 A、待判格点 p 都落在圆域内（径向档 13 点全在域内），
% 候选源也落在圆域内。暴力判据独立于被测实现：
%   源 s = A + t·[cos(θ+δ), sin(θ+δ)]，|δ| ≤ eps，|s| ≤ R_domain。
%   存在 s 使 dist(p, s) ≤ R_sensor，"看得到"。
%   断言：暴力说看得到，ray_can_see 必须放行（反向不要求）。
%
% 用法: test_ray_filter()
function test_ray_filter()
    config = struct('R_domain', 1800, 'R_sensor', 1000, 'epsilon_deg', 1);

    n_cases = 6000;
    n_t     = 600;
    n_delta = 13;

    rng(20260913);
    A     = sample_in_disk(n_cases, config.R_domain);
    P     = sample_in_disk(n_cases, config.R_domain);
    theta = rand(n_cases, 1) * 360;

    got  = false(n_cases, 1);
    want = false(n_cases, 1);
    for k = 1:n_cases
        got(k)  = ray_can_see(A(k, :), theta(k), P(k, :), config);
        want(k) = brute_can_see(A(k, :), theta(k), P(k, :), config, n_t, n_delta);
    end

    violated = find(want & ~got);
    fprintf('\n===== 声线过滤正确性回归 =====\n');
    fprintf('  用例 %d ｜ 暴力判"看得到" %d ｜ "看不到" %d\n', ...
        n_cases, nnz(want), nnz(~want));
    fprintf('  ray_can_see 放行率 %.1f%%（越低拦得越狠）\n', 100 * nnz(got) / n_cases);
    fprintf('  真能看到的案例里，过滤放行了 %.1f%%（漏放即违例）\n', ...
        100 * nnz(got & want) / max(1, nnz(want)));

    if isempty(violated)
        fprintf('  [PASS] 无违例：暴力说看得到时，过滤一律放行\n');
    else
        k = violated(1);
        fprintf('  [FAIL] %d 例违例 —— 过滤过激，会丢掉真正的第 2 个观测\n', numel(violated));
        fprintf('         例: A=(%.1f, %.1f) θ=%.2f° p=(%.1f, %.1f)\n', ...
            A(k,1), A(k,2), theta(k), P(k,1), P(k,2));
        error('test_ray_filter: 过滤不保守');
    end

    cfg = config;
    assert(ray_can_see([0 0], 45, [700 700], cfg), '格点就在射线上，却判为看不到');
    assert(~ray_can_see([0 0], 45, [-2000 -2000], cfg), '反方向 2828 m，却放行');
    fprintf('  [PASS] 边界样例：射线上放行 / 反方向拦截\n');

    ds = linspace(0, 3000, 121);
    first_cut = NaN;
    for d = ds
        if ~ray_can_see([0 0], 0, [500 d], cfg), first_cut = d; break; end
    end
    fprintf('  拦截阈值：格点距射线 %.0f m 起被拦\n', first_cut);
    fprintf('===== 全部通过 =====\n\n');
end

% 圆域内均匀采样
function Q = sample_in_disk(n, R)
    r = R * sqrt(rand(n, 1));
    a = 2 * pi * rand(n, 1);
    Q = [r .* cos(a), r .* sin(a)];
end

% 独立暴力判据：域内源 s(t, δ) 使 dist(p, s) ≤ R_sensor
function tf = brute_can_see(A, theta, p, config, n_t, n_delta)
    T = 2 * config.R_domain;            % 域内任意两点距离上界
    ts = linspace(0, T, n_t);
    tf = false;
    for d = linspace(-config.epsilon_deg, config.epsilon_deg, n_delta)
        u = [cosd(theta + d), sind(theta + d)];
        S = A + ts' * u;                                        % n_t × 2
        in_dom = sum(S.^2, 2) <= config.R_domain^2;
        near   = sum((S - p).^2, 2) <= config.R_sensor^2;
        if any(in_dom & near)
            tf = true;
            return;
        end
    end
end
