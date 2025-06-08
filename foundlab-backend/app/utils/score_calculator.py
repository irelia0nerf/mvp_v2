from math import exp
from typing import Any, Dict, List, Tuple

from app.models.score import FlagWithValue


class ScoreCalculator:
    """
    Calculates the P(x) score based on flags and metadata.
    This implementation uses a weighted average of active flag values for P(x).
    """

    def __init__(self, version: str = "1.0.0"):
        self.version = version
        self.neutral_probability_score = 0.5  # A neutral starting point for P(x)

    def _normalize_flag_value(self, value: Any) -> float:
        """
        Normalizes various flag value types to a float between 0 and 1.
        - `bool`: True -> 1.0, False -> 0.0
        - `int`/`float`: Clamped between 0.0 and 1.0 if outside this range, otherwise used directly.
        - Other types: Currently defaults to 0.0, could be extended for categorical mapping if needed.
        """
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        elif isinstance(value, (int, float)):
            return max(0.0, min(1.0, float(value)))
        return 0.0  # Default for unhandled types or non-contributing values

    def calculate_p_x(self, active_flags: List[FlagWithValue], metadata: Dict[str, Any]) -> Tuple[float, float]:
        """
        Calculates the raw score and the probability score P(x).
        The formula for P(x) used here is a weighted average:
        P(x) = Σ (normalized_flag_value_i * effective_weight_i) / Σ (effective_weight_i)

        Args:
            active_flags: A list of `FlagWithValue` instances where `is_active=True`.
            metadata: Additional metadata for context. Not directly factored into this P(x) calculation.

        Returns:
            A tuple (raw_score, probability_score)
        """
        if not active_flags:
            return 0.0, self.neutral_probability_score

        sum_of_weighted_values: float = 0.0
        sum_of_weights: float = 0.0

        for flag in active_flags:
            normalized_value = self._normalize_flag_value(flag.value)
            effective_weight = max(0.0, flag.weight)

            sum_of_weighted_values += normalized_value * effective_weight
            sum_of_weights += effective_weight

        if sum_of_weights == 0:
            return 0.0, self.neutral_probability_score

        raw_score = sum_of_weighted_values
        probability_score = raw_score / sum_of_weights
        probability_score = max(0.0, min(1.0, probability_score))

        return raw_score, probability_score
