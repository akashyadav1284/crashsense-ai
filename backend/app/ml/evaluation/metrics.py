"""
Model Evaluation Metrics & Walk-Forward Validation for CrashSense AI.
Enforces chronological out-of-sample testing with expanding windows (Walk-Forward).
Calculates Brier Score, Log Loss, ROC-AUC, Balanced Accuracy, Calibration ECE, and Edge Tests.
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    brier_score_loss,
    log_loss,
    roc_auc_score,
    confusion_matrix,
)
from backend.app.ml.schemas.experiment import EvaluationMetrics, WalkForwardFoldResult
from backend.app.ml.models.base_model import BaseMLModel, BaselineFrequencyModel, IndependenceNullModel


def compute_metrics(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    threshold: float = 0.5
) -> EvaluationMetrics:
    """
    Compute rigorous classification and probabilistic scoring metrics.
    y_true: binary 0/1 array.
    y_proba: 1D array of predicted probabilities for class 1.
    """
    if len(y_true) == 0:
        return EvaluationMetrics(
            accuracy=0.0,
            balanced_accuracy=0.0,
            brier_score=0.25,
            log_loss=0.69315,
            roc_auc=0.5,
            expected_calibration_error=0.0,
            true_positives=0,
            false_positives=0,
            true_negatives=0,
            false_negatives=0,
            confusion_matrix=[[0, 0], [0, 0]]
        )

    # Thresholded predictions
    y_pred = (y_proba >= threshold).astype(int)

    acc = float(accuracy_score(y_true, y_pred))
    bal_acc = float(balanced_accuracy_score(y_true, y_pred))
    brier = float(brier_score_loss(y_true, y_proba))

    # Log loss bounded to avoid math domain errors
    y_proba_clipped = np.clip(y_proba, 1e-15, 1 - 1e-15)
    try:
        loss = float(log_loss(y_true, y_proba_clipped, labels=[0, 1]))
    except Exception:
        loss = 0.69315

    # ROC AUC (requires at least 2 distinct classes)
    if len(np.unique(y_true)) > 1:
        try:
            auc = float(roc_auc_score(y_true, y_proba))
        except Exception:
            auc = 0.5
    else:
        auc = 0.5

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    # Expected Calibration Error (ECE) with 10 bins
    ece = compute_ece(y_true, y_proba, n_bins=10)

    return EvaluationMetrics(
        accuracy=acc,
        balanced_accuracy=bal_acc,
        brier_score=brier,
        log_loss=loss,
        roc_auc=auc,
        expected_calibration_error=ece,
        true_positives=int(tp),
        false_positives=int(fp),
        true_negatives=int(tn),
        false_negatives=int(fn),
        confusion_matrix=cm.tolist()
    )


def compute_ece(y_true: np.ndarray, y_proba: np.ndarray, n_bins: int = 10) -> float:
    """Calculate Expected Calibration Error across equal-width probability bins."""
    if len(y_true) == 0:
        return 0.0

    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    n = len(y_true)

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]

        in_bin = (y_proba >= bin_lower) & (y_proba < bin_upper) if i < n_bins - 1 else (y_proba >= bin_lower) & (y_proba <= bin_upper)
        bin_count = np.sum(in_bin)

        if bin_count > 0:
            bin_acc = np.mean(y_true[in_bin])
            bin_conf = np.mean(y_proba[in_bin])
            ece += (bin_count / n) * np.abs(bin_acc - bin_conf)

    return float(ece)


def compute_calibration_curve_data(y_true: np.ndarray, y_proba: np.ndarray, n_bins: int = 10) -> List[Dict[str, Any]]:
    """Generate reliability diagram data points (predicted probability vs empirical frequency)."""
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    points = []

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]

        in_bin = (y_proba >= bin_lower) & (y_proba < bin_upper) if i < n_bins - 1 else (y_proba >= bin_lower) & (y_proba <= bin_upper)
        count = int(np.sum(in_bin))

        if count > 0:
            emp_freq = float(np.mean(y_true[in_bin]))
            avg_pred = float(np.mean(y_proba[in_bin]))
        else:
            emp_freq = 0.0
            avg_pred = float((bin_lower + bin_upper) / 2.0)

        points.append({
            "bin_index": i,
            "bin_range": f"{bin_lower:.2f} - {bin_upper:.2f}",
            "mean_predicted_probability": round(avg_pred, 4),
            "empirical_frequency": round(emp_freq, 4),
            "sample_count": count
        })

    return points


class WalkForwardValidator:
    """
    Chronological Walk-Forward Expanding Window Validator.
    Never shuffles; strictly preserves temporal causality.
    """

    def __init__(self, n_splits: int = 4, min_train_ratio: float = 0.5):
        self.n_splits = max(2, n_splits)
        self.min_train_ratio = min_train_ratio

    def evaluate(
        self,
        model_factory,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: List[str]
    ) -> Tuple[EvaluationMetrics, List[WalkForwardFoldResult]]:
        """
        Execute expanding window walk-forward validation across chronological folds.
        """
        n_samples = len(X)
        if n_samples < 50:
            raise ValueError(f"Insufficient samples for walk-forward validation: {n_samples} < 50")

        min_train_size = int(n_samples * self.min_train_ratio)
        test_step = (n_samples - min_train_size) // self.n_splits

        fold_results: List[WalkForwardFoldResult] = []
        all_y_test: List[int] = []
        all_y_proba: List[float] = []

        for fold_idx in range(self.n_splits):
            train_end = min_train_size + fold_idx * test_step
            test_end = train_end + test_step if fold_idx < self.n_splits - 1 else n_samples

            X_train, y_train = X[:train_end], y[:train_end]
            X_test, y_test = X[train_end:test_end], y[train_end:test_end]

            if len(X_test) == 0:
                continue

            # Instantiate and fit fresh model instance
            fold_model: BaseMLModel = model_factory()
            fold_model.fit(X_train, y_train, feature_names=feature_names)

            # Predict on out-of-sample chronological test partition
            proba = fold_model.predict_proba(X_test)[:, 1]
            fold_metrics = compute_metrics(y_test, proba)

            fold_results.append(WalkForwardFoldResult(
                fold_index=fold_idx + 1,
                train_start_index=0,
                train_end_index=train_end - 1,
                test_start_index=train_end,
                test_end_index=test_end - 1,
                train_samples=len(X_train),
                test_samples=len(X_test),
                metrics=fold_metrics
            ))

            all_y_test.extend(y_test.tolist())
            all_y_proba.extend(proba.tolist())

        # Aggregate overall out-of-sample metrics across all walk-forward folds
        aggregate_metrics = compute_metrics(np.array(all_y_test), np.array(all_y_proba))
        return aggregate_metrics, fold_results

