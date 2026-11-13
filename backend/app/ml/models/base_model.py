"""
Abstract Base Model and Model Implementations for CRASHSENSE AI ML Research Lab.
Includes strict no-leakage baselines (Historical Frequency, Null Independence),
Logistic Regression, Random Forest, HistGradientBoosting, and XGBoost.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import joblib
import os


class BaseMLModel(ABC):
    """Abstract base class for all CrashSense AI research models."""

    def __init__(self, name: str, algorithm: str, hyperparameters: Optional[Dict[str, Any]] = None):
        self.name = name
        self.algorithm = algorithm
        self.hyperparameters = hyperparameters or {}
        self.is_fitted = False
        self.feature_names: List[str] = []
        self.model = None

    @abstractmethod
    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: Optional[List[str]] = None) -> "BaseMLModel":
        """Fit model on historical training data."""
        pass

    @abstractmethod
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict class probabilities: returns array of shape (N, 2) where col 1 is P(bust >= threshold)."""
        pass

    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        """Predict binary classification based on decision threshold."""
        proba = self.predict_proba(X)
        return (proba[:, 1] >= threshold).astype(int)

    def get_feature_importance(self) -> Dict[str, float]:
        """Extract normalized feature importances if supported."""
        return {}

    def save(self, filepath: str) -> None:
        """Persist model artifact using joblib."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: str) -> "BaseMLModel":
        """Load persisted model artifact."""
        return joblib.load(filepath)


class BaselineFrequencyModel(BaseMLModel):
    """
    Empirical Baseline Model.
    Predicts constant probability equal to the historical base rate P(y=1) in the training set.
    Any valid ML model must statistically outperform this baseline.
    """

    def __init__(self, hyperparameters: Optional[Dict[str, Any]] = None):
        super().__init__(name="Historical Frequency Baseline", algorithm="BASELINE_FREQUENCY", hyperparameters=hyperparameters)
        self.base_rate: float = 0.5

    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: Optional[List[str]] = None) -> "BaselineFrequencyModel":
        if len(y) > 0:
            self.base_rate = float(np.mean(y))
        else:
            self.base_rate = 0.5
        self.is_fitted = True
        self.feature_names = feature_names or []
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        n = X.shape[0]
        p = np.full(n, self.base_rate)
        return np.column_stack([1.0 - p, p])


class IndependenceNullModel(BaseMLModel):
    """
    Theoretical Null CSPRNG Independence Model.
    For crash games with house edge h (typically 1%-3%) and multiplier target M:
    Theoretical P(multiplier >= M) = (1 - h) / M.
    Assumes zero memory (IID sequence).
    """

    def __init__(self, target_multiplier: float = 2.0, house_edge: float = 0.01, hyperparameters: Optional[Dict[str, Any]] = None):
        params = hyperparameters or {}
        params.setdefault("target_multiplier", target_multiplier)
        params.setdefault("house_edge", house_edge)
        super().__init__(name="Null CSPRNG Independence Baseline", algorithm="NULL_INDEPENDENCE", hyperparameters=params)
        self.target_multiplier = float(params.get("target_multiplier", 2.0))
        self.house_edge = float(params.get("house_edge", 0.01))
        # Theoretical probability under fair/provably fair crash formula: P(X >= M) = (1 - h) / M
        self.theoretical_prob = max(0.001, min(0.999, (1.0 - self.house_edge) / self.target_multiplier))

    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: Optional[List[str]] = None) -> "IndependenceNullModel":
        self.is_fitted = True
        self.feature_names = feature_names or []
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        n = X.shape[0]
        p = np.full(n, self.theoretical_prob)
        return np.column_stack([1.0 - p, p])


class LogisticRegressionModel(BaseMLModel):
    """Regularized Logistic Regression with feature standardization."""

    def __init__(self, hyperparameters: Optional[Dict[str, Any]] = None):
        super().__init__(name="Logistic Regression", algorithm="LOGISTIC_REGRESSION", hyperparameters=hyperparameters)
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline

        c_val = float(self.hyperparameters.get("C", 1.0))
        penalty = self.hyperparameters.get("penalty", "l2")
        solver = self.hyperparameters.get("solver", "lbfgs")

        self.pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(C=c_val, penalty=penalty, solver=solver, max_iter=1000, random_state=42))
        ])

    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: Optional[List[str]] = None) -> "LogisticRegressionModel":
        self.pipeline.fit(X, y)
        self.is_fitted = True
        self.feature_names = feature_names or []
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.pipeline.predict_proba(X)

    def get_feature_importance(self) -> Dict[str, float]:
        if not self.is_fitted or not self.feature_names:
            return {}
        clf = self.pipeline.named_steps["clf"]
        coefs = np.abs(clf.coef_[0])
        total = np.sum(coefs) if np.sum(coefs) > 0 else 1.0
        normalized = coefs / total
        return {name: float(imp) for name, imp in zip(self.feature_names, normalized)}


class RandomForestModel(BaseMLModel):
    """Ensemble Random Forest Classifier."""

    def __init__(self, hyperparameters: Optional[Dict[str, Any]] = None):
        super().__init__(name="Random Forest", algorithm="RANDOM_FOREST", hyperparameters=hyperparameters)
        from sklearn.ensemble import RandomForestClassifier

        n_estimators = int(self.hyperparameters.get("n_estimators", 100))
        max_depth = self.hyperparameters.get("max_depth", 6)
        min_samples_split = int(self.hyperparameters.get("min_samples_split", 5))

        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            random_state=42,
            n_jobs=-1
        )

    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: Optional[List[str]] = None) -> "RandomForestModel":
        self.model.fit(X, y)
        self.is_fitted = True
        self.feature_names = feature_names or []
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict_proba(X)

    def get_feature_importance(self) -> Dict[str, float]:
        if not self.is_fitted or not self.feature_names:
            return {}
        importances = self.model.feature_importances_
        return {name: float(imp) for name, imp in zip(self.feature_names, importances)}


class HistGradientBoostingModel(BaseMLModel):
    """Histogram-based Gradient Boosting Classifier."""

    def __init__(self, hyperparameters: Optional[Dict[str, Any]] = None):
        super().__init__(name="HistGradientBoosting", algorithm="HIST_GRADIENT_BOOSTING", hyperparameters=hyperparameters)
        from sklearn.ensemble import HistGradientBoostingClassifier

        max_iter = int(self.hyperparameters.get("max_iter", 100))
        max_depth = self.hyperparameters.get("max_depth", 5)
        learning_rate = float(self.hyperparameters.get("learning_rate", 0.05))

        self.model = HistGradientBoostingClassifier(
            max_iter=max_iter,
            max_depth=max_depth,
            learning_rate=learning_rate,
            random_state=42
        )

    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: Optional[List[str]] = None) -> "HistGradientBoostingModel":
        self.model.fit(X, y)
        self.is_fitted = True
        self.feature_names = feature_names or []
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict_proba(X)


class XGBoostModel(BaseMLModel):
    """Extreme Gradient Boosting (XGBoost) Classifier."""

    def __init__(self, hyperparameters: Optional[Dict[str, Any]] = None):
        super().__init__(name="XGBoost Classifier", algorithm="XGBOOST", hyperparameters=hyperparameters)
        import xgboost as xgb

        n_estimators = int(self.hyperparameters.get("n_estimators", 100))
        max_depth = int(self.hyperparameters.get("max_depth", 4))
        learning_rate = float(self.hyperparameters.get("learning_rate", 0.05))
        subsample = float(self.hyperparameters.get("subsample", 0.8))

        self.model = xgb.XGBClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            subsample=subsample,
            eval_metric="logloss",
            random_state=42,
            n_jobs=-1
        )

    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: Optional[List[str]] = None) -> "XGBoostModel":
        self.model.fit(X, y)
        self.is_fitted = True
        self.feature_names = feature_names or []
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict_proba(X)

    def get_feature_importance(self) -> Dict[str, float]:
        if not self.is_fitted or not self.feature_names:
            return {}
        importances = self.model.feature_importances_
        return {name: float(imp) for name, imp in zip(self.feature_names, importances)}


def get_model_by_algorithm(algorithm: str, hyperparameters: Optional[Dict[str, Any]] = None) -> BaseMLModel:
    """Factory function to instantiate models by algorithm identifier."""
    algo = algorithm.upper()
    if algo == "BASELINE_FREQUENCY":
        return BaselineFrequencyModel(hyperparameters)
    elif algo == "NULL_INDEPENDENCE":
        return IndependenceNullModel(hyperparameters=hyperparameters)
    elif algo == "LOGISTIC_REGRESSION":
        return LogisticRegressionModel(hyperparameters)
    elif algo == "RANDOM_FOREST":
        return RandomForestModel(hyperparameters)
    elif algo in ("HIST_GRADIENT_BOOSTING", "GRADIENT_BOOSTING"):
        return HistGradientBoostingModel(hyperparameters)
    elif algo == "XGBOOST":
        return XGBoostModel(hyperparameters)
    else:
        raise ValueError(f"Unsupported ML algorithm: {algorithm}. Supported: BASELINE_FREQUENCY, NULL_INDEPENDENCE, LOGISTIC_REGRESSION, RANDOM_FOREST, HIST_GRADIENT_BOOSTING, XGBOOST")

