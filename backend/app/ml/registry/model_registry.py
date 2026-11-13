"""
Model Registry for CRASHSENSE AI Machine Learning Research Laboratory.
Manages model metadata, lifecycle states, persistence, and version tracking.
"""

import os
from typing import Dict, List, Optional
from datetime import datetime, timezone
from backend.app.ml.schemas.experiment import (
    ModelMetadata,
    ModelLifecycleStatus,
    ExperimentRecord,
)
from backend.app.ml.models.base_model import BaseMLModel


class ModelRegistry:
    """In-memory and filesystem registry for research models and experiment records."""

    _instance: Optional["ModelRegistry"] = None

    def __init__(self, storage_dir: str = "backend/data/models"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        self.models_meta: Dict[str, ModelMetadata] = {}
        self.loaded_models: Dict[str, BaseMLModel] = {}
        self.experiments: Dict[str, ExperimentRecord] = {}

    @classmethod
    def get_instance(cls) -> "ModelRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_model(self, meta: ModelMetadata, model_obj: Optional[BaseMLModel] = None) -> ModelMetadata:
        """Register a new or updated model entry."""
        meta.updated_at = datetime.now(timezone.utc)
        self.models_meta[meta.model_id] = meta

        if model_obj is not None:
            self.loaded_models[meta.model_id] = model_obj
            artifact_path = os.path.join(self.storage_dir, f"{meta.model_id}.joblib")
            model_obj.save(artifact_path)
            meta.model_file_path = artifact_path

        return meta

    def get_model_metadata(self, model_id: str) -> Optional[ModelMetadata]:
        return self.models_meta.get(model_id)

    def get_model(self, model_id: str) -> Optional[BaseMLModel]:
        if model_id in self.loaded_models:
            return self.loaded_models[model_id]

        meta = self.models_meta.get(model_id)
        if meta and meta.model_file_path and os.path.exists(meta.model_file_path):
            try:
                loaded = BaseMLModel.load(meta.model_file_path)
                self.loaded_models[model_id] = loaded
                return loaded
            except Exception:
                return None
        return None

    def list_models(
        self,
        platform_id: Optional[str] = None,
        game_provider: Optional[str] = None,
        status: Optional[ModelLifecycleStatus] = None
    ) -> List[ModelMetadata]:
        results = list(self.models_meta.values())
        if platform_id:
            results = [m for m in results if m.platform_id == platform_id]
        if game_provider:
            results = [m for m in results if m.game_provider == game_provider]
        if status:
            results = [m for m in results if m.status == status]
        return sorted(results, key=lambda x: x.created_at, reverse=True)

    def update_status(self, model_id: str, new_status: ModelLifecycleStatus) -> Optional[ModelMetadata]:
        if model_id in self.models_meta:
            self.models_meta[model_id].status = new_status
            self.models_meta[model_id].updated_at = datetime.now(timezone.utc)
            return self.models_meta[model_id]
        return None

    def record_experiment(self, experiment: ExperimentRecord) -> ExperimentRecord:
        self.experiments[experiment.experiment_id] = experiment
        return experiment

    def get_experiment(self, experiment_id: str) -> Optional[ExperimentRecord]:
        return self.experiments.get(experiment_id)

    def list_experiments(self) -> List[ExperimentRecord]:
        return sorted(list(self.experiments.values()), key=lambda x: x.created_at, reverse=True)

