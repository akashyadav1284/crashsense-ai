"""Analytics API Router."""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query, HTTPException, status
from backend.app.analytics.schemas.analytics import (
    DescriptiveStatsResponse,
    DistributionResponse,
    RollingStatsResponse,
    AutocorrelationResponse,
    OutlierResponse,
    DriftComparisonResponse,
    CrossPlatformComparisonResponse,
)
from backend.app.analytics.services.analytics_service import analytics_service

router = APIRouter(prefix="/analytics", tags=["Statistical Research & Multiplier Analytics"])


@router.get("/summary", response_model=Dict[str, Any])
async def get_analytics_summary(
    dataset_id: str = Query(default="ds-1xbet-aviator-standard")
) -> Dict[str, Any]:
    """High-level summary combining descriptive, distribution, and serial independence status."""
    desc = await analytics_service.get_descriptive_stats(dataset_id)
    dist = await analytics_service.get_distribution(dataset_id)
    acf = await analytics_service.get_autocorrelation(dataset_id, max_lags=5)
    return {
        "dataset_id": dataset_id,
        "sample_size": desc.sample_size,
        "mean": desc.mean,
        "median": desc.median,
        "std_dev": desc.std_dev,
        "iqr": desc.iqr,
        "categories_count": len(dist.categories),
        "serial_independence_null_rejected": acf.ljung_box.reject_null if acf.ljung_box else False,
        "warning": desc.warning
    }


@router.get("/descriptive", response_model=DescriptiveStatsResponse)
async def get_descriptive(
    dataset_id: str = Query(default="ds-1xbet-aviator-standard")
) -> DescriptiveStatsResponse:
    """Compute comprehensive descriptive sample statistics."""
    return await analytics_service.get_descriptive_stats(dataset_id)


@router.get("/distribution", response_model=DistributionResponse)
async def get_distribution(
    dataset_id: str = Query(default="ds-1xbet-aviator-standard")
) -> DistributionResponse:
    """Compute empirical frequency distribution with Wilson confidence intervals."""
    return await analytics_service.get_distribution(dataset_id)


@router.get("/frequency", response_model=DistributionResponse)
async def get_frequency(
    dataset_id: str = Query(default="ds-1xbet-aviator-standard")
) -> DistributionResponse:
    """Alias for multiplier frequency analysis."""
    return await analytics_service.get_distribution(dataset_id)


@router.get("/percentiles", response_model=Dict[str, Any])
async def get_percentiles(
    dataset_id: str = Query(default="ds-1xbet-aviator-standard")
) -> Dict[str, Any]:
    """Retrieve P1 through P99 sample percentiles."""
    desc = await analytics_service.get_descriptive_stats(dataset_id)
    return {
        "dataset_id": dataset_id,
        "sample_size": desc.sample_size,
        "percentiles": desc.percentiles
    }


@router.get("/rolling", response_model=RollingStatsResponse)
async def get_rolling_stats(
    dataset_id: str = Query(default="ds-1xbet-aviator-standard"),
    window: int = Query(50, ge=5, le=1000)
) -> RollingStatsResponse:
    """Compute sequential rolling moments (mean, median, standard deviation)."""
    return await analytics_service.get_rolling_stats(dataset_id, window_size=window)


@router.get("/autocorrelation", response_model=AutocorrelationResponse)
async def get_autocorrelation(
    dataset_id: str = Query(default="ds-1xbet-aviator-standard"),
    max_lags: int = Query(15, ge=1, le=50)
) -> AutocorrelationResponse:
    """Compute Autocorrelation Function (ACF) and Ljung-Box independence test."""
    return await analytics_service.get_autocorrelation(dataset_id, max_lags=max_lags)


@router.get("/independence", response_model=AutocorrelationResponse)
async def get_independence_diagnostics(
    dataset_id: str = Query(default="ds-1xbet-aviator-standard")
) -> AutocorrelationResponse:
    """Test sequential independence against theoretical random noise."""
    return await analytics_service.get_autocorrelation(dataset_id)


@router.get("/outliers", response_model=OutlierResponse)
async def get_outliers(
    dataset_id: str = Query(default="ds-1xbet-aviator-standard")
) -> OutlierResponse:
    """Identify empirical outliers using Tukey 1.5x IQR fences."""
    return await analytics_service.get_outliers(dataset_id)


@router.get("/drift", response_model=DriftComparisonResponse)
async def get_drift(
    dataset_id: str = Query(default="ds-1xbet-aviator-standard"),
    baseline_window: int = Query(100, ge=10, le=500),
    comparison_window: int = Query(100, ge=10, le=500)
) -> DriftComparisonResponse:
    """Evaluate distribution drift using Two-Sample Kolmogorov-Smirnov test and PSI."""
    return await analytics_service.get_drift(
        dataset_id,
        baseline_window=baseline_window,
        comparison_window=comparison_window
    )


@router.get("/confidence", response_model=DistributionResponse)
async def get_confidence_intervals(
    dataset_id: str = Query(default="ds-1xbet-aviator-standard")
) -> DistributionResponse:
    """Calculate 95% Wilson score confidence bounds for empirical category frequencies."""
    return await analytics_service.get_distribution(dataset_id)


@router.get("/compare", response_model=CrossPlatformComparisonResponse)
async def compare_platforms(
    dataset_a: str = Query(default="ds-1xbet-aviator-standard"),
    dataset_b: str = Query(default="ds-bcgame-crash-standard")
) -> CrossPlatformComparisonResponse:
    """Compare empirical moments and run two-sample KS test across operator partitions."""
    return await analytics_service.compare_platforms(dataset_a, dataset_b)

