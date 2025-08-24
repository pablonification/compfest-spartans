from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from .opencv_service import MeasurementResult
from .roboflow_service import Prediction


@dataclass
class PayoutConfig:
    size_weights_g: Dict[str, float]
    brand_overrides_g: Dict[str, float]
    pet_price_idr_per_kg: int
    coefficients_brand_unknown: Dict[str, float]
    confidence_bins: Tuple[Tuple[float, float], ...]
    cleanliness: Dict[str, float]
    cap_label: Dict[str, float]
    rounding: str = "round"  # one of: round|ceil|floor


DEFAULT_PAYOUT_CONFIG = PayoutConfig(
    size_weights_g={
        "330ml": 10.5,
        "600ml": 16.0,
        "750ml": 22.0,
        "1500ml": 30.0,
    },
    brand_overrides_g={
        # Example overrides; can be extended via admin later
        # "AQUA_600": 16.0,
        # "AQUA_1500": 30.0,
    },
    pet_price_idr_per_kg=3700,
    coefficients_brand_unknown={
        "330ml": 0.93,
        "600ml": 0.95,
        "750ml": 0.96,
        "1500ml": 0.97,
    },
    # (min_confidence_in_0_to_1, k)
    confidence_bins=(
        (0.85, 1.00),
        (0.70, 0.97),
        (0.50, 0.93),
    ),
    cleanliness={
        "clean_dry": 1.00,
        "slightly_dirty": 0.95,
        "dirty": 0.85,
    },
    cap_label={
        "separated": 1.02,
        "mixed": 1.00,
        "contaminated": 0.95,
    },
    rounding="round",
)


def _normalize_brand(brand: Optional[str]) -> Optional[str]:
    if not brand:
        return None
    normalized = "".join(ch for ch in brand.upper() if ch.isalnum())
    return normalized or None


def _select_size_key(volume_ml: float) -> str:
    """Pick the closest size key from the configured choices based on volume.

    This chooses among 330, 600, 750, 1500 ml by absolute difference.
    """
    candidates = {
        "330ml": 330.0,
        "600ml": 600.0,
        "750ml": 750.0,
        "1500ml": 1500.0,
    }
    best_key = min(candidates.keys(), key=lambda k: abs(volume_ml - candidates[k]))
    return best_key


def _confidence_k(conf_0_to_1: float, bins: Tuple[Tuple[float, float], ...]) -> float | float("nan"):
    # bins sorted by min descending
    for min_thr, k in sorted(bins, key=lambda x: x[0], reverse=True):
        if conf_0_to_1 >= min_thr:
            return k
    return float("nan")


@dataclass
class PayoutResult:
    payout_rp: Optional[int]
    k_brand: float
    k_conf: Optional[float]
    k_clean: float
    k_cap: float
    size_key: str
    weight_g_used: float
    price_per_kg: int
    brand_key_used: Optional[str]
    base_rp: float


def compute_payout(
    measurement: MeasurementResult,
    predictions: list[Prediction],
    *,
    cfg: PayoutConfig = DEFAULT_PAYOUT_CONFIG,
    cleanliness_key: str = "clean_dry",
    cap_label_key: str = "mixed",
) -> PayoutResult:
    """Compute payout in Rupiah based on measurement and predictions.

    Returns PayoutResult where payout_rp is None when measurement confidence is below
    the reject threshold (< 0.50 as per spec).
    """
    # Determine size key by closest volume
    size_key = _select_size_key(measurement.volume_ml)

    # Determine size confidence for K_conf. Prefer measurement.confidence_percent
    # if available; otherwise derive a conservative confidence from volume closeness.
    conf_percent = measurement.confidence_percent
    if conf_percent is None:
        target_volumes = {
            "330ml": 330.0,
            "600ml": 600.0,
            "750ml": 750.0,
            "1500ml": 1500.0,
        }
        target = target_volumes[size_key]
        diff_pct = abs(measurement.volume_ml - target) / target  # in 0..inf
        # Map diff to confidence: 1 - diff, clamped [0,1]
        conf_0_to_1 = max(0.0, min(1.0, 1.0 - diff_pct))
    else:
        conf_0_to_1 = max(0.0, min(1.0, conf_percent / 100.0))

    k_conf = _confidence_k(conf_0_to_1, cfg.confidence_bins)
    if not math.isfinite(k_conf):
        # Reject per spec; still return context for transparency
        weight_g_reject = cfg.size_weights_g[size_key]
        base_reject = (weight_g_reject / 1000.0) * cfg.pet_price_idr_per_kg
        return PayoutResult(
            payout_rp=None,
            k_brand=1.0,
            k_conf=None,
            k_clean=cfg.cleanliness.get(cleanliness_key, 1.0),
            k_cap=cfg.cap_label.get(cap_label_key, 1.0),
            size_key=size_key,
            weight_g_used=weight_g_reject,
            price_per_kg=cfg.pet_price_idr_per_kg,
            brand_key_used=None,
            base_rp=base_reject,
        )

    # Brand handling
    top_brand: Optional[str] = None
    if predictions:
        # choose highest confidence by Prediction.confidence
        top = max(predictions, key=lambda p: getattr(p, "confidence", 0.0))
        top_brand = top.brand
    brand_key = _normalize_brand(top_brand)

    # Determine weight (brand override -> size weight)
    weight_g = cfg.size_weights_g[size_key]
    if brand_key is not None:
        candidate_key = f"{brand_key}_{size_key.replace('ml', '')}"
        override = cfg.brand_overrides_g.get(candidate_key)
        if override is not None:
            weight_g = override

    weight_kg = weight_g / 1000.0

    # K_brand
    if brand_key is None:
        k_brand = cfg.coefficients_brand_unknown[size_key]
    else:
        k_brand = 1.0

    k_clean = cfg.cleanliness.get(cleanliness_key, 1.0)
    k_cap = cfg.cap_label.get(cap_label_key, 1.0)

    base = weight_kg * cfg.pet_price_idr_per_kg
    payout = base * k_brand * k_conf * k_clean * k_cap

    if cfg.rounding == "ceil":
        payout_int = math.ceil(payout)
    elif cfg.rounding == "floor":
        payout_int = math.floor(payout)
    else:
        payout_int = round(payout)

    return PayoutResult(
        payout_rp=int(payout_int),
        k_brand=k_brand,
        k_conf=k_conf,
        k_clean=k_clean,
        k_cap=k_cap,
        size_key=size_key,
        weight_g_used=weight_g,
        price_per_kg=cfg.pet_price_idr_per_kg,
        brand_key_used=brand_key,
        base_rp=base,
    )


