"""
Local CSV nutrition lookup for NutriScan - Food Calorie Detector.

This module reads nutrition values from the Indian food nutrition CSV dataset.
It does not call any online API.
"""

import csv
import os
import re
from difflib import get_close_matches
from functools import lru_cache
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_PATH = (
    PROJECT_ROOT
    / "Indian_food_nutritional_dataset"
    / "nutrition.csv"
)

if load_dotenv:
    load_dotenv(PROJECT_ROOT / ".env")
    load_dotenv()


COLUMN_ALIASES = {
    "food": ["Dish Name", "Food", "Food Name", "dish_name", "name"],
    "calories": ["Calories (kcal)", "Calories", "calories", "Energy (kcal)"],
    "carbs": ["Carbohydrates (g)", "Carbs (g)", "Carbohydrates", "carbs"],
    "protein": ["Protein (g)", "Protein", "protein"],
    "fat": ["Fats (g)", "Fat (g)", "Fats", "Fat", "fat"],
    "sugar": ["Free Sugar (g)", "Sugar (g)", "Sugars (g)", "Sugar", "sugar"],
    "fiber": ["Fibre (g)", "Fiber (g)", "Fibre", "Fiber", "fiber"],
}


FOOD_NAME_ALIASES = {
    "paneer butter masala": "paneer in butter sauce",
    "palak paneer": "spinach paneer",
    "kadai paneer": "kadhai paneer",
    "biryani": "vegetable biryani biriyani",
    "maach jhol": "fish curry",
    "makki di roti sarson da saag": "makki roti sarson saag",
    "ras malai": "rasmalai",
}


def normalize_food_key(food_name):
    text = str(food_name or "").lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _safe_float(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _resolve_dataset_path():
    configured_path = Path(os.getenv("NUTRITION_DATASET_PATH", DEFAULT_DATASET_PATH))
    dataset_path = configured_path if configured_path.is_absolute() else PROJECT_ROOT / configured_path

    if not dataset_path.exists():
        raise ValueError(f"Nutrition CSV dataset not found at: {dataset_path}")

    return dataset_path


def _find_column(fieldnames, candidates):
    for candidate in candidates:
        if candidate in fieldnames:
            return candidate

    normalized_columns = {normalize_food_key(column): column for column in fieldnames}
    for candidate in candidates:
        normalized = normalize_food_key(candidate)
        if normalized in normalized_columns:
            return normalized_columns[normalized]

    return None


def _extract_aliases(food_name):
    aliases = {normalize_food_key(food_name)}

    for parenthetical in re.findall(r"\((.*?)\)", str(food_name)):
        aliases.add(normalize_food_key(parenthetical))

    aliases.add(normalize_food_key(re.sub(r"\(.*?\)", "", str(food_name))))

    for token in re.split(r"/|,", str(food_name)):
        aliases.add(normalize_food_key(token))

    return {alias for alias in aliases if alias}


@lru_cache(maxsize=1)
def load_nutrition_rows():
    dataset_path = _resolve_dataset_path()

    with dataset_path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = reader.fieldnames or []

        columns = {
            key: _find_column(fieldnames, aliases)
            for key, aliases in COLUMN_ALIASES.items()
        }

        if not columns["food"]:
            raise ValueError("Nutrition CSV must contain a food or dish name column.")

        required = ["calories", "protein", "carbs", "fat", "sugar", "fiber"]
        missing = [key for key in required if not columns[key]]
        if missing:
            raise ValueError(f"Nutrition CSV is missing required columns: {', '.join(missing)}")

        rows = []
        lookup = {}

        for row in reader:
            food = (row.get(columns["food"]) or "").strip()
            if not food:
                continue

            nutrition = {
                "food": food,
                "searched_food": food,
                "calories": _safe_float(row.get(columns["calories"])),
                "protein": _safe_float(row.get(columns["protein"])),
                "carbs": _safe_float(row.get(columns["carbs"])),
                "fat": _safe_float(row.get(columns["fat"])),
                "sugar": _safe_float(row.get(columns["sugar"])),
                "fiber": _safe_float(row.get(columns["fiber"])),
                "serving_size": 100.0,
                "source": "Local nutrition CSV",
            }

            rows.append(nutrition)

            for alias in _extract_aliases(food):
                lookup.setdefault(alias, nutrition)

    return rows, lookup


def get_available_food_names():
    rows, _ = load_nutrition_rows()
    return sorted({row["food"] for row in rows})


def get_nutrition_data(food_name):
    if food_name is None or not str(food_name).strip():
        raise ValueError("Food name is required.")

    rows, lookup = load_nutrition_rows()
    search_key = normalize_food_key(food_name)
    alias_key = FOOD_NAME_ALIASES.get(search_key)

    match = lookup.get(search_key)

    if not match and alias_key:
        match = lookup.get(alias_key)

    if not match:
        contains_matches = [
            key for key in lookup
            if key in search_key and key != search_key
        ]
        if contains_matches:
            best_key = max(contains_matches, key=len)
            match = lookup[best_key]

    if not match:
        close_matches = get_close_matches(search_key, lookup.keys(), n=1, cutoff=0.88)
        if close_matches:
            match = lookup[close_matches[0]]

    if not match:
        raise ValueError(f"No nutrition data found in the local CSV for: {food_name}")

    return {
        **match,
        "searched_food": str(food_name),
    }
