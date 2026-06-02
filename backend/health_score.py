"""
Health score backend module for NutriScan - Food Calorie Detector.

This module analyzes nutrition values, calculates a simple health score, and
returns a category with practical recommendations for frontend display.

It does not contain frontend code, model training code, or prediction logic.
"""

import math


REQUIRED_NUTRITION_FIELDS = [
    "calories",
    "protein",
    "carbs",
    "fat",
    "sugar",
    "fiber",
]


def validate_nutrition_data(nutrition_data):
    """
    Validate nutrition data before calculating a health score.

    Args:
        nutrition_data: Dictionary containing nutrition values.

    Raises:
        ValueError: If input is empty, missing values, invalid, or negative.
    """
    if not nutrition_data:
        raise ValueError("Nutrition data is required.")

    if not isinstance(nutrition_data, dict):
        raise ValueError("Nutrition data must be provided as a dictionary.")

    for field in REQUIRED_NUTRITION_FIELDS:
        if field not in nutrition_data:
            raise ValueError(f"Missing nutrition value: {field}")

        try:
            value = float(nutrition_data[field])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid nutrition value for {field}.") from exc

        if not math.isfinite(value):
            raise ValueError(f"Nutrition value for {field} must be a valid number.")

        if value < 0:
            raise ValueError(f"Nutrition value for {field} cannot be negative.")


def calculate_score(nutrition_data):
    """
    Calculate a health score from 0 to 100.

    Scoring idea:
        - Protein and fiber increase the score.
        - Excess calories, fat, carbs, and sugar reduce the score.

    Args:
        nutrition_data: Dictionary containing calories, protein, carbs, fat,
            sugar, and fiber.

    Returns:
        Integer health score between 0 and 100.
    """
    try:
        validate_nutrition_data(nutrition_data)

        calories = float(nutrition_data["calories"])
        protein = float(nutrition_data["protein"])
        carbs = float(nutrition_data["carbs"])
        fat = float(nutrition_data["fat"])
        sugar = float(nutrition_data["sugar"])
        fiber = float(nutrition_data["fiber"])

        score = 70

        # Positive nutrition signals.
        if protein >= 20:
            score += 15
        elif protein >= 10:
            score += 10
        elif protein >= 5:
            score += 5

        if fiber >= 8:
            score += 12
        elif fiber >= 4:
            score += 8
        elif fiber >= 2:
            score += 4

        # Nutrition values to consume carefully.
        if calories > 700:
            score -= 25
        elif calories > 500:
            score -= 18
        elif calories > 350:
            score -= 10

        if fat > 30:
            score -= 18
        elif fat > 20:
            score -= 12
        elif fat > 12:
            score -= 6

        if carbs > 80:
            score -= 12
        elif carbs > 55:
            score -= 8
        elif carbs > 35:
            score -= 4

        if sugar > 30:
            score -= 25
        elif sugar > 18:
            score -= 16
        elif sugar > 10:
            score -= 8

        return max(0, min(100, round(score)))

    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Health score calculation failed: {exc}") from exc


def classify_food(score, nutrition_data=None):
    """
    Classify food based on health score and nutrition values.

    Args:
        score: Calculated health score.
        nutrition_data: Optional nutrition dictionary for special categories.

    Returns:
        Health category as a string.
    """
    try:
        score = int(score)

        if nutrition_data and float(nutrition_data.get("calories", 0)) > 700:
            return "High Calorie"

        if nutrition_data:
            carbs = float(nutrition_data.get("carbs", 0))
            fiber = float(nutrition_data.get("fiber", 0))
            if score < 75 and carbs > 45 and fiber < 2:
                return "Moderate"

        if score >= 85:
            return "Very Healthy"
        if score >= 70:
            return "Healthy"
        if score >= 50:
            return "Moderate"

        return "Unhealthy"

    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid score or nutrition data for classification.") from exc


def generate_recommendation(nutrition_data, score):
    """
    Generate simple health recommendations from nutrition values.

    Args:
        nutrition_data: Dictionary containing nutrition values.
        score: Calculated health score.

    Returns:
        Recommendation text.
    """
    try:
        validate_nutrition_data(nutrition_data)

        calories = float(nutrition_data["calories"])
        protein = float(nutrition_data["protein"])
        fat = float(nutrition_data["fat"])
        sugar = float(nutrition_data["sugar"])
        fiber = float(nutrition_data["fiber"])

        recommendations = []

        if protein >= 10:
            recommendations.append("High in protein.")
        elif protein < 5:
            recommendations.append("Low in protein.")

        if fiber >= 4:
            recommendations.append("Good source of fiber.")
        elif fiber < 2:
            recommendations.append("Low in fiber.")

        if sugar > 18:
            recommendations.append("Contains excess sugar.")
        elif sugar > 10:
            recommendations.append("Slightly high in sugar.")

        if fat > 20:
            recommendations.append("High in fat, consume in moderation.")
        elif fat > 12:
            recommendations.append("Slightly high in fat.")

        if calories > 700:
            recommendations.append("Very high in calories.")
        elif calories > 500:
            recommendations.append("High in calories.")

        if not recommendations:
            if score >= 70:
                recommendations.append("Good for a balanced diet.")
            else:
                recommendations.append("Consume in moderation.")

        return " ".join(recommendations)

    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Recommendation generation failed: {exc}") from exc


def calculate_health_score(nutrition_data):
    """
    Main function to calculate health score, category, and recommendation.

    Args:
        nutrition_data: Dictionary with calories, protein, carbs, fat, sugar,
            and fiber.

    Returns:
        Structured health score result.

    Example:
        {
            "health_score": 78,
            "category": "Healthy",
            "recommendation": "High in protein. Good source of fiber."
        }
    """
    try:
        validate_nutrition_data(nutrition_data)

        score = calculate_score(nutrition_data)
        category = classify_food(score, nutrition_data)
        recommendation = generate_recommendation(nutrition_data, score)

        return {
            "health_score": score,
            "category": category,
            "recommendation": recommendation,
        }

    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Health score processing failed: {exc}") from exc
