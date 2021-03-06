# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import unittest
import pytest
from sklearn.base import TransformerMixin
from sklearn.linear_model import LinearRegression, Lasso, LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, FunctionTransformer
from sklearn.model_selection import KFold
from econml.dml import DMLCateEstimator, LinearDMLCateEstimator, SparseLinearDMLCateEstimator, KernelDMLCateEstimator
import numpy as np
from econml.utilities import shape, hstack, vstack, reshape, cross_product
from econml.inference import BootstrapInference
from contextlib import ExitStack


# all solutions to underdetermined (or exactly determined) Ax=b are given by A⁺b+(I-A⁺A)w for some arbitrary w
# note that if Ax=b is overdetermined, this will raise an assertion error
def rand_sol(A, b):
    """Generate a random solution to the equation Ax=b."""
    assert np.linalg.matrix_rank(A) <= len(b)
    A_plus = np.linalg.pinv(A)
    x = A_plus @ b
    return x + (np.eye(x.shape[0]) - A_plus @ A) @ np.random.normal(size=x.shape)


class TestDML(unittest.TestCase):

    def test_cate_api(self):
        """Test that we correctly implement the CATE API."""
        n = 20

        def make_random(is_discrete, d):
            if d is None:
                return None
            sz = (n, d) if d >= 0 else (n,)
            if is_discrete:
                while True:
                    arr = np.random.choice(['a', 'b', 'c'], size=sz)
                    # ensure that we've got at least two of every element
                    _, counts = np.unique(arr, return_counts=True)
                    if len(counts) == 3 and counts.min() > 1:
                        return arr
            else:
                return np.random.normal(size=sz)

        for d_t in [2, 1, -1]:
            for is_discrete in [True, False] if d_t <= 1 else [False]:
                for d_y in [3, 1, -1]:
                    for d_x in [2, None]:
                        for d_w in [2, None]:
                            W, X, Y, T = [make_random(is_discrete, d)
                                          for is_discrete, d in [(False, d_w),
                                                                 (False, d_x),
                                                                 (False, d_y),
                                                                 (is_discrete, d_t)]]

                            d_t_final = 2 if is_discrete else d_t

                            effect_shape = (n,) + ((d_y,) if d_y > 0 else ())
                            marginal_effect_shape = ((n,) +
                                                     ((d_y,) if d_y > 0 else ()) +
                                                     ((d_t_final,) if d_t_final > 0 else ()))

                            # since T isn't passed to const_marginal_effect, defaults to one row if X is None
                            const_marginal_effect_shape = ((n if d_x else 1,) +
                                                           ((d_y,) if d_y > 0 else ()) +
                                                           ((d_t_final,) if d_t_final > 0 else()))

                            model_t = LogisticRegression() if is_discrete else Lasso()

                            # TODO: add stratification to bootstrap so that we can use it even with discrete treatments
                            all_infs = [None, 'statsmodels']
                            if not is_discrete:
                                all_infs.append(BootstrapInference(1))

                            for est, multi, infs in [(LinearDMLCateEstimator(model_y=Lasso(),
                                                                             model_t=model_t,
                                                                             discrete_treatment=is_discrete),
                                                      False,
                                                      all_infs),
                                                     (SparseLinearDMLCateEstimator(model_y=LinearRegression(),
                                                                                   model_t=model_t,
                                                                                   discrete_treatment=is_discrete),
                                                      True,
                                                      [None]),
                                                     (KernelDMLCateEstimator(model_y=LinearRegression(),
                                                                             model_t=model_t,
                                                                             discrete_treatment=is_discrete),
                                                      False,
                                                      [None])]:

                                if not(multi) and d_y > 1:
                                    continue

                                for inf in infs:
                                    with self.subTest(d_w=d_w, d_x=d_x, d_y=d_y, d_t=d_t,
                                                      is_discrete=is_discrete, est=est, inf=inf):
                                        est.fit(Y, T, X, W, inference=inf)
                                        # make sure we can call the marginal_effect and effect methods
                                        const_marg_eff = est.const_marginal_effect(X)
                                        marg_eff = est.marginal_effect(T, X)
                                        self.assertEqual(shape(marg_eff), marginal_effect_shape)
                                        self.assertEqual(shape(const_marg_eff), const_marginal_effect_shape)

                                        np.testing.assert_array_equal(
                                            marg_eff if d_x else marg_eff[0:1], const_marg_eff)

                                        T0 = np.full_like(T, 'a') if is_discrete else np.zeros_like(T)
                                        eff = est.effect(X, T0, T)
                                        self.assertEqual(shape(eff), effect_shape)

                                        if inf is not None:
                                            const_marg_eff_int = est.const_marginal_effect_interval(X)
                                            marg_eff_int = est.marginal_effect_interval(T, X)
                                            self.assertEqual(shape(marg_eff_int),
                                                             (2,) + marginal_effect_shape)
                                            self.assertEqual(shape(const_marg_eff_int),
                                                             (2,) + const_marginal_effect_shape)
                                            self.assertEqual(shape(est.effect_interval(X, T0, T)),
                                                             (2,) + effect_shape)

                                        est.score(Y, T, X, W)

                                        # make sure we can call effect with implied scalar treatments, no matter the
                                        # dimensions of T, and also that we warn when there are multiple treatments
                                        if d_t > 1:
                                            cm = self.assertWarns(Warning)
                                        else:
                                            cm = ExitStack()  # ExitStack can be used as a "do nothing" ContextManager
                                        with cm:
                                            effect_shape2 = (n if d_x else 1,) + ((d_y,) if d_y > 0 else())
                                            eff = est.effect(X) if not is_discrete else est.effect(X, 'a', 'b')
                                            self.assertEqual(shape(eff), effect_shape2)

    def test_can_use_vectors(self):
        """Test that we can pass vectors for T and Y (not only 2-dimensional arrays)."""
        dml = LinearDMLCateEstimator(LinearRegression(), LinearRegression(), featurizer=FunctionTransformer())
        dml.fit(np.array([1, 2, 3, 1, 2, 3]), np.array([1, 2, 3, 1, 2, 3]), np.ones((6, 1)))
        self.assertAlmostEqual(dml.coef_.reshape(())[()], 1)
        score = dml.score(np.array([1, 2, 3, 1, 2, 3]), np.array([1, 2, 3, 1, 2, 3]), np.ones((6, 1)))
        self.assertAlmostEqual(score, 0)

    def test_can_use_sample_weights(self):
        """Test that we can pass sample weights to an estimator."""
        dml = LinearDMLCateEstimator(LinearRegression(), LinearRegression(), featurizer=FunctionTransformer())
        dml.fit(np.array([1, 2, 3, 1, 2, 3]), np.array([1, 2, 3, 1, 2, 3]),
                np.ones((6, 1)), sample_weight=np.ones((6, )))
        self.assertAlmostEqual(dml.coef_.reshape(())[()], 1)

    def test_discrete_treatments(self):
        """Test that we can use discrete treatments"""
        dml = LinearDMLCateEstimator(LinearRegression(), LogisticRegression(C=1000),
                                     featurizer=FunctionTransformer(), discrete_treatment=True)
        # create a simple artificial setup where effect of moving from treatment
        #     1 -> 2 is 2,
        #     1 -> 3 is 1, and
        #     2 -> 3 is -1 (necessarily, by composing the previous two effects)
        # Using an uneven number of examples from different classes,
        # and having the treatments in non-lexicographic order,
        # Should rule out some basic issues.
        dml.fit(np.array([2, 3, 1, 3, 2, 1, 1, 1]), np.array([3, 2, 1, 2, 3, 1, 1, 1]), np.ones((8, 1)))
        np.testing.assert_almost_equal(dml.effect(np.ones((9, 1)),
                                                  np.array([1, 1, 1, 2, 2, 2, 3, 3, 3]),
                                                  np.array([1, 2, 3, 1, 2, 3, 1, 2, 3])),
                                       [0, 2, 1, -2, 0, -1, -1, 1, 0])
        dml.score(np.array([2, 3, 1, 3, 2, 1, 1, 1]), np.array([3, 2, 1, 2, 3, 1, 1, 1]), np.ones((8, 1)))

    def test_can_custom_splitter(self):
        # test that we can fit with a KFold instance
        dml = LinearDMLCateEstimator(LinearRegression(), LogisticRegression(C=1000),
                                     discrete_treatment=True, n_splits=KFold())
        dml.fit(np.array([1, 2, 3, 1, 2, 3]), np.array([1, 2, 3, 1, 2, 3]), np.ones((6, 1)))
        dml.score(np.array([1, 2, 3, 1, 2, 3]), np.array([1, 2, 3, 1, 2, 3]), np.ones((6, 1)))

        # test that we can fit with a train/test iterable
        dml = LinearDMLCateEstimator(LinearRegression(), LogisticRegression(C=1000),
                                     discrete_treatment=True, n_splits=[([0, 1, 2], [3, 4, 5])])
        dml.fit(np.array([1, 2, 3, 1, 2, 3]), np.array([1, 2, 3, 1, 2, 3]), np.ones((6, 1)))
        dml.score(np.array([1, 2, 3, 1, 2, 3]), np.array([1, 2, 3, 1, 2, 3]), np.ones((6, 1)))

    def test_can_use_statsmodel_inference(self):
        """Test that we can use statsmodels to generate confidence intervals"""
        dml = LinearDMLCateEstimator(LinearRegression(), LogisticRegression(C=1000),
                                     discrete_treatment=True)
        dml.fit(np.array([2, 3, 1, 3, 2, 1, 1, 1]), np.array(
            [3, 2, 1, 2, 3, 1, 1, 1]), np.ones((8, 1)), inference='statsmodels')
        interval = dml.effect_interval(np.ones((9, 1)),
                                       T0=np.array([1, 1, 1, 2, 2, 2, 3, 3, 3]),
                                       T1=np.array([1, 2, 3, 1, 2, 3, 1, 2, 3]),
                                       alpha=0.05)
        point = dml.effect(np.ones((9, 1)),
                           np.array([1, 1, 1, 2, 2, 2, 3, 3, 3]),
                           np.array([1, 2, 3, 1, 2, 3, 1, 2, 3]))
        assert len(interval) == 2
        lo, hi = interval
        assert lo.shape == hi.shape == point.shape
        assert (lo <= point).all()
        assert (point <= hi).all()
        assert (lo < hi).any()  # for at least some of the examples, the CI should have nonzero width

        interval = dml.const_marginal_effect_interval(np.ones((9, 1)), alpha=0.05)
        point = dml.const_marginal_effect(np.ones((9, 1)))
        assert len(interval) == 2
        lo, hi = interval
        assert lo.shape == hi.shape == point.shape
        assert (lo <= point).all()
        assert (point <= hi).all()
        assert (lo < hi).any()  # for at least some of the examples, the CI should have nonzero width

        interval = dml.coef__interval(alpha=0.05)
        point = dml.coef_
        assert len(interval) == 2
        lo, hi = interval
        assert lo.shape == hi.shape == point.shape
        assert (lo <= point).all()
        assert (point <= hi).all()
        assert (lo < hi).any()  # for at least some of the examples, the CI should have nonzero width

    def test_ignores_final_intercept(self):
        """Test that final model intercepts are ignored (with a warning)"""
        class InterceptModel:
            def fit(Y, X):
                pass

            def predict(X):
                return X + 1

        # (incorrectly) use a final model with an intercept
        dml = DMLCateEstimator(LinearRegression(), LinearRegression(),
                               model_final=InterceptModel,
                               featurizer=FunctionTransformer())
        # Because final model is fixed, actual values of T and Y don't matter
        t = np.random.normal(size=100)
        y = np.random.normal(size=100)
        with self.assertWarns(Warning):  # we should warn whenever there's an intercept
            dml.fit(y, t)
        assert dml.const_marginal_effect() == 1  # coefficient on X in InterceptModel is 1

    @staticmethod
    def _generate_recoverable_errors(a_X, X, a_W=None, W=None, featurizer=FunctionTransformer()):
        """Return error vectors e_t and e_y such that OLS can recover the true coefficients from both stages."""
        if W is None:
            W = np.empty((shape(X)[0], 0))
        if a_W is None:
            a_W = np.zeros((shape(W)[1],))
        # to correctly recover coefficients for T via OLS, we need e_t to be orthogonal to [W;X]
        WX = hstack([W, X])
        e_t = rand_sol(WX.T, np.zeros((shape(WX)[1],)))

        # to correctly recover coefficients for Y via OLS, we need ([X; W]⊗[1; ϕ(X); W])⁺ e_y =
        #                                                          -([X; W]⊗[1; ϕ(X); W])⁺ ((ϕ(X)⊗e_t)a_X+(W⊗e_t)a_W)
        # then, to correctly recover a in the third stage, we additionally need (ϕ(X)⊗e_t)ᵀ e_y = 0

        ϕ = featurizer.fit_transform(X)

        v_X = cross_product(ϕ, e_t)
        v_W = cross_product(W, e_t)

        M = np.linalg.pinv(cross_product(WX, hstack([np.ones((shape(WX)[0], 1)), ϕ, W])))
        e_y = rand_sol(vstack([M, v_X.T]), vstack([-M @ (v_X @ a_X + v_W @ a_W), np.zeros((shape(v_X)[1],))]))

        return e_t, e_y

    # TODO: it seems like roughly 20% of the calls to _test_sparse are failing - find out what's going wrong
    @pytest.mark.xfail
    def test_sparse(self):
        for _ in range(5):
            n_p = np.random.randint(2, 5)  # 2 to 4 products
            d_w = np.random.randint(0, 5)  # random number of covariates
            min_n = np.ceil(2 + d_w * (1 + (d_w + 1) / n_p))  # minimum number of rows per product
            n_r = np.random.randint(min_n, min_n + 3)
            with self.subTest(n_p=n_p, d_w=d_w, n_r=n_r):
                TestDML._test_sparse(n_p, d_w, n_r)

    # sparse test case: heterogeneous effect by product
    @staticmethod
    def _test_sparse(n_p, d_w, n_r):
        # need at least as many rows in e_y as there are distinct columns
        # in [X;X⊗W;W⊗W;X⊗e_t] to find a solution for e_t
        assert n_p * n_r >= 2 * n_p + n_p * d_w + d_w * (d_w + 1) / 2
        a = np.random.normal(size=(n_p,))  # one effect per product
        n = n_p * n_r
        p = np.tile(range(n_p), n_r)  # product id

        b = np.random.normal(size=(d_w + n_p,))
        g = np.random.normal(size=(d_w + n_p,))

        x = np.empty((2 * n, n_p))  # product dummies
        w = np.empty((2 * n, d_w))
        y = np.empty(2 * n)
        t = np.empty(2 * n)

        for fold in range(0, 2):
            x_f = OneHotEncoder().fit_transform(np.reshape(p, (-1, 1))).toarray()
            w_f = np.random.normal(size=(n, d_w))
            xw_f = hstack([x_f, w_f])
            e_t_f, e_y_f = TestDML._generate_recoverable_errors(a, x_f, W=w_f)

            t_f = xw_f @ b + e_t_f
            y_f = t_f * np.choose(p, a) + xw_f @ g + e_y_f

            x[fold * n:(fold + 1) * n, :] = x_f
            w[fold * n:(fold + 1) * n, :] = w_f
            y[fold * n:(fold + 1) * n] = y_f
            t[fold * n:(fold + 1) * n] = t_f

        dml = SparseLinearDMLCateEstimator(LinearRegression(fit_intercept=False), LinearRegression(
            fit_intercept=False), featurizer=FunctionTransformer())
        dml.fit(y, t, x, w)

        # note that this would fail for the non-sparse LinearDMLCateEstimator

        np.testing.assert_allclose(a, dml.coef_.reshape(-1))
        eff = reshape(t * np.choose(np.tile(p, 2), a), (-1,))
        np.testing.assert_allclose(eff, dml.effect(x, 0, t))
