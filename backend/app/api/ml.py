"""
API Endpoints for Phase 6 Machine Learning Research Laboratory.
Handles model training experiments, model registry queries, walk-forward validation results,
calibration curves, model comparisons, and strictly guarded research inference.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, status

from backend.app.ml.schemas.experiment import (
    ModelMetadata,
    ModelLifecycleStatus,
    ExperimentRequest,
    ExperimentRecord,
    ResearchInferenceRequest,
    ResearchInferenceResponse,
)
from backend.app.ml.services.ml_service import MLService
from backend.app.ml.registry.model_registry import ModelRegistry

router = APIRouter(prefix="/ml", tags=["Machine Learning Research Lab"])


@router.get("/models", response_model=List[ModelMetadata])
async def list_models(
    platform_id: Optional[str] = Query(None, description="Filter by platform ID"),
    game_provider: Optional[str] = Query(None, description="Filter by game provider"),
    status: Optional[ModelLifecycleStatus] = Query(None, description="Filter by lifecycle status"),
):
    """List all registered ML models with metadata, parameters, and edge validation flags."""
    registry = ModelRegistry.get_instance()
    return registry.list_models(platform_id=platform_id, game_provider=game_provider, status=status)


@router.get("/models/{model_id}", response_model=ModelMetadata)
async def get_model(model_id: str):
    """Retrieve detailed metadata and evaluation scores for a specific registered model."""
    registry = ModelRegistry.get_instance()
    meta = registry.get_model_metadata(model_id)
    if not meta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Model '{model_id}' not found.")
    return meta


@router.get("/experiments", response_model=List[ExperimentRecord])
async def list_experiments():
    """List all executed ML training research experiments."""
    registry = ModelRegistry.get_instance()
    return registry.list_experiments()


@router.get("/experiments/{experiment_id}", response_model=ExperimentRecord)
async def get_experiment(experiment_id: str):
    """Retrieve full experiment details including walk-forward folds and calibration curves."""
    registry = ModelRegistry.get_instance()
    exp = registry.get_experiment(experiment_id)
    if not exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Experiment '{experiment_id}' not found.")
    return exp


@router.post("/train", response_model=ExperimentRecord, status_code=status.HTTP_201_CREATED)
async def train_model(request: ExperimentRequest):
    """
    Train a candidate ML model on actual historical crash data using expanding-window walk-forward validation.
    Strictly verifies predictive performance against Null Independence Baselines.
    """
    ml_service = MLService.get_instance()
    try:
        experiment = await ml_service.run_training_experiment(request)
        return experiment
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Experiment training failed: {str(e)}")


@router.get("/compare")
async def compare_models(
    model_ids: List[str] = Query(..., description="List of model IDs to compare"),
):
    """Compare multiple models side-by-side against baseline metrics (Brier, LogLoss, AUC, ECE)."""
    registry = ModelRegistry.get_instance()
    comparison = []

    for m_id in model_ids:
        meta = registry.get_model_metadata(m_id)
        if meta:
            comparison.append({
                "model_id": meta.model_id,
                "name": meta.name,
                "algorithm": meta.algorithm,
                "target_threshold": meta.target_threshold,
                "training_sample_count": meta.training_sample_count,
                "accuracy": meta.evaluation_metrics.accuracy,
                "balanced_accuracy": meta.evaluation_metrics.balanced_accuracy,
                "brier_score": meta.evaluation_metrics.brier_score,
                "log_loss": meta.evaluation_metrics.log_loss,
                "roc_auc": meta.evaluation_metrics.roc_auc,
                "ece": meta.evaluation_metrics.expected_calibration_error,
                "baseline_brier": meta.baseline_metrics.brier_score if meta.baseline_metrics else None,
                "baseline_log_loss": meta.baseline_metrics.log_loss if meta.baseline_metrics else None,
                "has_validated_edge": meta.has_validated_edge,
                "status": meta.status.value,
            })

    if not comparison:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No valid models found matching the provided IDs.")

    return {"comparison_count": len(comparison), "models": comparison}


@router.post("/inference", response_model=ResearchInferenceResponse)
async def run_inference(request: ResearchInferenceRequest):
    """
    Run research inference on the latest historical sequence using a trained model.
    Includes mandatory scientific disclaimers regarding memoryless PRNG independence.
    """
    ml_service = MLService.get_instance()
    try:
        response = ml_service.run_research_inference(request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Inference computation error: {str(e)}")

