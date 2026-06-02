"""
Recommendation backend module for NutriScan - Food Calorie Detector.

This module creates rule-based food recommendations from nutrition data and
health score data. It is designed to be easy to replace or extend later with a
personalized recommendation engine.

It does not contain frontend code, model training code, or prediction logic.
"""

import random


REQUIRED_NUTRITION_FIELDS = [
    "calories",
    "protein",
    "fat",
    "sugar",
    "fiber",
]

DEFAULT_ALTERNATIVES = [
    "Veg Salad",
    "Fruit Bowl",
    "Vegetable Soup",
    "Sprout Bowl",
    "Brown Bread Sandwich",
]

FOOD_ALTERNATIVES = {
    "adhirasam": ["Fruit Bowl", "Plain Curd", "Nuts And Seeds"],
    "bandar laddu": ["Fruit Bowl", "Plain Curd", "Nuts And Seeds"],
    "basundi": ["Fruit Bowl", "Plain Curd", "Coconut Water"],
    "bhatura": ["Brown Bread Sandwich", "Vegetable Soup", "Veg Salad"],
    "biryani": ["Veg Salad", "Cucumber Raita", "Vegetable Soup"],
    "boondi": ["Veg Salad", "Vegetable Soup", "Sprout Bowl"],
    "cham cham": ["Fruit Bowl", "Plain Curd", "Coconut Water"],
    "chhena kheeri": ["Fruit Bowl", "Plain Curd", "Coconut Water"],
    "chicken biryani": ["Veg Salad", "Cucumber Raita", "Grilled Chicken"],
    "chicken razala": ["Grilled Chicken", "Veg Salad", "Vegetable Soup"],
    "chicken tikka": ["Veg Salad", "Vegetable Soup", "Cucumber Raita"],
    "chicken tikka masala": ["Grilled Chicken", "Veg Salad", "Vegetable Soup"],
    "daal baati churma": ["Veg Salad", "Plain Curd", "Vegetable Soup"],
    "daal puri": ["Veg Salad", "Vegetable Soup", "Sprout Bowl"],
    "dharwad pedha": ["Fruit Bowl", "Plain Curd", "Nuts And Seeds"],
    "doodhpak": ["Fruit Bowl", "Plain Curd", "Coconut Water"],
    "double ka meetha": ["Fruit Bowl", "Plain Curd", "Coconut Water"],
    "dum aloo": ["Veg Salad", "Vegetable Soup", "Sprout Bowl"],
    "egg biryani": ["Veg Salad", "Cucumber Raita", "Sprout Bowl"],
    "gajar ka halwa": ["Fruit Bowl", "Plain Curd", "Nuts And Seeds"],
    "ghevar": ["Fruit Bowl", "Plain Curd", "Coconut Water"],
    "gulab jamun": ["Fruit Bowl", "Plain Curd", "Coconut Water"],
    "imarti": ["Fruit Bowl", "Plain Curd", "Coconut Water"],
    "jalebi": ["Fruit Bowl", "Plain Curd", "Coconut Water"],
    "kachori": ["Veg Salad", "Vegetable Soup", "Sprout Bowl"],
    "kadhi pakoda": ["Veg Salad", "Vegetable Soup", "Sprout Bowl"],
    "kakinada khaja": ["Fruit Bowl", "Plain Curd", "Coconut Water"],
    "kalakand": ["Fruit Bowl", "Plain Curd", "Nuts And Seeds"],
    "kofta": ["Veg Salad", "Vegetable Soup", "Sprout Bowl"],
    "ledikeni": ["Fruit Bowl", "Plain Curd", "Coconut Water"],
    "litti chokha": ["Veg Salad", "Plain Curd", "Vegetable Soup"],
    "lyangcha": ["Fruit Bowl", "Plain Curd", "Coconut Water"],
    "makki di roti sarson da saag": ["Veg Salad", "Plain Curd", "Vegetable Soup"],
    "malapua": ["Fruit Bowl", "Plain Curd", "Coconut Water"],
    "misti doi": ["Fruit Bowl", "Plain Curd", "Coconut Water"],
    "mutton biryani": ["Veg Salad", "Cucumber Raita", "Vegetable Soup"],
    "mysore pak": ["Fruit Bowl", "Plain Curd", "Nuts And Seeds"],
    "navrattan korma": ["Veg Salad", "Vegetable Soup", "Sprout Bowl"],
    "poornalu": ["Fruit Bowl", "Plain Curd", "Nuts And Seeds"],
    "pootharekulu": ["Fruit Bowl", "Plain Curd", "Nuts And Seeds"],
    "qubani ka meetha": ["Fruit Bowl", "Plain Curd", "Coconut Water"],
    "ras malai": ["Fruit Bowl", "Plain Curd", "Coconut Water"],
    "rasgulla": ["Fruit Bowl", "Plain Curd", "Coconut Water"],
    "sheer korma": ["Fruit Bowl", "Plain Curd", "Nuts And Seeds"],
    "sheera": ["Fruit Bowl", "Plain Curd", "Nuts And Seeds"],
    "sohan halwa": ["Fruit Bowl", "Plain Curd", "Nuts And Seeds"],
    "sohan papdi": ["Fruit Bowl", "Plain Curd", "Nuts And Seeds"],
    "sutar feni": ["Fruit Bowl", "Plain Curd", "Nuts And Seeds"],
    "veg biryani": ["Veg Salad", "Cucumber Raita", "Fruit Bowl"],
}


def validate_recommendation_inputs(nutrition_data, health_data):
    """
    Validate nutrition data and health data before generating recommendations.

    Args:
        nutrition_data: Dictionary containing nutrition values.
        health_data: Dictionary containing health score and category.

    Raises:
        ValueError: If input data is missing, empty, invalid, or negative.
    """
    if not nutrition_data:
        raise ValueError("Nutrition data is required.")

    if not health_data:
        raise ValueError("Health data is required.")

    if not isinstance(nutrition_data, dict):
        raise ValueError("Nutrition data must be provided as a dictionary.")

    if not isinstance(health_data, dict):
        raise ValueError("Health data must be provided as a dictionary.")

    for field in REQUIRED_NUTRITION_FIELDS:
        if field not in nutrition_data:
            raise ValueError(f"Missing nutrition value: {field}")

        try:
            value = float(nutrition_data[field])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid nutrition value for {field}.") from exc

        if value < 0:
            raise ValueError(f"Nutrition value for {field} cannot be negative.")

    if "health_score" not in health_data:
        raise ValueError("Missing health score.")

    if "category" not in health_data:
        raise ValueError("Missing health category.")


def analyze_nutrition(nutrition_data, health_data):
    """
    Analyze nutrition values and create simple health quality signals.

    Args:
        nutrition_data: Dictionary containing nutrition values.
        health_data: Dictionary containing health score and category.

    Returns:
        Dictionary with nutrition analysis flags.
    """
    try:
        validate_recommendation_inputs(nutrition_data, health_data)

        calories = float(nutrition_data["calories"])
        protein = float(nutrition_data["protein"])
        fat = float(nutrition_data["fat"])
        sugar = float(nutrition_data["sugar"])
        fiber = float(nutrition_data["fiber"])
        category = str(health_data["category"])

        return {
            "high_calorie": calories > 500 or category == "High Calorie",
            "high_sugar": sugar > 20,
            "high_fat": fat > 20,
            "good_protein": protein > 15,
            "low_protein": protein < 5,
            "good_fiber": fiber > 5,
            "low_fiber": fiber < 2,
            "health_category": category,
        }

    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Nutrition analysis failed: {exc}") from exc


def generate_health_advice(analysis):
    """
    Generate health advice from nutrition analysis.

    Args:
        analysis: Dictionary returned by analyze_nutrition().

    Returns:
        Health advice text.
    """
    try:
        advice_parts = []

        if analysis["high_calorie"] and analysis["high_fat"]:
            advice_parts.append("This food is high in calories and fat.")
        elif analysis["high_calorie"]:
            advice_parts.append("This food is high in calories.")
        elif analysis["high_fat"]:
            advice_parts.append("This food is high in fat.")

        if analysis["high_sugar"]:
            advice_parts.append("It also contains high sugar content.")

        if analysis["good_protein"]:
            advice_parts.append("It is a good protein source.")
        elif analysis["low_protein"]:
            advice_parts.append("It is low in protein.")

        if analysis["good_fiber"]:
            advice_parts.append("Its fiber content supports digestion.")
        elif analysis["low_fiber"]:
            advice_parts.append("It has low fiber content.")

        if not advice_parts:
            advice_parts.append("This food can fit into a balanced diet.")

        return " ".join(advice_parts)

    except KeyError as exc:
        raise ValueError("Invalid nutrition analysis data.") from exc


def suggest_alternatives(nutrition_data, analysis):
    """
    Suggest healthier alternative foods.

    Args:
        nutrition_data: Dictionary that may include food name.
        analysis: Dictionary returned by analyze_nutrition().

    Returns:
        List of healthy alternative foods.
    """
    try:
        food_name = str(nutrition_data.get("food", "")).lower().strip()
        alternatives = FOOD_ALTERNATIVES.get(food_name, DEFAULT_ALTERNATIVES)

        if analysis["high_sugar"]:
            alternatives = alternatives + ["Fresh Fruit Bowl", "Plain Curd", "Coconut Water"]

        if analysis["low_protein"]:
            alternatives = alternatives + ["Paneer Salad", "Sprout Bowl", "Grilled Chicken"]

        if analysis["high_calorie"] or analysis["high_fat"]:
            alternatives = alternatives + ["Vegetable Soup", "Veg Salad", "Grilled Paneer"]

        unique_alternatives = list(dict.fromkeys(alternatives))
        random.shuffle(unique_alternatives)

        return unique_alternatives[:5]

    except Exception as exc:
        raise ValueError(f"Alternative suggestion failed: {exc}") from exc


def generate_meal_tips(analysis):
    """
    Generate practical diet and balanced meal tips.

    Args:
        analysis: Dictionary returned by analyze_nutrition().

    Returns:
        List of meal guidance tips.
    """
    try:
        tips = []

        if analysis["high_calorie"]:
            tips.append("Consume in moderation and balance it with a lighter next meal.")

        if analysis["high_sugar"]:
            tips.append("Reduce sugary drinks or desserts with this meal.")

        if analysis["high_fat"]:
            tips.append("Pair with vegetables or salad instead of fried sides.")

        if analysis["low_protein"]:
            tips.append("Add a protein-rich item such as paneer, eggs, dal, or grilled chicken.")

        if analysis["good_protein"]:
            tips.append("Good protein choice for a filling meal.")

        if analysis["good_fiber"]:
            tips.append("Good fiber content can support digestion.")

        if not tips:
            tips.append("Keep portions balanced and include vegetables when possible.")

        return tips

    except KeyError as exc:
        raise ValueError("Invalid nutrition analysis data.") from exc


def generate_diet_suggestion(analysis):
    """
    Create one short diet suggestion based on the health category and analysis.

    Args:
        analysis: Dictionary returned by analyze_nutrition().

    Returns:
        Diet suggestion text.
    """
    try:
        category = analysis["health_category"]

        if category == "Very Healthy":
            return "This is a strong choice for a healthy meal plan."

        if category == "Healthy":
            return "This can be included as part of a balanced diet."

        if category == "Moderate":
            return "Consider lighter alternatives or reduce portion size."

        if category == "High Calorie":
            return "Choose lighter alternatives and avoid large portions."

        return "Consume in moderation and pair with healthier sides."

    except KeyError as exc:
        raise ValueError("Invalid nutrition analysis data.") from exc


def generate_recommendations(nutrition_data, health_data):
    """
    Main function to generate food recommendations.

    Args:
        nutrition_data: Dictionary containing nutrition values.
        health_data: Dictionary containing health score and category.

    Returns:
        Structured recommendation dictionary.

    Example:
        {
            "advice": "This food is high in calories and fat.",
            "suggestion": "Consider lighter alternatives.",
            "healthy_alternatives": ["Salad", "Fruit Bowl", "Grilled Chicken"],
            "meal_tips": ["Consume in moderation."]
        }
    """
    try:
        validate_recommendation_inputs(nutrition_data, health_data)

        analysis = analyze_nutrition(nutrition_data, health_data)
        advice = generate_health_advice(analysis)
        suggestion = generate_diet_suggestion(analysis)
        healthy_alternatives = suggest_alternatives(nutrition_data, analysis)
        meal_tips = generate_meal_tips(analysis)

        return {
            "advice": advice,
            "suggestion": suggestion,
            "healthy_alternatives": healthy_alternatives,
            "meal_tips": meal_tips,
            "health_category": analysis["health_category"],
        }

    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Recommendation generation failed: {exc}") from exc
