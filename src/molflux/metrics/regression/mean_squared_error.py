"""Mean squared error regression loss."""

import logging
import warnings
from importlib.metadata import version
from typing import Any, List, Optional

import evaluate
from packaging.version import parse
from sklearn.metrics import mean_squared_error

import datasets

if parse(version("scikit-learn")) >= parse("1.4.0"):
    ROOT_MEAN_SQUARED_ERROR_AVAILABLE = True
    from sklearn.metrics import root_mean_squared_error
else:
    ROOT_MEAN_SQUARED_ERROR_AVAILABLE = False


from molflux.metrics.bases import HFMetric
from molflux.metrics.typing import ArrayLike, MetricResult

logger = logging.getLogger(__name__)

_DESCRIPTION = """
The mean_squared_error function computes mean square error, a risk metric
corresponding to the expected value of the squared (quadratic) error or loss.
"""

_KWARGS_DESCRIPTION = """
Args:
    predictions: Estimated target values.
    references: Ground truth (correct) target values.
    sample_weight (optional): Weighting of each sample.
    multioutput (optional): Defines aggregating of multiple output values.
        Array-like value defines weights used to average errors. Alternatively,
        one of {'raw_values', 'uniform_average'}. Defaults to 'uniform_average'.
        'raw_values' :
            Returns a full set of errors in case of multioutput input.
        'uniform_average' :
            Errors of all outputs are averaged with uniform weight.
    root (optional): If ``True`` returns RMSE value, if ``False`` returns MSE
        value. Defaults to ``False``.

        .. deprecated:: 0.23.0
           `root` is deprecated in 0.23.0 and will be removed in future releases.
           Use the `root_mean_squared_error` metric instead to calculate the root mean squared error.

Returns:
    mean_squared_error: A non-negative floating point value (the best value
    is 0.0), or an array of floating point values, one for each individual target.

Examples:
    >>> from molflux.metrics import load_metric
    >>> metric = load_metric("mean_squared_error")
    >>> predictions = [2.5, 0.0, 2, 8]
    >>> references = [3, -0.5, 2, 7]
    >>> metric.compute(predictions=predictions, references=references)
    {'mean_squared_error': 0.375}
    >>> references = [2.5, 0.0, 2, 8]
    >>> predictions = [3, -0.5, 2, 7]
    >>> metric = load_metric("mean_squared_error", config_name="multioutput")
    >>> predictions = [[0, 2],[-1, 2],[8, -5]]
    >>> references = [[0.5, 1],[-1, 1],[7, -6]]
    >>> metric.compute(predictions=predictions, references=references)
    {'mean_squared_error': 0.708...}
    >>> metric.compute(predictions=predictions, references=references, multioutput='raw_values')
    {'mean_squared_error': array([0.416..., 1.        ])}
    >>> metric.compute(predictions=predictions, references=references, multioutput=[0.3, 0.7])
    {'mean_squared_error': 0.825...}
"""

_CITATION = """\
@article{scikit-learn,
  title={Scikit-learn: Machine Learning in {P}ython},
  author={Pedregosa, F. and Varoquaux, G. and Gramfort, A. and Michel, V.
         and Thirion, B. and Grisel, O. and Blondel, M. and Prettenhofer, P.
         and Weiss, R. and Dubourg, V. and Vanderplas, J. and Passos, A. and
         Cournapeau, D. and Brucher, M. and Perrot, M. and Duchesnay, E.},
  journal={Journal of Machine Learning Research},
  volume={12},
  pages={2825--2830},
  year={2011}
}
"""


@evaluate.utils.file_utils.add_start_docstrings(_DESCRIPTION, _KWARGS_DESCRIPTION)
class MeanSquaredError(HFMetric):
    def _info(self) -> evaluate.MetricInfo:
        return evaluate.MetricInfo(
            description=_DESCRIPTION,
            citation=_CITATION,
            inputs_description=_KWARGS_DESCRIPTION,
            features=datasets.Features(
                {
                    "predictions": datasets.Sequence(datasets.Value("float")),
                    "references": datasets.Sequence(datasets.Value("float")),
                }
                if self.config_name == "multioutput"
                else {
                    "predictions": datasets.Value("float"),
                    "references": datasets.Value("float"),
                },
            ),
            reference_urls=[
                "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.mean_squared_error.html",
            ],
        )

    def _score(
        self,
        *,
        predictions: ArrayLike,
        references: ArrayLike,
        sample_weight: Optional[List[float]] = None,
        multioutput: str = "uniform_average",
        root: bool = "deprecated",  # type: ignore[assignment]
        **kwargs: Any,
    ) -> MetricResult:
        root_kwarg_set_by_user = root != "deprecated"
        if root_kwarg_set_by_user:
            warnings.warn(
                (
                    "'root' is deprecated in version 0.24.0 and "
                    "will be removed in future versions. To calculate the "
                    "root mean squared error, use the metric "
                    "'root_mean_squared_error'."
                ),
                FutureWarning,
                stacklevel=1,
            )
        else:  # swap in with actual default value
            root = False

        # TODO(avianello): cleanup once we can drop python 3.8 (RMSE will always be available)
        if ROOT_MEAN_SQUARED_ERROR_AVAILABLE:  # py3.9+
            if root:
                score = root_mean_squared_error(
                    y_true=references,
                    y_pred=predictions,
                    sample_weight=sample_weight,
                    multioutput=multioutput,
                )

            else:
                score = mean_squared_error(
                    y_true=references,
                    y_pred=predictions,
                    sample_weight=sample_weight,
                    multioutput=multioutput,
                )

        else:  # py3.8
            score = mean_squared_error(
                y_true=references,
                y_pred=predictions,
                sample_weight=sample_weight,
                multioutput=multioutput,
                squared=not root,
            )

        return {self.tag: score}
