"""
services/data_fusion.py
-----------------------
Multi-provider data fusion engine (Module 1.2).

Performs:
  - Cross-provider alignment & normalization
  - Value comparison and conflict detection (temperature, rain, wind, pressure)
  - Field-level missing data imputation (secondary provider fills gaps)
  - Weighted consensus or priority-based value fusion
  - Conflict manifest generation for downstream quality tracking
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from app.schemas.intelligence import ConflictingField, FusionSummary
from app.schemas.unified_weather import CURRENT_WEATHER_OPTIONAL_FIELDS, CurrentWeather, ProviderInfo


# Thresholds above which a numerical discrepancy is considered a conflict
_CONFLICT_THRESHOLDS = {
    "temperature": 2.5,   # °C difference
    "humidity": 15.0,     # % difference
    "rainfall": 5.0,      # mm difference
    "wind_speed": 15.0,   # km/h difference
    "pressure": 4.0,      # hPa difference
    "visibility": 3.0,    # km difference
}

# Default provider reliability weights (0.0 to 1.0)
DEFAULT_PROVIDER_WEIGHTS: Dict[str, float] = {
    "open_meteo": 1.0,
    "imd": 1.0,
    "tomorrow_io": 0.9,
    "gfs": 0.85,
    "mock_secondary": 0.8,
}


class DataFusionEngine:
    """
    Stateless multi-provider weather data fusion service.
    """

    def __init__(self, provider_weights: Optional[Dict[str, float]] = None) -> None:
        self.weights = provider_weights or DEFAULT_PROVIDER_WEIGHTS

    def fuse_current(
        self,
        observations: List[CurrentWeather],
        strategy: str = "weighted_consensus",
    ) -> Tuple[CurrentWeather, List[ConflictingField], FusionSummary]:
        """
        Fuse multiple CurrentWeather observations into a single consensus CurrentWeather.
        """
        if not observations:
            raise ValueError("Cannot fuse empty observation list.")

        if len(observations) == 1:
            primary = observations[0]
            summary = FusionSummary(
                strategy="single_provider",
                providers_evaluated=[primary.provider.name],
                primary_provider=primary.provider.name,
                fields_imputed=[],
                conflicts_detected=0,
            )
            return primary, [], summary

        primary = observations[0]
        conflicts: List[ConflictingField] = []
        imputed_fields: List[str] = []

        # Prepare field dictionary based on primary
        fused_data = primary.model_dump()
        all_provider_names = [obs.provider.name for obs in observations]

        # Scan each meteorological field
        for field in CURRENT_WEATHER_OPTIONAL_FIELDS:
            vals: Dict[str, float] = {}
            for obs in observations:
                v = getattr(obs, field, None)
                if v is not None and isinstance(v, (int, float)) and not isinstance(v, bool):
                    vals[obs.provider.name] = float(v)

            if not vals:
                continue

            # If primary was None, impute from first available secondary provider
            if getattr(primary, field, None) is None:
                donor_provider = list(vals.keys())[0]
                fused_data[field] = vals[donor_provider]
                imputed_fields.append(field)
                continue

            # If 2+ providers supply this numeric field, check for conflict
            if len(vals) >= 2 and field in _CONFLICT_THRESHOLDS:
                threshold = _CONFLICT_THRESHOLDS[field]
                val_list = list(vals.values())
                delta = abs(max(val_list) - min(val_list))

                if delta > threshold:
                    # Record conflict
                    conflicts.append(
                        ConflictingField(
                            field_name=field,
                            provider_values=vals,
                            discrepancy=round(delta, 2),
                            resolution=(
                                "weighted_average" if strategy == "weighted_consensus" else "primary_selection"
                            ),
                        )
                    )

                # Fuse value
                if strategy == "weighted_consensus":
                    total_w = sum(self.weights.get(name, 0.5) for name in vals)
                    if total_w > 0:
                        weighted_val = sum(
                            vals[name] * self.weights.get(name, 0.5) for name in vals
                        ) / total_w
                        fused_data[field] = round(weighted_val, 2)

        # Create fused ProviderInfo
        fused_provider = ProviderInfo(
            name="fused_multi_provider",
            display_name=f"Fused ({', '.join(all_provider_names)})",
            model="Multi-Provider Consensus",
        )
        fused_data["provider"] = fused_provider

        # Reset available_fields so model_post_init recomputes correctly
        fused_data["available_fields"] = []
        fused_data["missing_fields"] = []

        fused_weather = CurrentWeather(**fused_data)

        summary = FusionSummary(
            strategy=strategy,
            providers_evaluated=all_provider_names,
            primary_provider=primary.provider.name,
            fields_imputed=imputed_fields,
            conflicts_detected=len(conflicts),
        )

        return fused_weather, conflicts, summary
