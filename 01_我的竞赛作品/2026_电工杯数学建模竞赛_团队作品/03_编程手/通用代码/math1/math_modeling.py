#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数学建模算法库 (Mathematical Modeling Algorithm Library)
========================================================

本库汇集了数学建模竞赛中常用的50+种算法，分为17个板块：

  1. 评价方法        — AHP, TOPSIS, 熵权法, 模糊综合评价, 灰色关联, DEA, RSR
  2. 预测方法        — GM(1,1), Logistic, 指数平滑, 季节指数, 马尔可夫, GPR
  3. 线性优化        — 线性规划, 整数规划, 0-1规划
  4. 非线性优化      — 非线性规划, 多目标规划, 最速下降法
  5. 动态规划        — 0-1背包
  6. 智能优化        — 遗传算法, 粒子群算法, 模拟退火
  7. 图算法          — Dijkstra, Floyd
  8. 微分方程模型    — SIR传染病, Logistic人口, 兰彻斯特战争
  9. 降维方法        — PCA, t-SNE
 10. 异常值检测      — 3-sigma, IQR箱型图
 11. 插值方法        — 拉格朗日插值
 12. 概率分布        — 正态, Beta, Gamma, 几何, 指数, 二项, 超几何, 均匀, 泊松
 13. 统计检验        — t检验(单样本/独立/配对), 卡方检验
 14. 参数估计        — MLE, EM(GMM), 贝叶斯估计
 15. 相关性分析      — Pearson, Spearman, Kendall, 协方差, 切比雪夫界
 16. 中心极限定理    — Lindeberg-Levy, De Moivre-Laplace
 17. 机器学习        — K-means, GMM, 层次聚类, KNN, 决策树, 朴素贝叶斯, BP神经网络, 线性回归

核心依赖: numpy, scipy
可选依赖: sklearn, pulp, statsmodels (仅在调用相关函数时需要)
"""

import numpy as np
import math

__version__ = "1.0.0"
__all__ = [
    # 评价方法
    "ahp_evaluate", "topsis_evaluate", "entropy_weight_evaluate",
    "fuzzy_comprehensive_evaluate", "grey_relational_evaluate",
    "dea_evaluate", "rsr_evaluate",
    # 预测方法
    "gm11_predict", "logistic_fit", "quadratic_exponential_smooth",
    "seasonal_index_predict", "markov_predict", "gaussian_process_regress",
    # 线性优化
    "linear_programming_solve", "integer_programming_solve",
    "zero_one_programming_solve",
    # 非线性优化
    "nonlinear_programming_solve", "multi_objective_solve", "steepest_descent",
    # 动态规划
    "knapsack_dp",
    # 智能优化
    "genetic_algorithm_optimize", "particle_swarm_optimize",
    "simulated_annealing_optimize",
    # 图算法
    "dijkstra_shortest_path", "floyd_all_pairs_shortest",
    # 微分方程
    "sir_epidemic_solve", "logistic_population_solve", "lanchester_war_solve",
    # 降维
    "pca_reduce", "tsne_reduce",
    # 异常值检测
    "three_sigma_outliers", "iqr_outliers",
    # 插值
    "lagrange_interpolate",
    # 概率分布
    "Normal", "Beta", "Gamma", "Geometric", "Exponential",
    "Binomial", "HyperGeometric", "Uniform", "Poisson",
    # 统计检验
    "t_test_1sample", "t_test_independent", "t_test_paired",
    "chi_squared_test",
    # 参数估计
    "mle_estimate", "em_gmm_1d", "bayes_estimate",
    # 相关性
    "pearson_corr", "spearman_corr", "kendall_corr",
    "covariance", "chebyshev_bound",
    # 中心极限定理
    "clt_lindeberg_levy", "clt_demoivre_laplace",
    # 机器学习
    "kmeans_cluster", "gmm_cluster", "hierarchical_cluster",
    "knn_classify", "decision_tree_classify",
    "naive_bayes_classify", "bp_neural_network_regress",
    "linear_regression_fit", "polynomial_regression_fit",
]


# ===========================================================================
# SECTION 1: 评价方法 (Evaluation Methods)
# ===========================================================================

def ahp_evaluate(judgment_matrix, check_consistency=True):
    """
    层次分析法 (Analytic Hierarchy Process).

    通过判断矩阵的特征向量计算各指标/方案的权重，并进行一致性检验。

    Parameters
    ----------
    judgment_matrix : np.ndarray, shape (n, n)
        判断矩阵，A[i,j] 表示指标i相对于指标j的重要性（1-9标度法）。
        1=同等重要, 3=稍重要, 5=明显重要, 7=强烈重要, 9=极端重要。
        倒数表示相反关系。
    check_consistency : bool
        是否进行一致性检验 (默认 True)。

    Returns
    -------
    weights : np.ndarray, shape (n,)
        归一化的权重向量，各分量之和为1。
    info : dict
        包含 'max_eigenvalue', 'CI', 'CR', 'is_consistent', 'RI' 等信息。

    适用场景: 多准则决策, 专家打分权重确定, 方案优选。
    """
    n = judgment_matrix.shape[0]
    eigenvalues, eigenvectors = np.linalg.eig(judgment_matrix)
    max_eig = np.max(eigenvalues.real)
    idx = np.argmax(eigenvalues.real)
    w = eigenvectors[:, idx].real
    weights = w / np.sum(w)

    info = {'max_eigenvalue': max_eig, 'weights': weights}
    if check_consistency and n > 1:
        CI = (max_eig - n) / (n - 1)
        RI_list = [0, 0, 0.58, 0.90, 1.12, 1.24, 1.32, 1.41, 1.45, 1.49, 1.51]
        RI = RI_list[n] if n < len(RI_list) else 1.49
        CR = CI / RI if RI != 0 else 0
        info['CI'] = CI
        info['CR'] = CR
        info['RI'] = RI
        info['is_consistent'] = CR < 0.1
    return weights, info


def topsis_evaluate(data, weights, is_benefit=None):
    """
    TOPSIS综合评价法 (Technique for Order Preference by Similarity to
    Ideal Solution).

    通过计算各方案到正理想解和负理想解的距离，得到贴近度进行排序。

    Parameters
    ----------
    data : np.ndarray, shape (m, n)
        原始数据矩阵，m个方案，n个指标。
    weights : np.ndarray, shape (n,)
        各指标权重，各分量之和应为1。
    is_benefit : np.ndarray or None, shape (n,)
        各指标是否为效益型。True=效益型(越大越好), False=成本型(越小越好)。
        默认为全部效益型。

    Returns
    -------
    scores : np.ndarray, shape (m,)
        各方案的贴近度（综合评价指数），越大越优。
    info : dict
        包含 'ranking', 'd_plus', 'd_minus', 'ideal_plus', 'ideal_minus'。

    适用场景: 多方案综合评价与排序, 供应商选择, 项目评估。
    """
    m, n = data.shape
    if is_benefit is None:
        is_benefit = np.ones(n, dtype=bool)

    # 向量归一化
    data_norm = np.zeros((m, n))
    for j in range(n):
        norm = np.sqrt(np.sum(data[:, j] ** 2))
        data_norm[:, j] = data[:, j] / norm if norm != 0 else 0

    # 加权
    weighted = data_norm * weights

    # 正/负理想解
    z_plus = np.zeros(n)
    z_minus = np.zeros(n)
    for j in range(n):
        if is_benefit[j]:
            z_plus[j] = np.max(weighted[:, j])
            z_minus[j] = np.min(weighted[:, j])
        else:
            z_plus[j] = np.min(weighted[:, j])
            z_minus[j] = np.max(weighted[:, j])

    # 距离
    d_plus = np.sqrt(np.sum((weighted - z_plus) ** 2, axis=1))
    d_minus = np.sqrt(np.sum((weighted - z_minus) ** 2, axis=1))

    # 贴近度
    scores = d_minus / (d_plus + d_minus + np.finfo(float).eps)
    ranking = np.argsort(-scores) + 1

    return scores, {
        'ranking': ranking,
        'd_plus': d_plus,
        'd_minus': d_minus,
        'ideal_plus': z_plus,
        'ideal_minus': z_minus,
    }


def entropy_weight_evaluate(data):
    """
    熵权法.

    利用信息熵计算各指标的客观权重：指标的变异程度越大，熵值越小，权重越大。

    Parameters
    ----------
    data : np.ndarray, shape (m, n)
        原始数据矩阵，m个方案，n个指标（所有指标视为效益型）。

    Returns
    -------
    scores : np.ndarray, shape (m,)
        各方案的综合得分。
    info : dict
        包含 'weights', 'entropy', 'ranking'。

    适用场景: 客观权重确定, 综合评价（无需主观赋权）, 经济效率评估。
    """
    m, n = data.shape

    # 归一化到 [0,1]
    data_norm = np.zeros((m, n))
    for j in range(n):
        max_v, min_v = np.max(data[:, j]), np.min(data[:, j])
        if max_v != min_v:
            data_norm[:, j] = (data[:, j] - min_v) / (max_v - min_v)

    # 比重
    p = np.zeros((m, n))
    for j in range(n):
        s = np.sum(data_norm[:, j])
        p[:, j] = data_norm[:, j] / s if s != 0 else 1.0 / m

    # 熵值
    k = 1.0 / np.log(m) if m > 1 else 0
    e = np.zeros(n)
    for j in range(n):
        e[j] = -k * np.sum(p[:, j] * np.log(p[:, j] + np.finfo(float).eps))

    # 权重
    d = 1 - e
    weights = d / np.sum(d)

    # 得分
    scores = np.dot(data_norm, weights)
    ranking = np.argsort(-scores) + 1

    return scores, {'weights': weights, 'entropy': e, 'ranking': ranking}


def fuzzy_comprehensive_evaluate(data, weights, criteria):
    """
    模糊综合评价法.

    通过隶属度函数将指标值转换为对各评价等级的隶属度，加权合成得到综合评价。

    Parameters
    ----------
    data : np.ndarray, shape (m, n)
        m个评价对象，n个评价指标。
    weights : np.ndarray, shape (n,)
        各指标权重。
    criteria : np.ndarray, shape (n, k)
        各指标对应k个等级的标准值。每行从优到劣排列。

    Returns
    -------
    scores : np.ndarray, shape (m,)
        各对象的综合得分（等级赋分加权）。
    info : dict
        包含 'evaluation_matrix' (m x k综合评价矩阵), 'ranking'。

    适用场景: 带有模糊等级的评价问题, 员工考核, 教学质量评估。
    """
    m, n = data.shape
    k = criteria.shape[1]
    membership = np.zeros((m, k, n))
    level_scores = np.arange(k, 0, -1)

    for i in range(m):
        for j in range(n):
            x = data[i, j]
            s = criteria[j, :]

            # 最优等级
            if x >= s[0]:
                membership[i, 0, j] = 1
            elif x < s[1]:
                membership[i, 0, j] = 0
            else:
                membership[i, 0, j] = (x - s[1]) / (s[0] - s[1])

            # 中间等级
            for l in range(1, k - 1):
                if x >= s[l - 1] or x < s[l + 1]:
                    membership[i, l, j] = 0
                elif x >= s[l]:
                    membership[i, l, j] = (s[l - 1] - x) / (s[l - 1] - s[l])
                else:
                    membership[i, l, j] = (x - s[l + 1]) / (s[l] - s[l + 1])

            # 最劣等级
            if x <= s[-1]:
                membership[i, -1, j] = 1
            elif x > s[-2]:
                membership[i, -1, j] = 0
            else:
                membership[i, -1, j] = (s[-2] - x) / (s[-2] - s[-1])

    # 综合评价矩阵
    evaluation = np.zeros((m, k))
    for i in range(m):
        for l in range(k):
            evaluation[i, l] = np.sum(weights * membership[i, l, :])

    scores = evaluation @ level_scores
    ranking = np.argsort(-scores) + 1

    return scores, {'evaluation_matrix': evaluation, 'ranking': ranking}


def grey_relational_evaluate(data, reference=None):
    """
    灰色关联分析法 (Grey Relational Analysis).

    计算各方案与理想参考序列之间的灰色关联度，关联度越大表示方案越优。

    Parameters
    ----------
    data : np.ndarray, shape (m, n)
        m个方案，n个指标。
    reference : np.ndarray or None, shape (n,)
        理想参考序列。若为None，则取各指标最大值作为参考。

    Returns
    -------
    r : np.ndarray, shape (m,)
        各方案的灰色关联度。
    info : dict
        包含 'ranking', 'gamma' (关联系数矩阵)。

    适用场景: 样本量少、信息不完全时的综合评价, 经济发展水平对比。
    """
    m, n = data.shape
    if reference is None:
        reference = np.max(data, axis=0)

    combined = np.vstack((data, reference.reshape(1, -1)))
    data_norm = np.zeros((m, n))
    ref_norm = np.zeros(n)

    for j in range(n):
        max_v, min_v = np.max(combined[:, j]), np.min(combined[:, j])
        if max_v != min_v:
            data_norm[:, j] = (data[:, j] - min_v) / (max_v - min_v)
            ref_norm[j] = (reference[j] - min_v) / (max_v - min_v)

    delta = np.abs(data_norm - ref_norm)
    rho = 0.5
    max_d, min_d = np.max(delta), np.min(delta)
    gamma = (min_d + rho * max_d) / (delta + rho * max_d)
    r = np.mean(gamma, axis=1)
    ranking = np.argsort(-r) + 1

    return r, {'ranking': ranking, 'gamma': gamma}


def dea_evaluate(X, Y):
    """
    数据包络分析 (Data Envelopment Analysis, DEA-CCR模型).

    通过求解线性规划计算各决策单元(DMU)的相对效率。

    Parameters
    ----------
    X : np.ndarray, shape (n, m)
        投入矩阵，n个决策单元，m个投入指标。
    Y : np.ndarray, shape (n, s)
        产出矩阵，n个决策单元，s个产出指标。

    Returns
    -------
    theta : np.ndarray, shape (n,)
        各DMU的效率值（大于等于1时有效）。
    info : dict
        包含 'is_efficient', 'lambda_', 's_minus', 's_plus'。

    适用场景: 生产效率评价, 企业绩效评估, 资源配置分析。
    """
    from scipy.optimize import linprog

    n, m = X.shape
    s = Y.shape[1]
    theta = np.zeros(n)
    lambda_ = np.zeros((n, n))
    s_minus = np.zeros((n, m))
    s_plus = np.zeros((n, s))

    for j in range(n):
        c = np.hstack((np.zeros(n), np.ones(m), np.ones(s)))
        A_eq_top = np.hstack((X.T, np.eye(m), np.zeros((m, s))))
        b_eq_top = X[j, :].reshape(-1, 1)
        A_eq_bot = np.hstack((-Y.T, np.zeros((s, m)), np.eye(s)))
        b_eq_bot = -Y[j, :].reshape(-1, 1)
        A_eq = np.vstack((A_eq_top, A_eq_bot))
        b_eq = np.vstack((b_eq_top, b_eq_bot))
        bounds = [(0, None)] * (n + m + s)
        res = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')
        theta[j] = res.fun
        lambda_[j, :] = res.x[:n]
        s_minus[j, :] = res.x[n:n + m]
        s_plus[j, :] = res.x[n + m:n + m + s]

    is_eff = (theta >= 1 - 1e-6) & (np.sum(s_minus, axis=1) < 1e-6) & (np.sum(s_plus, axis=1) < 1e-6)

    return theta, {
        'is_efficient': is_eff,
        'lambda_': lambda_,
        's_minus': s_minus,
        's_plus': s_plus,
    }


def rsr_evaluate(data, weights, is_benefit=None):
    """
    秩和比综合评价法 (Rank-Sum Ratio).

    通过对指标编秩加权求和得到RSR值，并进行分档排序。

    Parameters
    ----------
    data : np.ndarray, shape (m, n)
        m个方案，n个指标。
    weights : np.ndarray, shape (n,)
        各指标权重。
    is_benefit : np.ndarray or None, shape (n,)
        各指标是否为效益型。默认为全部效益型。

    Returns
    -------
    rsr : np.ndarray, shape (m,)
        各方案的秩和比值。
    info : dict
        包含 'ranking', 'grade' (分档, 1档最优)。

    适用场景: 多方案综合评价, 医院绩效评价, 教育质量评估。
    """
    m, n = data.shape
    if is_benefit is None:
        is_benefit = np.ones(n, dtype=bool)

    R = np.zeros((m, n))
    for j in range(n):
        idx = np.argsort(-data[:, j])
        r = np.zeros(m)
        for i in range(m):
            r[idx[i]] = i + 1
        if not is_benefit[j]:
            r = m + 1 - r
        R[:, j] = r

    rsr = np.dot(R, weights) / m
    sorted_idx = np.argsort(-rsr)
    ranking = np.zeros(m, dtype=int)
    for i in range(m):
        ranking[sorted_idx[i]] = i + 1

    quarter = int(np.ceil(m / 4))
    grade = np.zeros(m, dtype=int)
    for g in range(4):
        start = g * quarter
        end = min((g + 1) * quarter, m)
        grade[sorted_idx[start:end]] = g + 1

    return rsr, {'ranking': ranking, 'grade': grade}


# ===========================================================================
# SECTION 2: 预测方法 (Prediction & Forecasting)
# ===========================================================================

def gm11_predict(x0, forecast_steps=1):
    """
    GM(1,1)灰色预测模型.

    适用于小样本（4-10个数据点）、信息不完全的预测问题，无需数据满足典型分布。

    Parameters
    ----------
    x0 : np.ndarray, shape (n,)
        原始数据序列（非负）。
    forecast_steps : int
        预测步数（默认1）。

    Returns
    -------
    forecast : np.ndarray, shape (forecast_steps,)
        预测值序列。
    info : dict
        包含 'a' (发展系数), 'b' (灰作用量), 'fitted', 'C' (后验差比),
        'P' (小误差概率), 'grade' (精度等级)。

    适用场景: 短期预测, 少量数据的趋势预测, 销售额预测。
    """
    n = len(x0)
    x1 = np.cumsum(x0)

    B = np.zeros((n - 1, 2))
    Y = np.zeros((n - 1, 1))
    for i in range(n - 1):
        B[i, 0] = -0.5 * (x1[i] + x1[i + 1])
        B[i, 1] = 1
        Y[i, 0] = x0[i + 1]

    BT = B.T
    params = np.dot(np.dot(np.linalg.inv(np.dot(BT, B)), BT), Y)
    a = params[0, 0]
    b = params[1, 0]

    def _predict(k):
        x1_hat = (x0[0] - b / a) * np.exp(-a * k) + b / a
        if k == 0:
            return x1_hat
        x1_prev = (x0[0] - b / a) * np.exp(-a * (k - 1)) + b / a
        return x1_hat - x1_prev

    fitted = np.zeros(n)
    fitted[0] = x0[0]
    for i in range(1, n):
        fitted[i] = _predict(i)

    forecast = np.array([_predict(n + i) for i in range(forecast_steps)])

    # 模型检验
    epsilon = x0 - fitted
    s1 = np.std(x0, ddof=1)
    s2 = np.std(epsilon, ddof=1)
    C = s2 / s1 if s1 != 0 else 0
    P = np.mean(np.abs(epsilon - np.mean(epsilon)) < 0.6745 * s1)
    if C < 0.35 and P > 0.95:
        grade = "好"
    elif C < 0.5 and P > 0.8:
        grade = "合格"
    elif C < 0.65 and P > 0.7:
        grade = "勉强"
    else:
        grade = "不合格"

    return forecast, {
        'a': a, 'b': b, 'fitted': fitted, 'C': C, 'P': P, 'grade': grade
    }


def logistic_fit(t_data, y_data, predict_t=None):
    """
    Logistic生长曲线拟合.

    拟合 Logistic 函数 y = K / (1 + (K/y0-1)*exp(-r*t))，适用于S型增长数据。

    Parameters
    ----------
    t_data : np.ndarray, shape (n,)
        时间点。
    y_data : np.ndarray, shape (n,)
        观测值。
    predict_t : np.ndarray or None
        需要预测的时间点。若为None则只返回拟合结果。

    Returns
    -------
    fitted : np.ndarray, shape (n,)
        拟合值。
    info : dict
        包含 'K', 'r', 'y0', 'predictions', 'r_squared'。

    适用场景: 人口增长预测, 市场饱和分析, 技术扩散曲线。
    """
    from scipy.optimize import curve_fit

    def _logistic(t, K, r, y0):
        return K / (1 + (K / y0 - 1) * np.exp(-r * t))

    popt, _ = curve_fit(_logistic, t_data, y_data,
                        p0=[np.max(y_data) * 1.5, 0.3, y_data[0]],
                        maxfev=10000)
    K, r, y0 = popt
    fitted = _logistic(t_data, K, r, y0)

    ss_res = np.sum((y_data - fitted) ** 2)
    ss_tot = np.sum((y_data - np.mean(y_data)) ** 2)
    r_squared = 1 - ss_res / ss_tot

    predictions = None
    if predict_t is not None:
        predictions = _logistic(predict_t, K, r, y0)

    return fitted, {
        'K': K, 'r': r, 'y0': y0,
        'predictions': predictions, 'r_squared': r_squared,
    }


def quadratic_exponential_smooth(data, alpha=0.3, forecast_steps=1):
    """
    二次指数平滑 (Holt线性趋势法).

    适用于具有线性趋势的时间序列预测。

    Parameters
    ----------
    data : np.ndarray, shape (n,)
        历史数据序列。
    alpha : float
        平滑系数，0~1之间。
    forecast_steps : int
        预测步数。

    Returns
    -------
    forecast : np.ndarray, shape (forecast_steps,)
        预测值。
    info : dict
        包含 'fitted', 'a' (截距), 'b' (趋势), 'rmse'。

    适用场景: 线性趋势的销售预测, 产量预测, 库存预测。
    """
    n = len(data)
    s1 = np.zeros(n)
    s2 = np.zeros(n)
    s1[0] = data[0]
    s2[0] = data[0]

    for i in range(1, n):
        s1[i] = alpha * data[i] + (1 - alpha) * s1[i - 1]
        s2[i] = alpha * s1[i] + (1 - alpha) * s2[i - 1]

    a = 2 * s1[-1] - s2[-1]
    b = (alpha / (1 - alpha)) * (s1[-1] - s2[-1]) if alpha != 1 else 0

    fitted = np.zeros(n)
    for t in range(n):
        fitted[t] = a - b * (n - t - 1)

    future = np.arange(1, forecast_steps + 1)
    forecast = a + b * future
    rmse = np.sqrt(np.mean((data - fitted) ** 2))

    return forecast, {'fitted': fitted, 'a': a, 'b': b, 'rmse': rmse}


def seasonal_index_predict(data, n_seasons=4, forecast_steps=1):
    """
    季节指数预测法.

    分解时间序列为趋势项和季节项，分别预测后合成。

    Parameters
    ----------
    data : np.ndarray, shape (n_periods * n_seasons,)
        历史数据（按季节排列）。
    n_seasons : int
        每周期季节数（如季度数据为4）。
    forecast_steps : int
        预测步数。

    Returns
    -------
    forecast : np.ndarray, shape (forecast_steps,)
        预测值。
    info : dict
        包含 'seasonal_indices', 'trend_a', 'trend_b', 'fitted', 'rmse'。

    适用场景: 季节性销售预测, 旅游客流预测, 季度产量预测。
    """
    n = len(data)
    n_periods = n // n_seasons

    # 计算季节指数
    period_means = data.reshape(n_periods, n_seasons).mean(axis=0)
    grand_mean = np.mean(data)
    seasonal_idx = period_means / grand_mean

    # 去季节化
    seasonal_expanded = np.tile(seasonal_idx, n_periods)
    deseasonalized = data / seasonal_expanded

    # 线性趋势
    t = np.arange(1, n + 1)
    coeffs = np.polyfit(t, deseasonalized, 1)
    trend = np.polyval(coeffs, t)

    # 预测
    future_t = np.arange(n + 1, n + forecast_steps + 1)
    trend_forecast = np.polyval(coeffs, future_t)
    future_seasonal = np.tile(seasonal_idx, int(np.ceil(forecast_steps / n_seasons)))
    forecast = trend_forecast * future_seasonal[:forecast_steps]

    fitted = trend * seasonal_expanded
    rmse = np.sqrt(np.mean((data - fitted) ** 2))

    return forecast, {
        'seasonal_indices': seasonal_idx,
        'trend_a': coeffs[0], 'trend_b': coeffs[1],
        'fitted': fitted, 'rmse': rmse,
    }


def markov_predict(states, n_states=3, forecast_steps=5):
    """
    马尔可夫链预测.

    基于状态转移概率矩阵对未来状态分布进行预测。

    Parameters
    ----------
    states : np.ndarray, shape (n,), dtype=int
        历史状态序列（0到n_states-1的整数）。
    n_states : int
        状态总数。
    forecast_steps : int
        预测步数。

    Returns
    -------
    forecast_distributions : list of np.ndarray
        未来每步的状态概率分布。
    info : dict
        包含 'transition_matrix', 'steady_state', 'most_likely_states'。

    适用场景: 股票涨跌预测, 天气状态预测, 市场占有率变化。
    """
    transition_counts = np.zeros((n_states, n_states), dtype=int)
    for t in range(len(states) - 1):
        transition_counts[states[t], states[t + 1]] += 1

    transition_matrix = np.zeros((n_states, n_states))
    for i in range(n_states):
        total = np.sum(transition_counts[i, :])
        if total > 0:
            transition_matrix[i, :] = transition_counts[i, :] / total

    # 初始分布
    current = np.zeros(n_states)
    current[states[-1]] = 1.0

    forecast_distributions = []
    for _ in range(forecast_steps):
        current = np.dot(current, transition_matrix)
        forecast_distributions.append(current.copy())

    most_likely = [np.argmax(d) for d in forecast_distributions]

    # 稳态分布
    steady = current.copy()
    for _ in range(1000):
        steady = np.dot(steady, transition_matrix)

    return forecast_distributions, {
        'transition_matrix': transition_matrix,
        'steady_state': steady,
        'most_likely_states': most_likely,
    }


def gaussian_process_regress(X_train, y_train, X_test):
    """
    高斯过程回归 (Gaussian Process Regression).

    使用RBF核的高斯过程回归，提供预测均值和不确定性估计。

    Parameters
    ----------
    X_train : np.ndarray, shape (n_train, n_features)
        训练特征。
    y_train : np.ndarray, shape (n_train,)
        训练标签。
    X_test : np.ndarray, shape (n_test, n_features)
        测试特征。

    Returns
    -------
    y_pred : np.ndarray, shape (n_test,)
        预测均值。
    info : dict
        包含 'std' (预测标准差), 'rmse_train'。

    适用场景: 小样本回归预测, 带有不确定性估计的预测, 实验设计优化。
    """
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import RBF, ConstantKernel

    kernel = ConstantKernel(1.0) * RBF(1.0)
    model = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=5,
                                     random_state=42)
    model.fit(X_train, y_train)
    y_pred, std = model.predict(X_test, return_std=True)
    y_train_pred = model.predict(X_train)
    rmse_train = np.sqrt(np.mean((y_train - y_train_pred) ** 2))

    return y_pred, {'std': std, 'rmse_train': rmse_train}


# ===========================================================================
# SECTION 3: 线性优化 (Linear Optimization)
# ===========================================================================

def linear_programming_solve(c, A_ub=None, b_ub=None, A_eq=None, b_eq=None,
                              bounds=None, maximize=True):
    """
    线性规划求解器.

    使用PuLP库求解标准线性规划问题：max/min c·x s.t. A_ub·x <= b_ub, A_eq·x == b_eq.

    Parameters
    ----------
    c : list or np.ndarray, shape (n,)
        目标函数系数。
    A_ub : np.ndarray or None, shape (m, n)
        不等式约束系数矩阵。
    b_ub : np.ndarray or None, shape (m,)
        不等式约束右端常数。
    A_eq : np.ndarray or None, shape (k, n)
        等式约束系数矩阵。
    b_eq : np.ndarray or None, shape (k,)
        等式约束右端常数。
    bounds : list of tuple or None
        每个变量的上下界 [(low, high), ...]。
    maximize : bool
        True为最大化，False为最小化。

    Returns
    -------
    solution : np.ndarray, shape (n,)
        最优解。
    info : dict
        包含 'objective_value', 'status'。

    适用场景: 资源分配, 生产计划, 运输调度。
    """
    import pulp as pl

    n = len(c)
    prob = pl.LpProblem("LP", pl.LpMaximize if maximize else pl.LpMinimize)
    x = [pl.LpVariable(f"x{i}", lowBound=0) for i in range(n)]

    if bounds:
        for i, (low, high) in enumerate(bounds):
            x[i].lowBound = low
            x[i].upBound = high

    prob += pl.lpSum(c[i] * x[i] for i in range(n))

    if A_ub is not None and b_ub is not None:
        for i in range(len(b_ub)):
            prob += pl.lpSum(A_ub[i][j] * x[j] for j in range(n)) <= b_ub[i]

    if A_eq is not None and b_eq is not None:
        for i in range(len(b_eq)):
            prob += pl.lpSum(A_eq[i][j] * x[j] for j in range(n)) == b_eq[i]

    prob.solve(pl.PULP_CBC_CMD(msg=False))
    solution = np.array([pl.value(var) for var in x])
    obj_value = pl.value(prob.objective)

    return solution, {'objective_value': obj_value, 'status': pl.LpStatus[prob.status]}


def integer_programming_solve(c, A_ub=None, b_ub=None, A_eq=None, b_eq=None,
                               maximize=True):
    """
    整数规划求解器.

    所有变量为整数类型。

    Parameters
    ----------
    (同 linear_programming_solve，但所有变量为整数)

    Returns
    -------
    solution : np.ndarray
        整数最优解。
    info : dict

    适用场景: 人员分配, 设备数量规划, 项目投资组合。
    """
    import pulp as pl

    n = len(c)
    prob = pl.LpProblem("IP", pl.LpMaximize if maximize else pl.LpMinimize)
    x = [pl.LpVariable(f"x{i}", lowBound=0, cat='Integer') for i in range(n)]

    prob += pl.lpSum(c[i] * x[i] for i in range(n))

    if A_ub is not None and b_ub is not None:
        for i in range(len(b_ub)):
            prob += pl.lpSum(A_ub[i][j] * x[j] for j in range(n)) <= b_ub[i]

    if A_eq is not None and b_eq is not None:
        for i in range(len(b_eq)):
            prob += pl.lpSum(A_eq[i][j] * x[j] for j in range(n)) == b_eq[i]

    prob.solve(pl.PULP_CBC_CMD(msg=False))
    solution = np.array([pl.value(var) for var in x], dtype=int)
    obj_value = pl.value(prob.objective)

    return solution, {'objective_value': obj_value, 'status': pl.LpStatus[prob.status]}


def zero_one_programming_solve(c, A_ub=None, b_ub=None, maximize=True):
    """
    0-1规划求解器.

    所有变量为0-1二元变量。

    Parameters
    ----------
    c : list or np.ndarray
        目标函数系数。
    A_ub : np.ndarray or None
        约束系数矩阵。
    b_ub : np.ndarray or None
        约束右端常数。
    maximize : bool

    Returns
    -------
    solution : np.ndarray, dtype=int
        0-1最优解。
    info : dict

    适用场景: 选址问题, 项目选择, 设施布局。
    """
    import pulp as pl

    n = len(c)
    prob = pl.LpProblem("ZOP", pl.LpMaximize if maximize else pl.LpMinimize)
    x = [pl.LpVariable(f"x{i}", cat='Binary') for i in range(n)]

    prob += pl.lpSum(c[i] * x[i] for i in range(n))

    if A_ub is not None and b_ub is not None:
        for i in range(len(b_ub)):
            prob += pl.lpSum(A_ub[i][j] * x[j] for j in range(n)) <= b_ub[i]

    prob.solve(pl.PULP_CBC_CMD(msg=False))
    solution = np.array([int(pl.value(var)) for var in x])
    obj_value = pl.value(prob.objective)

    return solution, {'objective_value': obj_value, 'status': pl.LpStatus[prob.status]}


# ===========================================================================
# SECTION 4: 非线性优化 (Nonlinear Optimization)
# ===========================================================================

def nonlinear_programming_solve(obj_func, x0, constraints=None, bounds=None):
    """
    非线性规划求解器.

    使用scipy的SLSQP方法求解带约束的非线性规划。

    Parameters
    ----------
    obj_func : callable
        目标函数 f(x) -> float (将最小化此函数)。
    x0 : np.ndarray
        初始猜测。
    constraints : list of dict or None
        scipy格式的约束列表，如 [{'type':'ineq', 'fun':lambda x: ...}]。
    bounds : list of tuple or None
        变量边界 [(low, high), ...]。

    Returns
    -------
    solution : np.ndarray
        最优解。
    info : dict
        包含 'objective_value', 'success', 'message'。

    适用场景: 非线性成本优化, 工程设计优化, 经济均衡分析。
    """
    from scipy.optimize import minimize

    result = minimize(obj_func, x0, method='SLSQP',
                      constraints=constraints if constraints else [],
                      bounds=bounds, options={'maxiter': 1000, 'ftol': 1e-9})
    return result.x, {
        'objective_value': result.fun,
        'success': result.success,
        'message': result.message,
    }


def multi_objective_solve(obj_funcs, x0, weights=None, constraints=None, bounds=None):
    """
    加权求和法多目标规划.

    将多个目标函数通过加权求和转化为单目标优化问题。

    Parameters
    ----------
    obj_funcs : list of callable
        目标函数列表 [f1, f2, ...]，每个接受x并返回标量。
    x0 : np.ndarray
        初始猜测。
    weights : list or None
        各目标函数的权重。若为None则等权重。
    constraints : list of dict or None
    bounds : list of tuple or None

    Returns
    -------
    solution : np.ndarray
        最优解。
    info : dict
        包含 'objective_values' (各目标的取值), 'weights'。

    适用场景: 多目标决策, 利润与环保平衡, 成本与质量权衡。
    """
    from scipy.optimize import minimize

    n_obj = len(obj_funcs)
    if weights is None:
        weights = np.ones(n_obj) / n_obj
    weights = np.array(weights)

    def weighted_obj(x):
        return sum(w * f(x) for w, f in zip(weights, obj_funcs))

    result = minimize(weighted_obj, x0, method='SLSQP',
                      constraints=constraints if constraints else [],
                      bounds=bounds, options={'maxiter': 1000})
    obj_values = [f(result.x) for f in obj_funcs]

    return result.x, {
        'objective_values': obj_values,
        'weights': weights,
        'total': result.fun,
        'success': result.success,
    }


def steepest_descent(grad_func, x0, learning_rate=0.1, max_iter=1000, tol=1e-6):
    """
    最速下降法（梯度下降法）.

    沿负梯度方向迭代寻优，适用于无约束凸优化问题。

    Parameters
    ----------
    grad_func : callable
        梯度函数 grad(x) -> np.ndarray。
    x0 : list or np.ndarray
        初始点。
    learning_rate : float
        学习率（步长）。
    max_iter : int
        最大迭代次数。
    tol : float
        收敛容差。

    Returns
    -------
    solution : np.ndarray
        最优解。
    info : dict
        包含 'path', 'n_iter', 'final_grad_norm'。

    适用场景: 无约束凸优化, 机器学习参数优化, 最小二乘问题。
    """
    x = np.array(x0, dtype=np.float64)
    path = [x.copy()]

    for i in range(max_iter):
        grad = grad_func(x)
        if np.linalg.norm(grad) < tol:
            break
        x = x - learning_rate * grad
        path.append(x.copy())

    return x, {
        'path': path,
        'n_iter': min(i + 1, max_iter),
        'final_grad_norm': np.linalg.norm(grad_func(x)),
    }


# ===========================================================================
# SECTION 5: 动态规划 (Dynamic Programming)
# ===========================================================================

def knapsack_dp(values, weights, capacity):
    """
    0-1背包问题动态规划求解.

    Parameters
    ----------
    values : list or np.ndarray
        每个物品的价值。
    weights : list or np.ndarray
        每个物品的重量。
    capacity : float
        背包容量。

    Returns
    -------
    max_value : float
        最大总价值。
    info : dict
        包含 'selected' (选中物品索引), 'total_weight'。

    适用场景: 资源分配, 投资组合选择, 货物装载优化。
    """
    n = len(values)
    w = list(weights)
    v = list(values)
    capacity = int(capacity)

    dp = [[0.0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(capacity + 1):
            if int(w[i - 1]) <= j:
                dp[i][j] = max(v[i - 1] + dp[i - 1][j - int(w[i - 1])], dp[i - 1][j])
            else:
                dp[i][j] = dp[i - 1][j]

    # 回溯
    selected = []
    j = capacity
    for i in range(n, 0, -1):
        if dp[i][j] != dp[i - 1][j]:
            selected.append(i - 1)
            j -= int(w[i - 1])
    selected.reverse()

    return dp[n][capacity], {
        'selected': selected,
        'total_weight': sum(weights[i] for i in selected),
    }


# ===========================================================================
# SECTION 6: 智能优化 (Intelligent Optimization)
# ===========================================================================

def genetic_algorithm_optimize(objective_func, bounds, pop_size=50,
                                num_generations=100, mutation_rate=0.1,
                                crossover_rate=0.8, random_state=None):
    """
    遗传算法 (Genetic Algorithm).

    模拟生物进化过程的全局优化算法：选择→交叉→变异→精英保留。

    Parameters
    ----------
    objective_func : callable
        目标函数 f(x) -> float，求解最小值。
    bounds : list of tuple
        各维度的取值范围 [(low, high), ...]。
    pop_size : int
        种群大小。
    num_generations : int
        进化代数。
    mutation_rate : float
        变异概率。
    crossover_rate : float
        交叉概率。
    random_state : int or None
        随机种子。

    Returns
    -------
    best_solution : np.ndarray
        最优解。
    info : dict
        包含 'best_value', 'history' (每代最优值)。

    适用场景: 复杂的全局优化问题, 多峰函数优化, 参数寻优。
    """
    if random_state is not None:
        np.random.seed(random_state)

    dim = len(bounds)

    def _init():
        pop = np.zeros((pop_size, dim))
        for d in range(dim):
            pop[:, d] = np.random.uniform(bounds[d][0], bounds[d][1], pop_size)
        return pop

    def _select(population, fitness, num_parents):
        fitness_adj = np.max(fitness) - fitness + 1e-10
        prob = fitness_adj / np.sum(fitness_adj)
        parents = population[np.random.choice(pop_size, num_parents, p=prob)]
        return parents

    def _crossover(parents, offspring_size):
        offspring = np.zeros(offspring_size)
        n_parents = len(parents)
        for i in range(offspring_size[0]):
            p1_idx = i % n_parents
            p2_idx = (i + 1) % n_parents
            if dim == 1:
                offspring[i] = parents[p1_idx] if np.random.rand() < 0.5 else parents[p2_idx]
            elif np.random.rand() < crossover_rate:
                cp = np.random.randint(1, dim)
                offspring[i, :cp] = parents[p1_idx, :cp]
                offspring[i, cp:] = parents[p2_idx, cp:]
            else:
                offspring[i] = parents[p1_idx]
        return offspring

    def _mutate(offspring):
        for i in range(offspring.shape[0]):
            for d in range(dim):
                if np.random.rand() < mutation_rate:
                    offspring[i, d] += np.random.normal(0, 0.5)
                    offspring[i, d] = np.clip(offspring[i, d], bounds[d][0], bounds[d][1])
        return offspring

    population = _init()
    fitness = np.array([objective_func(ind) for ind in population])
    best_idx = np.argmin(fitness)
    best_solution = population[best_idx].copy()
    best_value = fitness[best_idx]
    history = [best_value]

    for _ in range(num_generations):
        n_parents = pop_size // 2
        parents = _select(population, fitness, n_parents)
        offspring = _crossover(parents, (pop_size - n_parents, dim))
        offspring = _mutate(offspring)
        population = np.vstack((parents, offspring))
        fitness = np.array([objective_func(ind) for ind in population])

        cur_best_idx = np.argmin(fitness)
        if fitness[cur_best_idx] < best_value:
            best_solution = population[cur_best_idx].copy()
            best_value = fitness[cur_best_idx]
        history.append(best_value)

    return best_solution, {'best_value': best_value, 'history': history}


def particle_swarm_optimize(objective_func, bounds, num_particles=30,
                             max_iter=100, w=0.5, c1=1.0, c2=2.0,
                             random_state=None):
    """
    粒子群优化算法 (Particle Swarm Optimization).

    模拟鸟群觅食行为：粒子通过在搜索空间中跟踪个体和群体最优位置来更新速度和位置。

    Parameters
    ----------
    objective_func : callable
        目标函数 f(x) -> float，求解最小值。
    bounds : list of tuple
        各维度取值范围。
    num_particles : int
        粒子数。
    max_iter : int
        最大迭代次数。
    w : float
        惯性权重。
    c1 : float
        认知系数。
    c2 : float
        社会系数。
    random_state : int or None

    Returns
    -------
    best_position : np.ndarray
        全局最优位置。
    info : dict
        包含 'best_value', 'history'。

    适用场景: 连续优化问题, 神经网络权值优化, 函数极值求解。
    """
    if random_state is not None:
        np.random.seed(random_state)

    dim = len(bounds)
    particles = np.random.rand(num_particles, dim)
    for d in range(dim):
        particles[:, d] = particles[:, d] * (bounds[d][1] - bounds[d][0]) + bounds[d][0]

    velocities = np.random.randn(num_particles, dim) * 0.1
    pbest_pos = particles.copy()
    pbest_val = np.array([objective_func(p) for p in particles])
    gbest_idx = np.argmin(pbest_val)
    gbest_pos = pbest_pos[gbest_idx].copy()
    gbest_val = pbest_val[gbest_idx]
    history = [gbest_val]

    for _ in range(max_iter):
        r1, r2 = np.random.rand(num_particles, dim), np.random.rand(num_particles, dim)
        velocities = (w * velocities
                      + c1 * r1 * (pbest_pos - particles)
                      + c2 * r2 * (gbest_pos - particles))
        particles += velocities

        for d in range(dim):
            mask_low = particles[:, d] < bounds[d][0]
            mask_high = particles[:, d] > bounds[d][1]
            particles[mask_low, d] = bounds[d][0]
            particles[mask_high, d] = bounds[d][1]
            velocities[mask_low | mask_high, d] = 0

        cur_val = np.array([objective_func(p) for p in particles])
        improved = cur_val < pbest_val
        pbest_pos[improved] = particles[improved].copy()
        pbest_val[improved] = cur_val[improved]

        cur_gbest_idx = np.argmin(pbest_val)
        if pbest_val[cur_gbest_idx] < gbest_val:
            gbest_pos = pbest_pos[cur_gbest_idx].copy()
            gbest_val = pbest_val[cur_gbest_idx]
        history.append(gbest_val)

    return gbest_pos, {'best_value': gbest_val, 'history': history}


def simulated_annealing_optimize(objective_func, bounds, initial_temp=100.0,
                                  cooling_rate=0.95, max_iter=1000,
                                  step_size=None, random_state=None):
    """
    模拟退火算法 (Simulated Annealing).

    模拟物理退火过程，通过Metropolis准则接受劣解以跳出局部最优。

    Parameters
    ----------
    objective_func : callable
        目标函数，求解最小值。
    bounds : list of tuple
        各维度取值范围。
    initial_temp : float
        初始温度。
    cooling_rate : float
        降温速率 (0~1)。
    max_iter : int
        最大迭代次数。
    step_size : float or None
        邻域搜索步长。若为None则自动设为各维度范围的1/10。
    random_state : int or None

    Returns
    -------
    best_solution : np.ndarray
        最优解。
    info : dict
        包含 'best_value', 'history'。

    适用场景: 组合优化, 全局优化, 大规模参数寻优。
    """
    if random_state is not None:
        np.random.seed(random_state)

    dim = len(bounds)
    if step_size is None:
        step_size = np.mean([b[1] - b[0] for b in bounds]) / 10

    current = np.array([np.random.uniform(l, h) for l, h in bounds])
    current_value = objective_func(current)
    best_solution = current.copy()
    best_value = current_value
    temp = initial_temp
    history = [best_value]

    for i in range(max_iter):
        neighbor = current.copy()
        idx = np.random.randint(dim)
        neighbor[idx] += np.random.uniform(-step_size, step_size)
        neighbor[idx] = np.clip(neighbor[idx], bounds[idx][0], bounds[idx][1])

        neighbor_value = objective_func(neighbor)
        delta = neighbor_value - current_value

        if delta < 0 or np.random.rand() < np.exp(-delta / temp):
            current = neighbor.copy()
            current_value = neighbor_value
            if current_value < best_value:
                best_solution = current.copy()
                best_value = current_value

        temp *= cooling_rate
        history.append(best_value)

        if i % 100 == 0 and i > 0:
            step_size = max(0.1, step_size * 0.95)

    return best_solution, {'best_value': best_value, 'history': history}


# ===========================================================================
# SECTION 7: 图算法 (Graph Algorithms)
# ===========================================================================

def dijkstra_shortest_path(adj_matrix, start_node):
    """
    Dijkstra最短路径算法.

    计算从指定源节点到图中所有其他节点的最短路径。要求边权非负。

    Parameters
    ----------
    adj_matrix : np.ndarray, shape (n, n)
        邻接矩阵，adj[i,j]为从节点i到节点j的边权，0表示无边。
    start_node : int
        源节点索引。

    Returns
    -------
    distances : np.ndarray, shape (n,)
        从源节点到各节点的最短距离，inf表示不可达。
    info : dict
        包含 'paths' (各节点的最短路径节点序列，None表示不可达)。

    适用场景: 路径规划, 网络路由, 物流配送优化。
    """
    n = len(adj_matrix)
    distances = np.full(n, np.inf)
    distances[start_node] = 0
    visited = np.zeros(n, dtype=bool)
    predecessors = np.full(n, -1, dtype=int)

    for _ in range(n):
        unvisited = np.where(~visited)[0]
        if len(unvisited) == 0:
            break
        u = unvisited[np.argmin(distances[unvisited])]
        if distances[u] == np.inf:
            break
        visited[u] = True

        for v in range(n):
            if adj_matrix[u][v] > 0 and not visited[v]:
                new_dist = distances[u] + adj_matrix[u][v]
                if new_dist < distances[v]:
                    distances[v] = new_dist
                    predecessors[v] = u

    paths = []
    for end in range(n):
        if distances[end] == np.inf:
            paths.append(None)
        else:
            path = []
            cur = end
            while cur != -1:
                path.append(cur)
                cur = predecessors[cur]
            path.reverse()
            paths.append(path if path[0] == start_node else None)

    return distances, {'paths': paths}


def floyd_all_pairs_shortest(adj_matrix):
    """
    Floyd-Warshall全源最短路径算法.

    计算图中所有节点对之间的最短路径。

    Parameters
    ----------
    adj_matrix : np.ndarray, shape (n, n)
        邻接矩阵，inf表示无边。

    Returns
    -------
    dist : np.ndarray, shape (n, n)
        所有节点对的最短距离。
    info : dict
        包含 'path' (前驱矩阵), 'get_path' (路径重构辅助函数)。

    适用场景: 全网络路径分析, 交通可达性分析, 社交网络距离。
    """
    n = len(adj_matrix)
    dist = adj_matrix.astype(float).copy()
    path = np.full((n, n), -1, dtype=int)

    for i in range(n):
        for j in range(n):
            if i != j and dist[i, j] != np.inf:
                path[i, j] = i

    for k in range(n):
        for i in range(n):
            for j in range(n):
                if dist[i, k] + dist[k, j] < dist[i, j]:
                    dist[i, j] = dist[i, k] + dist[k, j]
                    path[i, j] = path[k, j]

    def _get_path(start, end):
        if path[start, end] == -1:
            return None
        result = [end]
        cur = end
        while cur != start:
            cur = path[start, cur]
            if cur == -1:
                return None
            result.append(cur)
        return result[::-1]

    return dist, {'path_matrix': path, 'get_path': _get_path}


# ===========================================================================
# SECTION 8: 微分方程模型 (Differential Equation Models)
# ===========================================================================

def sir_epidemic_solve(N, I0, beta, gamma, t_span=(0, 100), n_points=1000):
    """
    SIR传染病模型数值求解.

    求解 SIR 常微分方程组: dS/dt = -βSI/N, dI/dt = βSI/N - γI, dR/dt = γI.

    Parameters
    ----------
    N : float
        总人口。
    I0 : float
        初始感染者数量。
    beta : float
        感染率（每个感染者每天传染的人数）。
    gamma : float
        恢复率（1/平均感染天数）。
    t_span : tuple
        时间范围 (t_start, t_end)。
    n_points : int
        输出点数量。

    Returns
    -------
    t : np.ndarray
        时间点。
    result : np.ndarray, shape (n_points, 3)
        S, I, R 三列的时间序列。
    info : dict
        包含 'R0' (基本再生数), 'peak_time', 'peak_I'。

    适用场景: 疫情传播预测, 谣言扩散分析, 创新扩散模型。
    """
    from scipy.integrate import solve_ivp

    def _sir(t, state):
        S, I, R = state
        dS = -beta * S * I / N
        dI = beta * S * I / N - gamma * I
        dR = gamma * I
        return [dS, dI, dR]

    R0 = N - I0
    S0 = N - I0 - R0
    sol = solve_ivp(_sir, t_span, [S0, I0, R0],
                    t_eval=np.linspace(t_span[0], t_span[1], n_points),
                    method='RK45')

    I_series = sol.y[1]
    peak_idx = np.argmax(I_series)
    peak_time = sol.t[peak_idx]
    peak_I = I_series[peak_idx]

    return sol.t, sol.y.T, {
        'R0': beta / gamma,
        'peak_time': peak_time,
        'peak_I': peak_I,
    }


def logistic_population_solve(P0, r, K, t_span=(0, 200), n_points=1000):
    """
    Logistic人口增长模型.

    求解 Logistic 微分方程: dP/dt = r*P*(1 - P/K).

    Parameters
    ----------
    P0 : float
        初始人口。
    r : float
        内禀增长率。
    K : float
        环境承载力（最大人口容量）。
    t_span : tuple
        时间范围。
    n_points : int
        输出点数量。

    Returns
    -------
    t : np.ndarray
        时间点。
    P : np.ndarray, shape (n_points,)
        人口时间序列。
    info : dict

    适用场景: 人口预测, 生物种群动态, 市场增长分析。
    """
    from scipy.integrate import solve_ivp

    def _logistic(t, P):
        return r * P * (1 - P / K)

    sol = solve_ivp(_logistic, t_span, [P0],
                    t_eval=np.linspace(t_span[0], t_span[1], n_points),
                    method='RK45')

    return sol.t, sol.y[0], {}


def lanchester_war_solve(x0, y0, a, b, t_span=(0, 10), max_steps=10000):
    """
    兰彻斯特战争模型（平方律）.

    求解兰彻斯特方程: dx/dt = -b*y, dy/dt = -a*x.

    Parameters
    ----------
    x0 : float
        甲方初始兵力。
    y0 : float
        乙方初始兵力。
    a : float
        乙方的战斗效能系数。
    b : float
        甲方的战斗效能系数。
    t_span : tuple
        时间范围。
    max_steps : int
        最大步数。

    Returns
    -------
    t : np.ndarray
        时间点。
    result : np.ndarray, shape (n, 2)
        双方兵力时间序列。
    info : dict
        包含 'winner' (获胜方), 'end_time' (战斗结束时间),
        'remaining' (获胜方剩余兵力)。

    适用场景: 军事对抗分析, 市场竞争模拟, 资源消耗模型。
    """
    from scipy.integrate import solve_ivp

    def _lanchester(t, state):
        x, y = state
        return [-b * y, -a * x]

    sol = solve_ivp(_lanchester, t_span, [x0, y0],
                    method='RK45', max_step=(t_span[1] - t_span[0]) / max_steps)

    # 找到一方兵力耗尽的时间
    end_time = t_span[1]
    winner = None
    remaining = 0
    for i in range(len(sol.t)):
        if sol.y[0, i] < 1:
            winner = '乙方'
            remaining = sol.y[1, i]
            end_time = sol.t[i]
            break
        if sol.y[1, i] < 1:
            winner = '甲方'
            remaining = sol.y[0, i]
            end_time = sol.t[i]
            break

    return sol.t, sol.y.T, {
        'winner': winner, 'end_time': end_time, 'remaining': remaining,
    }


# ===========================================================================
# SECTION 9: 降维方法 (Dimensionality Reduction)
# ===========================================================================

def pca_reduce(data, n_components=2, standardize=True):
    """
    主成分分析 (PCA) 降维.

    Parameters
    ----------
    data : np.ndarray, shape (n_samples, n_features)
        原始数据。
    n_components : int
        目标维度。
    standardize : bool
        是否先标准化。

    Returns
    -------
    reduced : np.ndarray, shape (n_samples, n_components)
        降维后的数据。
    info : dict
        包含 'explained_variance_ratio', 'components', 'loadings'。

    适用场景: 高维数据可视化, 特征降维, 去噪预处理。
    """
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler

    if standardize:
        data = StandardScaler().fit_transform(data)

    model = PCA(n_components=n_components)
    reduced = model.fit_transform(data)

    loadings = model.components_.T * np.sqrt(model.explained_variance_)

    return reduced, {
        'explained_variance_ratio': model.explained_variance_ratio_,
        'explained_variance': model.explained_variance_,
        'components': model.components_,
        'loadings': loadings,
    }


def tsne_reduce(data, n_components=2, perplexity=30, random_state=42):
    """
    t-SNE降维 (t-Distributed Stochastic Neighbor Embedding).

    适合高维数据的非线性降维可视化，较好保留局部结构。

    Parameters
    ----------
    data : np.ndarray, shape (n_samples, n_features)
    n_components : int
        目标维度（通常为2）。
    perplexity : int
        困惑度参数，通常5-50之间。
    random_state : int

    Returns
    -------
    reduced : np.ndarray, shape (n_samples, n_components)
        降维后的数据。
    info : dict

    适用场景: 高维数据可视化, 聚类结果可视化, 数据探索。
    """
    from sklearn.manifold import TSNE
    from sklearn.preprocessing import StandardScaler

    data_std = StandardScaler().fit_transform(data)
    model = TSNE(n_components=n_components, perplexity=perplexity,
                 random_state=random_state)
    reduced = model.fit_transform(data_std)
    return reduced, {}


# ===========================================================================
# SECTION 10: 异常值检测 (Outlier Detection)
# ===========================================================================

def three_sigma_outliers(data):
    """
    3-sigma法则异常值检测.

    将超出均值±3倍标准差范围的点标记为异常值。

    Parameters
    ----------
    data : np.ndarray, shape (n,)
        一维数据。

    Returns
    -------
    is_outlier : np.ndarray, shape (n,), dtype=bool
        异常值标记。
    info : dict
        包含 'mu', 'sigma', 'lower', 'upper'。

    适用场景: 数据清洗, 异常数据筛选, 质量控制。
    """
    mu = np.mean(data)
    sigma = np.std(data)
    lower = mu - 3 * sigma
    upper = mu + 3 * sigma
    is_outlier = (data < lower) | (data > upper)
    return is_outlier, {'mu': mu, 'sigma': sigma, 'lower': lower, 'upper': upper}


def iqr_outliers(data, factor=1.5):
    """
    箱型图(IQR)异常值检测.

    将超出 Q1 - factor*IQR 和 Q3 + factor*IQR 的点标记为异常值。

    Parameters
    ----------
    data : np.ndarray, shape (n,)
        一维数据。
    factor : float
        IQR倍数，默认1.5。

    Returns
    -------
    is_outlier : np.ndarray, shape (n,), dtype=bool
    info : dict
        包含 'Q1', 'Q3', 'IQR', 'lower', 'upper'。

    适用场景: 偏态分布数据的异常检测, 稳健异常值识别。
    """
    Q1 = np.percentile(data, 25)
    Q3 = np.percentile(data, 75)
    IQR = Q3 - Q1
    lower = Q1 - factor * IQR
    upper = Q3 + factor * IQR
    is_outlier = (data < lower) | (data > upper)
    return is_outlier, {'Q1': Q1, 'Q3': Q3, 'IQR': IQR, 'lower': lower, 'upper': upper}


# ===========================================================================
# SECTION 11: 插值方法 (Interpolation)
# ===========================================================================

def lagrange_interpolate(x_sample, y_sample, x_interp):
    """
    拉格朗日多项式插值.

    通过已知采样点构造拉格朗日基函数，计算插值点的函数值。

    Parameters
    ----------
    x_sample : np.ndarray, shape (n,)
        已知采样点的x坐标。
    y_sample : np.ndarray, shape (n,)
        已知采样点的y坐标。
    x_interp : np.ndarray, shape (m,)
        待插值点的x坐标。

    Returns
    -------
    y_interp : np.ndarray, shape (m,)
        插值结果。
    info : dict

    适用场景: 数据补全, 缺失值插值, 函数逼近。
    """
    n = len(x_sample)
    y_interp = np.zeros_like(x_interp, dtype=np.float64)

    for k, x in enumerate(x_interp):
        y = 0.0
        for i in range(n):
            L = 1.0
            for j in range(n):
                if j != i:
                    L *= (x - x_sample[j]) / (x_sample[i] - x_sample[j])
            y += y_sample[i] * L
        y_interp[k] = y

    return y_interp, {}


# ===========================================================================
# SECTION 12: 概率分布 (Statistical Distributions)
# ===========================================================================

class Normal:
    """正态分布 N(μ, σ²). 适用: 测量误差, 自然现象, 中心极限定理相关."""

    def __init__(self, mu=0, sigma=1):
        if sigma <= 0:
            raise ValueError("sigma must be positive")
        self.mu = mu
        self.sigma = sigma

    def pdf(self, x):
        return (1 / (self.sigma * math.sqrt(2 * math.pi))) * \
               math.exp(-((x - self.mu) ** 2) / (2 * self.sigma ** 2))

    def cdf(self, x):
        return 0.5 * (1 + math.erf((x - self.mu) / (self.sigma * math.sqrt(2))))

    def expectation(self):
        return self.mu

    def variance(self):
        return self.sigma ** 2

    def std_dev(self):
        return self.sigma


class Beta:
    """Beta分布 Beta(α, β). 适用: 概率/比例的分布建模, 贝叶斯先验."""

    def __init__(self, alpha, beta):
        if alpha <= 0 or beta <= 0:
            raise ValueError("alpha and beta must be positive")
        self.alpha = alpha
        self.beta = beta

    def pdf(self, x):
        if not 0 <= x <= 1:
            return 0
        B = math.gamma(self.alpha) * math.gamma(self.beta) / math.gamma(self.alpha + self.beta)
        return (x ** (self.alpha - 1)) * ((1 - x) ** (self.beta - 1)) / B

    def cdf(self, x, steps=1000):
        if x <= 0:
            return 0.0
        if x >= 1:
            return 1.0
        xs, dx = np.linspace(0, x, steps, retstep=True)
        return np.trapezoid([self.pdf(v) for v in xs], dx=dx)

    def expectation(self):
        return self.alpha / (self.alpha + self.beta)

    def variance(self):
        ab = self.alpha + self.beta
        return (self.alpha * self.beta) / (ab ** 2 * (ab + 1))

    def std_dev(self):
        return math.sqrt(self.variance())


class Gamma:
    """Gamma分布 Gamma(k, λ). 适用: 等待时间, 寿命建模, 降水量分布."""

    def __init__(self, k, lam):
        if k <= 0 or lam <= 0:
            raise ValueError("k and lam must be positive")
        self.k = k
        self.lam = lam

    def pdf(self, x):
        if x < 0:
            return 0
        return (self.lam ** self.k * x ** (self.k - 1) *
                math.exp(-self.lam * x)) / math.gamma(self.k)

    def cdf(self, x, steps=1000):
        if x <= 0:
            return 0.0
        xs, dx = np.linspace(0, x, steps, retstep=True)
        return np.trapezoid([self.pdf(v) for v in xs], dx=dx)

    def expectation(self):
        return self.k / self.lam

    def variance(self):
        return self.k / self.lam ** 2

    def std_dev(self):
        return math.sqrt(self.variance())


class Geometric:
    """几何分布 Geom(p). 适用: 首次成功所需试验次数, 寿命测试."""

    def __init__(self, p):
        if not 0 < p <= 1:
            raise ValueError("p must be in (0, 1]")
        self.p = p

    def pmf(self, k):
        if k < 1:
            return 0
        return ((1 - self.p) ** (k - 1)) * self.p

    def cdf(self, k):
        if k < 1:
            return 0.0
        return 1 - (1 - self.p) ** int(k)

    def expectation(self):
        return 1 / self.p

    def variance(self):
        return (1 - self.p) / self.p ** 2

    def std_dev(self):
        return math.sqrt(self.variance())


class Exponential:
    """指数分布 Exp(λ). 适用: 等待时间, 元器件寿命, 衰减过程."""

    def __init__(self, lam):
        if lam <= 0:
            raise ValueError("lam must be positive")
        self.lam = lam

    def pdf(self, x):
        if x < 0:
            return 0
        return self.lam * math.exp(-self.lam * x)

    def cdf(self, x):
        if x < 0:
            return 0.0
        return 1 - math.exp(-self.lam * x)

    def expectation(self):
        return 1 / self.lam

    def variance(self):
        return 1 / self.lam ** 2

    def std_dev(self):
        return 1 / self.lam


class Binomial:
    """二项分布 B(n, p). 适用: n次独立试验成功次数, 抽样检验."""

    def __init__(self, n, p):
        if n <= 0 or not isinstance(n, int):
            raise ValueError("n must be a positive integer")
        if not 0 <= p <= 1:
            raise ValueError("p must be in [0, 1]")
        self.n = n
        self.p = p

    def pmf(self, k):
        if k < 0 or k > self.n:
            return 0
        return math.comb(self.n, k) * (self.p ** k) * ((1 - self.p) ** (self.n - k))

    def cdf(self, k):
        return sum(self.pmf(i) for i in range(int(k) + 1))

    def expectation(self):
        return self.n * self.p

    def variance(self):
        return self.n * self.p * (1 - self.p)

    def std_dev(self):
        return math.sqrt(self.variance())


class HyperGeometric:
    """超几何分布 H(N, M, n). 适用: 不放回抽样, 产品抽检."""

    def __init__(self, N, M, n):
        self.N = N
        self.M = M
        self.n_sample = n

    def pmf(self, k):
        lo = max(0, self.n_sample + self.M - self.N)
        hi = min(self.n_sample, self.M)
        if k < lo or k > hi:
            return 0
        return (math.comb(self.M, k) * math.comb(self.N - self.M, self.n_sample - k)
                / math.comb(self.N, self.n_sample))

    def cdf(self, k):
        return sum(self.pmf(i) for i in range(int(k) + 1))

    def expectation(self):
        return self.n_sample * self.M / self.N

    def variance(self):
        p = self.M / self.N
        return self.n_sample * p * (1 - p) * (self.N - self.n_sample) / (self.N - 1)

    def std_dev(self):
        return math.sqrt(self.variance())


class Uniform:
    """均匀分布 U(a, b). 适用: 随机模拟, 随机数生成, 无信息先验."""

    def __init__(self, a, b):
        if a >= b:
            raise ValueError("a must be less than b")
        self.a = a
        self.b = b

    def pdf(self, x):
        if self.a <= x <= self.b:
            return 1 / (self.b - self.a)
        return 0

    def cdf(self, x):
        if x < self.a:
            return 0.0
        if x > self.b:
            return 1.0
        return (x - self.a) / (self.b - self.a)

    def expectation(self):
        return (self.a + self.b) / 2

    def variance(self):
        return (self.b - self.a) ** 2 / 12

    def std_dev(self):
        return math.sqrt(self.variance())


class Poisson:
    """泊松分布 P(λ). 适用: 稀有事件发生次数, 单位时间到达数, 排队论."""

    def __init__(self, lam):
        if lam <= 0:
            raise ValueError("lam must be positive")
        self.lam = lam

    @staticmethod
    def _factorial(n):
        result = 1
        for i in range(2, n + 1):
            result *= i
        return result

    def pmf(self, k):
        if k < 0 or not isinstance(k, int):
            return 0
        return (self.lam ** k * math.exp(-self.lam)) / self._factorial(k)

    def cdf(self, k):
        return sum(self.pmf(i) for i in range(int(k) + 1))

    def expectation(self):
        return self.lam

    def variance(self):
        return self.lam

    def std_dev(self):
        return math.sqrt(self.lam)


# ===========================================================================
# SECTION 13: 统计检验 (Statistical Tests)
# ===========================================================================

def _normal_cdf(z):
    """标准正态CDF近似."""
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def t_test_1sample(data, mu0=0, alpha=0.05, alternative='two-sided'):
    """
    单样本t检验.

    检验样本均值是否与给定值mu0有显著差异。

    Parameters
    ----------
    data : np.ndarray
        样本数据。
    mu0 : float
        原假设均值。
    alpha : float
        显著性水平。
    alternative : str
        'two-sided', 'greater', 'less'.

    Returns
    -------
    t_stat : float
        t统计量。
    info : dict
        包含 'p_value', 'df', 'reject' (是否拒绝H0)。

    适用场景: 单组实验效果检验, 产品质量检查, 医学疗效评估。
    """
    n = len(data)
    x_bar = np.mean(data)
    s = np.std(data, ddof=1)
    t_stat = (x_bar - mu0) / (s / np.sqrt(n))
    df = n - 1

    p_val = _t_test_p_value(t_stat, df, alternative)
    reject = p_val < alpha

    return t_stat, {'p_value': p_val, 'df': df, 'reject': reject, 'alpha': alpha}


def t_test_independent(data1, data2, alpha=0.05, alternative='two-sided',
                        equal_var=True):
    """
    独立样本t检验.

    检验两组独立样本的均值是否具有显著差异。

    Parameters
    ----------
    data1, data2 : np.ndarray
        两组样本数据。
    alpha : float
    alternative : str
    equal_var : bool
        是否假设方差相等（True: 合并方差; False: Welch校正）。

    Returns
    -------
    t_stat : float
    info : dict

    适用场景: A/B测试效果对比, 两组实验对比, 药物效果比较。
    """
    n1, n2 = len(data1), len(data2)
    x1, x2 = np.mean(data1), np.mean(data2)
    s1, s2 = np.std(data1, ddof=1), np.std(data2, ddof=1)

    if equal_var:
        sp = np.sqrt(((n1 - 1) * s1 ** 2 + (n2 - 1) * s2 ** 2) / (n1 + n2 - 2))
        t_stat = (x1 - x2) / (sp * np.sqrt(1 / n1 + 1 / n2))
        df = n1 + n2 - 2
    else:
        t_stat = (x1 - x2) / np.sqrt(s1 ** 2 / n1 + s2 ** 2 / n2)
        num = (s1 ** 2 / n1 + s2 ** 2 / n2) ** 2
        den = ((s1 ** 2 / n1) ** 2) / (n1 - 1) + ((s2 ** 2 / n2) ** 2) / (n2 - 1)
        df = num / den

    p_val = _t_test_p_value(t_stat, df, alternative)
    reject = p_val < alpha

    return t_stat, {'p_value': p_val, 'df': df, 'reject': reject,
                    'mean1': x1, 'mean2': x2, 'alpha': alpha}


def t_test_paired(data1, data2, alpha=0.05, alternative='two-sided'):
    """
    配对样本t检验.

    检验两组配对样本的均值差异是否显著。

    Parameters
    ----------
    data1, data2 : np.ndarray
        两组配对数据（长度相同）。
    alpha : float
    alternative : str

    Returns
    -------
    t_stat : float
    info : dict

    适用场景: 同一对象的处理前后对比, 配对实验设计, 药效检验。
    """
    diff = np.array(data1) - np.array(data2)
    return t_test_1sample(diff, mu0=0, alpha=alpha, alternative=alternative)


def chi_squared_test(observed, alpha=0.05):
    """
    卡方独立性检验.

    检验两个分类变量是否独立。

    Parameters
    ----------
    observed : np.ndarray, shape (r, c)
        观测频数列联表。
    alpha : float

    Returns
    -------
    chi2 : float
        卡方统计量。
    info : dict
        包含 'p_value', 'df', 'reject', 'expected' (期望频数)。

    适用场景: 分类变量关联分析, 问卷调查分析, 基因型分布检验。
    """
    r, c = observed.shape
    row_sum = observed.sum(axis=1)
    col_sum = observed.sum(axis=0)
    total = observed.sum()
    expected = np.outer(row_sum, col_sum) / total

    chi2 = np.sum((observed - expected) ** 2 / expected)
    df = (r - 1) * (c - 1)

    # 正态近似p值
    z = (chi2 - df) / np.sqrt(2 * df) if df > 0 else 0
    p_val = 1 - _normal_cdf(z)
    reject = p_val < alpha

    return chi2, {
        'p_value': p_val, 'df': df, 'reject': reject,
        'expected': expected, 'alpha': alpha,
    }


def _t_test_p_value(t_stat, df, alternative):
    """t分布的p值（梯形积分法）."""
    if df <= 0:
        return 1.0

    steps = 10000
    # t分布尾部较厚(df=1时为柯西分布)，使用±50范围配合归一化确保精度
    limit = 50 if df <= 2 else 20
    xs = np.linspace(-limit, limit, steps)
    const = math.gamma((df + 1) / 2) / (math.sqrt(df * math.pi) * math.gamma(df / 2))
    pdf_vals = const * (1 + xs ** 2 / df) ** (-(df + 1) / 2)
    dx = 2 * limit / (steps - 1)
    # 归一化确保总面积精确为1，消除截断误差
    total_area = np.trapezoid(pdf_vals, dx=dx)
    pdf_vals = pdf_vals / total_area

    if alternative == 'two-sided':
        idx = np.searchsorted(xs, abs(t_stat))
        return max(0.0, min(1.0, 2 * (1 - np.trapezoid(pdf_vals[:idx], dx=dx))))
    elif alternative == 'greater':
        idx = np.searchsorted(xs, t_stat)
        return max(0.0, min(1.0, 1 - np.trapezoid(pdf_vals[:idx], dx=dx)))
    else:  # less
        idx = np.searchsorted(xs, t_stat)
        return max(0.0, min(1.0, np.trapezoid(pdf_vals[:idx], dx=dx)))


# ===========================================================================
# SECTION 14: 参数估计 (Parameter Estimation)
# ===========================================================================

def mle_estimate(xs, param_grid, pmf_or_pdf):
    """
    最大似然估计 (Maximum Likelihood Estimation).

    通过网格搜索找到使对数似然函数最大的参数值。

    Parameters
    ----------
    xs : np.ndarray
        观测样本数据。
    param_grid : list
        待估计参数的候选值列表。
    pmf_or_pdf : callable
        分布的概率质量/密度函数，签名: f(x, param) -> float。

    Returns
    -------
    best_param : float
        最优参数值。
    info : dict
        包含 'max_loglik' (最大对数似然值), 'all_logliks'。

    适用场景: 分布参数估计, 模型参数拟合, 可靠性分析。
    """
    best_param = param_grid[0]
    max_loglik = -np.inf
    all_logliks = []

    for param in param_grid:
        loglik = sum(np.log(max(pmf_or_pdf(x, param), np.finfo(float).eps))
                     for x in xs)
        all_logliks.append(loglik)
        if loglik > max_loglik:
            max_loglik = loglik
            best_param = param

    return best_param, {'max_loglik': max_loglik, 'all_logliks': all_logliks}


def em_gmm_1d(xs, K=2, max_iter=100, tol=1e-4):
    """
    EM算法一维高斯混合模型 (Expectation-Maximization).

    Parameters
    ----------
    xs : np.ndarray
        一维观测数据。
    K : int
        高斯分量个数。
    max_iter : int
        最大迭代次数。
    tol : float
        收敛容差。

    Returns
    -------
    pis : np.ndarray, shape (K,)
        各分量的混合系数。
    mus : np.ndarray, shape (K,)
        各分量的均值。
    sigma2s : np.ndarray, shape (K,)
        各分量的方差。
    info : dict
        包含 'n_iter', 'log_likelihoods'。

    适用场景: 混合分布分解, 模式识别, 聚类分析。
    """
    N = len(xs)
    # 初始化
    pis = np.ones(K) / K
    mus = np.linspace(np.min(xs), np.max(xs), K)
    sigma2s = np.ones(K) * np.var(xs)

    log_liks = []
    for _ in range(max_iter):
        # E步：计算责任度
        gamma = np.zeros((N, K))
        for k in range(K):
            gamma[:, k] = pis[k] * (1 / np.sqrt(2 * np.pi * sigma2s[k]) *
                         np.exp(-(xs - mus[k]) ** 2 / (2 * sigma2s[k])))
        gamma /= gamma.sum(axis=1, keepdims=True)

        # M步：更新参数
        Nk = gamma.sum(axis=0)
        pis_new = Nk / N
        mus_new = (gamma * xs.reshape(-1, 1)).sum(axis=0) / Nk
        sigma2s_new = np.zeros(K)
        for k in range(K):
            sigma2s_new[k] = (gamma[:, k] * (xs - mus_new[k]) ** 2).sum() / Nk[k]

        # 收敛检测
        log_lik = np.sum(np.log(np.sum(
            [pis_new[k] * (1 / np.sqrt(2 * np.pi * sigma2s_new[k]) *
             np.exp(-(xs - mus_new[k]) ** 2 / (2 * sigma2s_new[k])))
             for k in range(K)], axis=0)))
        log_liks.append(log_lik)

        if len(log_liks) > 1 and abs(log_lik - log_liks[-2]) < tol:
            break

        pis, mus, sigma2s = pis_new, mus_new, sigma2s_new

    return pis, mus, sigma2s, {'n_iter': len(log_liks), 'log_likelihoods': log_liks}


def bayes_estimate(xs, theta_grid, prior_func, likelihood_func):
    """
    贝叶斯参数估计.

    通过贝叶斯公式计算参数的后验分布和期望值。

    Parameters
    ----------
    xs : np.ndarray
        观测数据。
    theta_grid : np.ndarray
        参数候选值网格。
    prior_func : callable
        先验分布函数 prior(theta) -> float。
    likelihood_func : callable
        似然函数 likelihood(theta, xs) -> float。

    Returns
    -------
    posterior_mean : float
        后验均值。
    info : dict
        包含 'posterior' (后验概率字典)。

    适用场景: 先验知识较强的参数估计, 小样本分析, 贝叶斯推断。
    """
    posterior = {}
    total = 0
    for theta in theta_grid:
        posterior[theta] = prior_func(theta) * likelihood_func(theta, xs)
        total += posterior[theta]

    for theta in theta_grid:
        posterior[theta] /= total

    posterior_mean = sum(theta * p for theta, p in posterior.items())

    return posterior_mean, {'posterior': posterior}


# ===========================================================================
# SECTION 15: 相关性分析 (Correlation & Association)
# ===========================================================================

def pearson_corr(x, y):
    """
    Pearson相关系数.

    衡量两个连续变量之间的线性相关程度，取值范围[-1, 1]。

    Parameters
    ----------
    x, y : np.ndarray
        两个等长的一维数组。

    Returns
    -------
    r : float
        Pearson相关系数。

    适用场景: 线性相关性分析, 特征选择, 数据探索。
    """
    return covariance(x, y, sample=True) / (np.std(x, ddof=1) * np.std(y, ddof=1))


def spearman_corr(x, y):
    """
    Spearman秩相关系数.

    基于数据秩次的非参数相关度量，对单调关系敏感，对异常值稳健。

    Parameters
    ----------
    x, y : np.ndarray

    Returns
    -------
    rho : float
        Spearman相关系数。

    适用场景: 非线性单调趋势分析, 异常值较多的数据, 序数变量分析。
    """
    from scipy.stats import rankdata
    rx = rankdata(x)
    ry = rankdata(y)
    return pearson_corr(rx, ry)


def kendall_corr(x, y):
    """
    Kendall秩相关系数 (τ).

    基于数据对的一致性/不一致性计数的非参数相关度量。

    Parameters
    ----------
    x, y : np.ndarray

    Returns
    -------
    tau : float
        Kendall τ系数。

    适用场景: 小样本相关性分析, 序数数据, 假设检验。
    """
    n = len(x)
    concordant = 0
    discordant = 0

    for i in range(n):
        for j in range(i + 1, n):
            dx = x[i] - x[j] if isinstance(x[i], (int, float)) else 0
            dy = y[i] - y[j] if isinstance(y[i], (int, float)) else 0
            if dx * dy > 0:
                concordant += 1
            elif dx * dy < 0:
                discordant += 1

    total = n * (n - 1) / 2
    return (concordant - discordant) / total


def covariance(x, y, sample=True):
    """
    协方差.

    Parameters
    ----------
    x, y : np.ndarray
    sample : bool
        True使用n-1（样本协方差），False使用n（总体协方差）。

    Returns
    -------
    cov : float
    """
    n = len(x)
    ex, ey = np.mean(x), np.mean(y)
    ddof = 1 if sample else 0
    return np.sum((x - ex) * (y - ey)) / (n - ddof)


def chebyshev_bound(k):
    """
    切比雪夫不等式界.

    对于任意分布，P(|X-μ| ≥ kσ) ≤ 1/k².

    Parameters
    ----------
    k : float
        标准差倍数。

    Returns
    -------
    bound : float
        偏差概率的上界。

    适用场景: 概率上界估计, 样本量确定, 鲁棒性分析。
    """
    return min(1.0, 1.0 / k ** 2) if k > 0 else 1.0


# ===========================================================================
# SECTION 16: 中心极限定理 (Central Limit Theorem)
# ===========================================================================

def clt_lindeberg_levy(x, mu, var, n):
    """
    Lindeberg-Levy中心极限定理.

    计算独立同分布样本均值标准化后的正态近似概率。
    P(ΣXi ≤ x) ≈ Φ((x - n*μ)/√(n*var)).

    Parameters
    ----------
    x : float
        和的上界值。
    mu : float
        总体的均值。
    var : float
        总体的方差。
    n : int
        样本量。

    Returns
    -------
    prob : float
        近似概率。

    适用场景: 大样本近似推理, 置信区间构造, 统计推断。
    """
    z = (x - n * mu) / np.sqrt(n * var)
    return _normal_cdf(z)


def clt_demoivre_laplace(k, n, p):
    """
    De Moivre-Laplace中心极限定理.

    二项分布的正态近似（带连续性校正）:
    P(X ≤ k) ≈ Φ((k + 0.5 - n*p)/√(n*p*(1-p))).

    Parameters
    ----------
    k : int
        成功次数的上界。
    n : int
        试验次数。
    p : float
        每次试验的成功概率。

    Returns
    -------
    prob : float

    适用场景: 二项分布的大样本近似, 比例检验, 抽样调查。
    """
    z = (k + 0.5 - n * p) / np.sqrt(n * p * (1 - p))
    return _normal_cdf(z)


# ===========================================================================
# SECTION 17: 机器学习 (Machine Learning)
# ===========================================================================

def kmeans_cluster(data, n_clusters=3, random_state=42, standardize=True):
    """
    K-means聚类.

    Parameters
    ----------
    data : np.ndarray, shape (n_samples, n_features)
    n_clusters : int
    random_state : int
    standardize : bool

    Returns
    -------
    labels : np.ndarray, shape (n_samples,)
        聚类标签。
    info : dict
        包含 'centers', 'inertia', 'n_iter'。

    适用场景: 客户分群, 市场细分, 图像压缩。
    """
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    if standardize:
        data = StandardScaler().fit_transform(data)

    model = KMeans(n_clusters=n_clusters, init='k-means++', n_init=10,
                   max_iter=300, random_state=random_state)
    labels = model.fit_predict(data)
    centers = model.cluster_centers_

    return labels, {
        'centers': centers,
        'inertia': model.inertia_,
        'n_iter': model.n_iter_,
    }


def gmm_cluster(data, n_components=3, covariance_type='full', random_state=42):
    """
    高斯混合模型 (GMM) 聚类.

    Parameters
    ----------
    data : np.ndarray, shape (n_samples, n_features)
    n_components : int
    covariance_type : str
        'full', 'tied', 'diag', 'spherical'.
    random_state : int

    Returns
    -------
    labels : np.ndarray, shape (n_samples,)
        硬聚类标签。
    info : dict
        包含 'probabilities' (软概率), 'means', 'weights'。

    适用场景: 软聚类, 概率聚类, 形状非球形的类别。
    """
    from sklearn.mixture import GaussianMixture

    model = GaussianMixture(n_components=n_components,
                            covariance_type=covariance_type,
                            random_state=random_state)
    model.fit(data)
    labels = model.predict(data)
    probs = model.predict_proba(data)

    return labels, {
        'probabilities': probs,
        'means': model.means_,
        'weights': model.weights_,
    }


def hierarchical_cluster(data, n_clusters=3, method='ward'):
    """
    层次聚类.

    Parameters
    ----------
    data : np.ndarray, shape (n_samples, n_features)
    n_clusters : int
    method : str
        链接方式: 'ward', 'average', 'complete', 'single'.

    Returns
    -------
    labels : np.ndarray, shape (n_samples,)
        聚类标签。
    info : dict
        包含 'linkage_matrix'。

    适用场景: 层次化数据探索, 系统发育树, 客户分层。
    """
    from scipy.cluster.hierarchy import linkage, fcluster
    from sklearn.preprocessing import StandardScaler

    data_std = StandardScaler().fit_transform(data)
    Z = linkage(data_std, method=method)
    labels = fcluster(Z, n_clusters, criterion='maxclust')

    return labels, {'linkage_matrix': Z}


def knn_classify(X_train, y_train, X_test, k=5):
    """
    K-近邻分类 (K-Nearest Neighbors).

    Parameters
    ----------
    X_train : np.ndarray, shape (n_train, n_features)
    y_train : np.ndarray, shape (n_train,)
    X_test : np.ndarray, shape (n_test, n_features)
    k : int

    Returns
    -------
    y_pred : np.ndarray, shape (n_test,)
        预测标签。
    info : dict

    适用场景: 模式识别, 推荐系统, 异常检测。
    """
    from sklearn.neighbors import KNeighborsClassifier

    model = KNeighborsClassifier(n_neighbors=k, metric='euclidean')
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    return y_pred, {}


def decision_tree_classify(X_train, y_train, X_test, max_depth=None):
    """
    决策树分类 (Decision Tree).

    Parameters
    ----------
    X_train, y_train, X_test : np.ndarray
    max_depth : int or None
        树的最大深度。

    Returns
    -------
    y_pred : np.ndarray
    info : dict
        包含 'feature_importances'。

    适用场景: 分类规则提取, 特征重要性分析, 可解释分类。
    """
    from sklearn.tree import DecisionTreeClassifier

    model = DecisionTreeClassifier(criterion='gini', max_depth=max_depth,
                                   random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    return y_pred, {'feature_importances': model.feature_importances_}


def naive_bayes_classify(X_train, y_train, X_test, var_smoothing=1e-9):
    """
    朴素贝叶斯分类 (Gaussian Naive Bayes).

    Parameters
    ----------
    X_train, y_train, X_test : np.ndarray
    var_smoothing : float

    Returns
    -------
    y_pred : np.ndarray
    info : dict

    适用场景: 文本分类, 垃圾邮件检测, 快速基线分类器。
    """
    from sklearn.naive_bayes import GaussianNB

    model = GaussianNB(var_smoothing=var_smoothing)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    return y_pred, {}


def bp_neural_network_regress(X_train, y_train, X_test, hidden_layers=(10,),
                               max_iter=1000, random_state=42):
    """
    BP神经网络回归 (MLP Regressor).

    Parameters
    ----------
    X_train : np.ndarray, shape (n_train, n_features)
    y_train : np.ndarray, shape (n_train,)
    X_test : np.ndarray, shape (n_test, n_features)
    hidden_layers : tuple
        各隐藏层神经元数量，如 (64, 32)。
    max_iter : int
    random_state : int

    Returns
    -------
    y_pred : np.ndarray
    info : dict

    适用场景: 非线性回归, 复杂函数逼近, 预测建模。
    """
    from sklearn.neural_network import MLPRegressor
    from sklearn.preprocessing import StandardScaler

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = MLPRegressor(hidden_layer_sizes=hidden_layers, activation='relu',
                         solver='adam', max_iter=max_iter, random_state=random_state)
    model.fit(X_train_scaled, y_train)
    y_pred = model.predict(X_test_scaled)
    return y_pred, {}


def linear_regression_fit(X_train, y_train, X_test):
    """
    多元线性回归.

    Parameters
    ----------
    X_train, y_train, X_test : np.ndarray

    Returns
    -------
    y_pred : np.ndarray
    info : dict
        包含 'coefficients', 'intercept'。

    适用场景: 线性关系建模, 基准模型, 经济预测。
    """
    from sklearn.linear_model import LinearRegression

    model = LinearRegression()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    return y_pred, {
        'coefficients': model.coef_,
        'intercept': model.intercept_,
    }


def polynomial_regression_fit(X_train, y_train, X_test, degree=2):
    """
    多项式回归.

    通过构造多项式特征后进行线性回归，实现对非线性关系的拟合。

    Parameters
    ----------
    X_train, y_train, X_test : np.ndarray
    degree : int
        多项式次数。

    Returns
    -------
    
    y_pred : np.ndarray
    info : dict
        包含 'coefficients', 'intercept'。

    适用场景: 非线性数据拟合, 趋势分析, 曲线回归。
    """
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import PolynomialFeatures
    from sklearn.preprocessing import StandardScaler

    poly = PolynomialFeatures(degree=degree, include_bias=False)
    scaler = StandardScaler()

    X_train_poly = scaler.fit_transform(poly.fit_transform(X_train))
    X_test_poly = scaler.transform(poly.transform(X_test))

    model = LinearRegression()
    model.fit(X_train_poly, y_train)
    y_pred = model.predict(X_test_poly)

    return y_pred, {
        'coefficients': model.coef_,
        'intercept': model.intercept_,
    }
