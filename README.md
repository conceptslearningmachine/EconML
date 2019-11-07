[![Build Status](https://dev.azure.com/ms/EconML/_apis/build/status/Microsoft.EconML?branchName=master)](https://dev.azure.com/ms/EconML/_build/latest?definitionId=49&branchName=master)
[![PyPI version](https://img.shields.io/pypi/v/econml.svg)](https://pypi.org/project/econml/)
[![PyPI wheel](https://img.shields.io/pypi/wheel/econml.svg)](https://pypi.org/project/econml/)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/econml.svg)](https://pypi.org/project/econml/)



<h1><img src="https://www.microsoft.com/en-us/research/wp-content/uploads/2016/12/MSR-ALICE-HeaderGraphic-1920x720_1-800x550.jpg" width="130px" align="left" style="margin-right: 10px;"> EconML: A Python Package for ML-Based Heterogeneous Treatment Effects Estimation</h1>

**EconML** is a Python package for estimating heterogeneous treatment effects from observational data via machine learning. This package was designed and built as part of the [ALICE project](https://www.microsoft.com/en-us/research/project/alice/) at Microsoft Research with the goal to combine state-of-the-art machine learning 
techniques with econometrics to bring automation to complex causal inference problems. The promise of EconML:

* Implement recent techniques in the literature at the intersection of econometrics and machine learning
* Maintain flexibility in modeling the effect heterogeneity (via techniques such as random forests, boosting, lasso and neural nets), while preserving the causal interpretation of the learned model and often offering valid confidence intervals
* Use a unified API
* Build on standard Python packages for Machine Learning and Data Analysis

In a nutshell, this
toolkit is designed to measure the causal effect of some treatment variable(s) `T` on an outcome 
variable `Y`, controlling for a set of features `X`. For detailed information about the package, 
consult the documentation at https://econml.azurewebsites.net/.

<details>
<summary><strong><em>Table of Contents</em></strong></summary>

- [Introduction](#Introduction)
  - [About Treatment Effect Estimation](#About-Treatment-Effect-Estimation)
  - [Example Applications](#Example-Applications)
- [News](#News)
- [Getting Started](#Getting-Started)
  - [Installation](#Installation)
  - [Usage Examples](#Usage-Examples)
- [For Developers](#For-Developers)
  - [Running the tests](#Running-the-tests)
  - [Generating the documentation](#Generating-the-documentation)
- [Blogs and Publications](#Blogs-and-Publications)
- [Citation](#Citation)
- [Contributing and Feedback](#Contributing-and-Feedback)
- [References](#References)

</details>

# Introduction

## About Treatment Effect Estimation

One of the biggest promises of machine learning is to automate decision making in a multitude of domains. At the core of many data-driven personalized decision scenarios is the estimation of heterogeneous treatment effects: what is the causal effect of an intervention on an outcome of interest for a sample with a particular set of features? 

Such questions arise frequently in customer segmentation (what is the effect of placing a customer in a tier over another tier), dynamic pricing (what is the effect of a pricing policy on demand) and medical studies (what is the effect of a treatment on a patient). In many such settings we have an abundance of observational data, where the treatment was chosen via some unknown policy, but the ability to run control A/B tests is limited.

## Example Applications

<table style="width:80%">
  <tr align="left">
    <td width="25%"><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/Business_card_-_The_Noun_Project.svg/610px-Business_card_-_The_Noun_Project.svg.png"/></td>
    <td width="75%">
        <h4>Customer Targeting</h4>
        <p> Businesses offer personalized incentives to customers to increase sales and level of engagement. Any such personalized intervention corresponds to a monetary investment and the main question that business analytics are called to answer is: what is the return on investment? Analyzing the ROI is inherently a treatment effect question: what was the effect of any investment on a customer's spend? Understanding how ROI varies across customers can enable more targeted investment policies and increased ROI via better targeting. 
        </p>
    </td>
  </tr>
  <tr align="left">
    <td width="25%"><img src="https://upload.wikimedia.org/wikipedia/commons/c/c9/Online-shop_button.jpg"/></td>
    <td width="75%">
        <h4>Personalized Pricing</h4>
        <p>Personalized discounts have are widespread in the digital economy. To set the optimal personalized discount policy a business needs to understand what is the effect of a drop in price on the demand of a customer for a product as a function of customer characteristics. The estimation of such personalized demand elasticities can also be phrased in the language of heterogeneous treatment effects, where the treatment is the price on the demand as a function of observable features of the customer. </p>
    </td>
  </tr>
  <tr align="left">
    <td><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/VariousPills.jpg/640px-VariousPills.jpg"/></td>
    <td width="75%">
        <h4>Stratification in Clinical Trials</h4>
        <p>
        Which patients should be selected for a clinical trial? If we want to demonstrate that a clinical treatment has an effect on at least some subset of a population then fully randomized clinical trials are inappropriate as they will solely estimate average effects. Using heterogeneous treatment effect techniques, we can use observational data to come up with estimates of these effects and identify good candidate patients for a clinical trial that our model estimates have high treatment effects.
        </p>
    </td>
  </tr>
  <tr align="left">
    <td width="25%"><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Mouse-cursor-hand-pointer.svg/1023px-Mouse-cursor-hand-pointer.svg.png" width="200" /></td>
    <td width="75%">
        <h4>Learning Click-Through-Rates</h4>
    <p>
        In the design of a page layout and ad placement, it is important to understand the click-through-rate of page components on different positions of a page. Modern approaches may be to run multiple A/B tests, but when such page component involve revenue considerations, then observational data can help guide correct A/B tests to run. Heterogeneous treatment effect estimation can provide estimates of the click-through-rate of page components from observational data. In this setting, the treatment is simply whether the component is placed on that page position and the response is whether the user clicked on it.
    </p>
    </td>
  </tr>
</table>

# News
 
 **06/03/2019:** Release v0.4, see release notes [here](https://github.com/Microsoft/EconML/releases/tag/v0.4). 

**05/03/2019:** Release v0.3, see release notes [here](https://github.com/Microsoft/EconML/releases/tag/v0.3).

**04/10/2019:** Release v0.2, see release notes [here](https://github.com/Microsoft/EconML/releases/tag/v0.2).

**03/06/2019:** Release v0.1, welcome to have a try and provide feedback.

# Getting Started

## Installation

Install the latest release from [PyPI](https://pypi.org/project/econml/):
```
pip install econml
```
To install from source, see [For Developers](#for-developers) section below.

## Usage Examples

* [Double Machine Learning](#references)

  ```Python
  from econml.dml import DMLCateEstimator
  from sklearn.linear_model import LassoCV
  
  est = DMLCateEstimator(model_y=LassoCV(), model_t=LassoCV())
  est.fit(Y, T, X, W) # W -> high-dimensional confounders, X -> features
  treatment_effects = est.effect(X_test)
  ```

* [Orthogonal Random Forests](#references)

  ```Python
  from econml.ortho_forest import ContinuousTreatmentOrthoForest
  # Use defaults
  est = ContinuousTreatmentOrthoForest()
  # Or specify hyperparameters
  est = ContinuousTreatmentOrthoForest(n_trees=500, min_leaf_size=10, max_depth=10, 
                                       subsample_ratio=0.7, lambda_reg=0.01,
                                       model_T=LassoCV(cv=3), model_Y=LassoCV(cv=3)
                                       )
  est.fit(Y, T, X, W)
  treatment_effects = est.effect(X_test)
    ```

* [Deep Instrumental Variables](#references)
  
  ```Python
  import keras
  from econml.deepiv import DeepIVEstimator

  treatment_model = keras.Sequential([keras.layers.Dense(128, activation='relu', input_shape=(2,)),
                                     keras.layers.Dropout(0.17),
                                     keras.layers.Dense(64, activation='relu'),
                                     keras.layers.Dropout(0.17),
                                     keras.layers.Dense(32, activation='relu'),
                                     keras.layers.Dropout(0.17)])
  response_model = keras.Sequential([keras.layers.Dense(128, activation='relu', input_shape=(2,)),
                                    keras.layers.Dropout(0.17),
                                    keras.layers.Dense(64, activation='relu'),
                                    keras.layers.Dropout(0.17),
                                    keras.layers.Dense(32, activation='relu'),
                                    keras.layers.Dropout(0.17),
                                    keras.layers.Dense(1)])
  est = DeepIVEstimator(n_components=10, # Number of gaussians in the mixture density networks)
                        m=lambda z, x: treatment_model(keras.layers.concatenate([z, x])), # Treatment model
                        h=lambda t, x: response_model(keras.layers.concatenate([t, x])), # Response model
                        n_samples=1 # Number of samples used to estimate the response
                        )
  est.fit(Y, T, X, Z) # Z -> instrumental variables
  treatment_effects = est.effect(T0, T1, X_test)
  ```


* Bootstrap Confidence Intervals
  ```Python
  from econml.dml import DMLCateEstimator
  
  est = DMLCateEstimator(model_y=LassoCV(), model_t=LassoCV(), inference='bootstrap')
  est.fit(Y, T, X, W)
  treatment_effect_interval = est.effect_interval(X_test, lower=1, upper=99)
  ```

To see more complex examples, go to the [notebooks](https://github.com/Microsoft/EconML/tree/master/notebooks) section of the repository. For a more detailed description of the treatment effect estimation algorithms, see the EconML [documentation](https://econml.azurewebsites.net/).

# For Developers

You can get started by cloning this repository. We use 
[setuptools](https://setuptools.readthedocs.io/en/latest/index.html) for building and distributing our package.
We rely on some recent features of setuptools, so make sure to upgrade to a recent version with
`pip install setuptools --upgrade`.  Then from your local copy of the repository you can run `python setup.py develop` to get started.

## Running the tests

This project uses [pytest](https://docs.pytest.org/) for testing.  To run tests locally after installing the package, 
you can use `python setup.py pytest`.

## Generating the documentation

This project's documentation is generated via [Sphinx](https://www.sphinx-doc.org/en/master/index.html).  To generate a local copy
of the documentation from a clone of this repository, just run `python setup.py build_sphinx -W -E -a`, which will build the documentation and place it
under the `build/sphinx/html` path.

The reStructuredText files that make up the documentation are stored in the [docs directory](https://github.com/Microsoft/EconML/tree/master/doc); module documentation is automatically generated by the Sphinx build process.

# Blogs and Publications

* June 2019: [Treatment Effects with Instruments paper](https://arxiv.org/pdf/1905.10176.pdf)

* May 2019: [Open Data Science Conference Workshop](https://staging5.odsc.com/training/portfolio/machine-learning-estimation-of-heterogeneous-treatment-effect-the-microsoft-econml-library) 

* 2018: [Orthogonal Random Forests paper](http://proceedings.mlr.press/v97/oprescu19a.html)

* 2017: [DeepIV paper](http://proceedings.mlr.press/v70/hartford17a/hartford17a.pdf)

# Citation

If you use EconML in your research, please cite us as follows:

   Microsoft Research. **EconML: A Python Package for ML-Based Heterogeneous Treatment Effects Estimation.** https://github.com/microsoft/EconML, 2019. Version 0.x.

BibTex:

```
@misc{econml,
  author={Microsoft Research},
  title={{EconML}: {A Python Package for ML-Based Heterogeneous Treatment Effects Estimation}},
  howpublished={https://github.com/microsoft/EconML},
  note={Version 0.x},
  year={2019}
}
```

# Contributing and Feedback

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.microsoft.com.

When you submit a pull request, a CLA-bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., label, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

# References

V. Syrgkanis, V. Lei, M. Oprescu, M. Hei, K. Battocchi, G. Lewis.
**Machine Learning Estimation of Heterogeneous Treatment Effects with Instruments.**
[*Proceedings of the 33rd Conference on Neural Information Processing Systems (NeurIPS)*](https://arxiv.org/abs/1905.10176), 2019
**(Spotlight Presentation)**

D. Foster, V. Syrgkanis.
**Orthogonal Statistical Learning.**
[*Proceedings of the 32nd Annual Conference on Learning Theory (COLT)*](https://arxiv.org/pdf/1901.09036.pdf), 2019
**(Best Paper Award)**

M. Oprescu, V. Syrgkanis and Z. S. Wu.
**Orthogonal Random Forest for Causal Inference.**
[*Proceedings of the 36th International Conference on Machine Learning (ICML)*](http://proceedings.mlr.press/v97/oprescu19a.html), 2019.

V. Chernozhukov, D. Nekipelov, V. Semenova, V. Syrgkanis.
**Plug-in Regularized Estimation of High-Dimensional Parameters in Nonlinear Semiparametric Models.**
[*Arxiv preprint arxiv:1806.04823*](https://arxiv.org/abs/1806.04823), 2018.

Jason Hartford, Greg Lewis, Kevin Leyton-Brown, and Matt Taddy. **Deep IV: A flexible approach for counterfactual prediction.** [*Proceedings of the 34th International Conference on Machine Learning, ICML'17*](http://proceedings.mlr.press/v70/hartford17a/hartford17a.pdf), 2017.

V. Chernozhukov, D. Chetverikov, M. Demirer, E. Duflo, C. Hansen, and a. W. Newey. **Double Machine Learning for Treatment and Causal Parameters.** [*ArXiv preprint arXiv:1608.00060*](https://arxiv.org/abs/1608.00060), 2016.
