def clamped_ratio(value: float, target: float) -> float:
    """value/target, clamped to [0, 1]. A non-positive target is treated as already saturated."""
    if target <= 0:
        return 1.0
    return min(value / target, 1.0)
