"""  Created on 03/06/2022::
------------- simul_commonprob.py -------------

**Authors**: L. Mingarelli
"""

import numpy as np
from scipy.stats import norm, mvn

def simul_commonprob(margprob, corr=0, method="integrate", n1=10**5, n2=10):
    """
    Compute common probabilities of binary random variates
    generated by thresholding normal variates at 0.

    The output of this function is used by rmvbin. For all combinations of marginprob[i], marginprob[j]
    and corr[k], the probability that both components of a normal random variable with mean qnorm(marginprob[i,j])
    and correlation corr[k] are larger than zero is computed.
    The probabilities are either computed by numerical integration of the multivariate normal density,
    or by Monte Carlo simulation.
    For normal usage of rmvbin it is not necessary to use this function, one simulation result is provided
    as variable SimulVals in this package and loaded by default.

    Args:
        margprob: vector of marginal probabilities.
        corr: vector of correlation values for normal distribution.
        method: either "integrate" or "monte carlo".
        n1: number of normal variates if method is "monte carlo".
        n2: number of repetitions if method is "monte carlo".

    Returns:
        an array of dimension (len(margprob), len(margprob), len(corr)).
    """
    lm = len(margprob)
    lr = len(corr)

    z = np.zeros((lm, lm, lr))

    method = ["integrate", "monte carlo"].index(method)
    if method == -1:
        raise ValueError("invalid method")

    for k in range(lr):
        sigma = np.array([[1, corr[k]], [corr[k], 1]])
        for m in range(lm):
            q1 = norm.ppf(margprob[m])
            for n in range(m, lm):
                corr[k] = round(corr[k], 12)
                margprob[m] = round(margprob[m], 12)
                margprob[n] = round(margprob[n], 12)
                print(corr[k], margprob[m], margprob[n], ": ", end="")
                q2 = norm.ppf(margprob[n])

                if corr[k] == -1:
                    z[m, n, k] = max(margprob[m] + margprob[n] - 1, 0)
                    print("done")
                elif corr[k] == 0:
                    z[m, n, k] = margprob[m] * margprob[n]
                    print("done")
                elif corr[k] == 1:
                    z[m, n, k] = min(margprob[m], margprob[n])
                    print("done")
                elif margprob[m] * margprob[n] == 0:
                    z[m, n, k] = 0
                    print("done")
                elif margprob[m] == 1:
                    z[m, n, k] = margprob[n]
                    print("done")
                elif margprob[n] == 1:
                    z[m, n, k] = margprob[m]
                    print("done")
                elif method == 0: # Integrate
                    a, _ = mvn.mvnun([0, 0], [np.inf, np.inf], [q1, q2], sigma)
                    if not np.isfinite(a):
                        z[m, n, k] = np.nan
                    else:
                        z[m, n, k] = a
                else:               # Monte Carlo
                    x2 = np.zeros(n2)
                    for l in range(n2):
                        x1 = np.random.multivariate_normal([q1, q2], sigma, size=n1)
                        x2[l] = np.mean((x1[:, 0] > 0) & (x1[:, 1] > 0))
                    z[m, n, k] = np.mean(x2)
                    print("done")
                z[n, m, k] = z[m, n, k]

    D = {}
    for j in range(lm):
        for k in range(j, lm):
            mj = round(margprob[j], 10)
            mk = round(margprob[k], 10)
            D[(mj, mk)] = D[(mj, mk)] = np.vstack((corr, z[j, k, :]))


    return D


# I think by this time these two should be ok - keep the above
def create_joint_prob_corr_mat(_N=20, to_dict=True):
    """
    This function generates the mat of joint probabilities for
    each configuration of marginal probabilities and correlation values.
    Args:
        _N (int): xxx
        to_dict (bool): xxx
    """
    N = _N +1
    N_c = _N*2 + 1
    p = np.linspace(0,1,N)  # Range of marginal probability
    corr = np.linspace(-1., 1., N_c)  # Range of correlations

    mat = np.zeros(shape=(N_c, N, N))

    for i in range(N_c):
        sig = np.matrix([[1., corr[i]], [corr[i], 1.]])
        for j in range(N):
            for k in range(j, N):

                if corr[i] == -1:
                    jp = max(0., p[j] + p[k] - 1.)
                elif corr[i] == 0.:
                    jp = p[j] * p[k]
                elif corr[i] == 1.:
                    jp = min(p[j], p[k])
                elif p[j] * p[k] == 0. or p[j] == 1 or p[k] == 1.:
                    jp = p[j] * p[k]
                else:
                    jp = mvn.mvnun(np.array([0., 0.]), np.array([np.inf, np.inf]),
                                   [norm.ppf(p[j]), norm.ppf(p[k])],
                                   sig)[0]

                mat[i, j, k] = mat[i, k, j] = jp

    if to_dict:
        n_table = {}

        # convert to dictionary:
        for j in range(len(p)):
            for k in range(j, len(p)):
                pj = round(p[j], 10)
                pk = round(p[k], 10)
                n_table[(pj, pk)] = n_table[(pj, pk)] = np.array((corr, mat[:, j, k]))

        return n_table

    return mat