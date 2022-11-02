# -*- coding: utf-8 -*-
"""
Created on Mon Jan 27 16:23:54 2014

Copyright (c) 2013-2014, CEA/DSV/I2BM/Neurospin. All rights reserved.

@author:  Tommy Löfstedt
@email:   tommy.loefstedt@cea.fr
@license: BSD 3-clause.
"""
import numpy as np

from .grad import grad_gl
from .grad import grad_l1
from .grad import grad_l2_squared
from .utils import bisection_method

__all__ = ['load']


def load(l, k, g, beta, M, e, A, snr=None, intercept=False):
    """Returns data generated such that we know the exact solution.

    The data generated by this function is fit to the Linear regression + L1 +
    L2 + Group lasso function, i.e. to:

        f(b) = (1 / 2).|Xb - y|² + l.|b|_1 + (k / 2).|b|² + g.GL(b),

    where |.|_1 is the L1 norm, |.|² is the squared L2 norm and GL is the
    group lasso penalty.

    Parameters
    ----------
    l : Non-negative float. The L1 regularisation parameter.

    k : Non-negative float. The L2 regularisation parameter.

    g : Non-negative float. The group lasso regularisation parameter.

    beta : Numpy array (p-by-1). The regression vector to generate data from.

    M : Numpy array (n-by-p). The matrix to use when building data. This
            matrix carries the desired correlation structure of the generated
            data. The generated data will be a column-scaled version of this
            matrix.

    e : Numpy array (n-by-1). The error vector e = Xb - y. This vector carries
            the desired distribution of the residual.

    A : Numpy or (usually) scipy.sparse array (K-by-p). The linear operator
            for the Nesterov function.

    snr : Positive float. Signal-to-noise ratio between model and residual.

    intercept : Boolean. Whether or not to include an intercept variable. This
            variable is not penalised. Note that if intercept is True, then e
            will be centred.

    Returns
    -------
    X : Numpy array (n-by-p). The generated X matrix.

    y : Numpy array (n-by-1). The generated y vector.

    beta : Numpy array (p-by-1). The regression vector with the correct snr.
    """
    l = float(l)
    k = float(k)
    g = float(g)

    if intercept:
        e = e - np.mean(e)

    if snr is not None:
        def f(x):
            X, y = _generate(l, k, g, x * beta, M, e, A, intercept)

#            print "snr = %.5f = %.5f = |X.b| / |e| = %.5f / %.5f" \
#                   % (snr, np.linalg.norm(np.dot(X, x * beta)) \
#                                           / np.linalg.norm(e),
#                      np.linalg.norm(np.dot(X, x * beta)), np.linalg.norm(e))

            return (np.linalg.norm(np.dot(X, x * beta)) / np.linalg.norm(e)) \
                   - snr

        snr = bisection_method(f, low=0.0, high=np.sqrt(snr), maxiter=30)

        beta = beta * snr

    X, y = _generate(l, k, g, beta, M, e, A, intercept)

    return X, y, beta


def _generate(l, k, g, beta, M, e, A, intercept):

    p = beta.shape[0]

    if intercept:
        gradL1 = grad_l1(beta[1:, :])
        gradL2 = grad_l2_squared(beta[1:, :])
        gradGL = grad_gl(beta[1:, :], A)
    else:
        gradL1 = grad_l1(beta)
        gradL2 = grad_l2_squared(beta)
        gradGL = grad_gl(beta, A)

    alpha = -(l * gradL1 + k * gradL2 + g * gradGL)
    Mte = np.dot(M.T, e)
    if intercept:
        alpha = np.divide(alpha, Mte[1:, :])
    else:
        alpha = np.divide(alpha, Mte)

    X = np.ones(M.shape)
    if intercept:
        for i in range(p - 1):
            X[:, i + 1] = M[:, i + 1] * alpha[i, 0]
    else:
        for i in range(p):
            X[:, i] = M[:, i] * alpha[i, 0]

    y = np.dot(X, beta) - e

    return X, y
