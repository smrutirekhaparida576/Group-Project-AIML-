"""
YOLO prediction module for NutriScan - Food Calorie Detector.

Loads the trained Ultralytics YOLO model and returns the predicted food label
with confidence.
"""

import os
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATH = PROJECT_ROOT / "model" / "best.pt"
DEFAULT_SERVING_MODEL_PATH = PROJECT_ROOT / "model" / "Serving_Size.pt"
ULTRALYTICS_CONFIG_DIR = PROJECT_ROOT / "Ultralytics"

if load_dotenv:
    load_dotenv(PROJECT_ROOT / ".env")
    load_dotenv()


def _display_food_name(label):
    return str(label).replace("_", " ").title()


def _normalize_label(label):
    return str(label or "").replace("_", " ").strip().lower()


def _resolve_model_path():
    configured_path = Path(os.getenv("FOOD_MODEL_PATH", DEFAULT_MODEL_PATH))
    model_path = configured_path if configured_path.is_absolute() else PROJECT_ROOT / configured_path

    if not model_path.exists():
        raise ValueError(
            f"YOLO food model not found at: {model_path}. Put your trained best.pt file there "
            "or update FOOD_MODEL_PATH in .env."
        )

    if model_path.suffix.lower() != ".pt":
        raise ValueError("This app is now configured for a YOLO .pt model. Update FOOD_MODEL_PATH to your best.pt file.")

    return model_path


def _resolve_serving_model_path():
    configured_path = Path(os.getenv("SERVING_MODEL_PATH", DEFAULT_SERVING_MODEL_PATH))
    model_path = configured_path if configured_path.is_absolute() else PROJECT_ROOT / configured_path

    if not model_path.exists():
        raise ValueError(
            f"YOLO serving-size model not found at: {model_path}. Put your trained Serving_Size.pt file there "
            "or update SERVING_MODEL_PATH in .env."
        )

    if model_path.suffix.lower() != ".pt":
        raise ValueError("Serving-size estimation requires a YOLO .pt model. Update SERVING_MODEL_PATH.")

    return model_path


def _load_yolo_module():
    try:
        os.environ.setdefault("YOLO_CONFIG_DIR", str(ULTRALYTICS_CONFIG_DIR))
        from ultralytics import YOLO

        return YOLO
    except ImportError as exc:
        raise ValueError("Ultralytics is not installed. Install requirements before running the YOLO model.") from exc


@lru_cache(maxsize=1)
def load_model():
    model_path = _resolve_model_path()
    YOLO = _load_yolo_module()
    return YOLO(str(model_path))


@lru_cache(maxsize=1)
def load_serving_model():
    model_path = _resolve_serving_model_path()
    YOLO = _load_yolo_module()
    return YOLO(str(model_path))


def _prepare_image(image):
    if isinstance(image, Image.Image):
        prepared_image = ImageOps.exif_transpose(image).convert("RGB")
        if prepared_image.size[0] == 0 or prepared_image.size[1] == 0:
            raise ValueError("Image input is empty.")
        return prepared_image

    image_array = np.asarray(image)

    if image_array.size == 0:
        raise ValueError("Image input is empty.")

    if image_array.ndim == 4:
        image_array = image_array[0]

    if image_array.ndim != 3 or image_array.shape[-1] not in {3, 4}:
        raise ValueError("Invalid image format. Expected an RGB food image.")

    if image_array.shape[-1] == 4:
        image_array = image_array[..., :3]

    if image_array.dtype != np.uint8:
        max_value = float(np.max(image_array))
        if max_value <= 1.0:
            image_array = image_array * 255
        image_array = np.clip(image_array, 0, 255).astype(np.uint8)

    return Image.fromarray(image_array, mode="RGB")


def _model_image_size(model):
    overrides = getattr(model, "overrides", {}) or {}
    return int(overrides.get("imgsz") or 224)


def _format_prediction(label, confidence, class_index):
    return {
        "food": _display_food_name(label),
        "confidence": f"{confidence * 100:.1f}%",
        "confidence_value": round(confidence * 100, 1),
        "class_index": class_index,
    }


def _clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def _top_class_predictions(probs, names, limit=5):
    scores = probs.data.cpu().numpy()
    top_indexes = np.argsort(scores)[::-1][:limit]
    predictions = []

    for index in top_indexes:
        label = names.get(int(index), str(index)) if isinstance(names, dict) else names[int(index)]
        confidence = float(scores[index])
        predictions.append(_format_prediction(label, confidence, int(index)))

    return predictions


def _top_detection_predictions(boxes, names, limit=5):
    confidences = boxes.conf.cpu().numpy()
    class_indexes = boxes.cls.cpu().numpy().astype(int)
    top_indexes = np.argsort(confidences)[::-1][:limit]
    predictions = []

    for box_index in top_indexes:
        class_index = int(class_indexes[box_index])
        label = names.get(class_index, str(class_index)) if isinstance(names, dict) else names[class_index]
        confidence = float(confidences[box_index])
        predictions.append(_format_prediction(label, confidence, class_index))

    return predictions


def predict_food(image):
    try:
        model = load_model()
        results = model.predict(_prepare_image(image), imgsz=_model_image_size(model), verbose=False)

        if not results:
            raise ValueError("YOLO model did not return a prediction.")

        result = results[0]
        names = result.names or getattr(model, "names", {}) or {}

        if getattr(result, "probs", None) is not None:
            predicted_index = int(result.probs.top1)
            confidence = float(result.probs.top1conf)
            top_predictions = _top_class_predictions(result.probs, names)
        elif getattr(result, "boxes", None) is not None and len(result.boxes) > 0:
            confidences = result.boxes.conf.cpu().numpy()
            best_box_index = int(np.argmax(confidences))
            predicted_index = int(result.boxes.cls[best_box_index].item())
            confidence = float(confidences[best_box_index])
            top_predictions = _top_detection_predictions(result.boxes, names)
        else:
            raise ValueError("YOLO model returned no class prediction.")

        if isinstance(names, dict):
            label = names.get(predicted_index, str(predicted_index))
        else:
            label = names[predicted_index]

        prediction = _format_prediction(label, confidence, predicted_index)
        prediction["top_predictions"] = top_predictions
        return prediction

    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Food prediction failed: {exc}") from exc


def _serving_base_grams(food_name):
    normalized = _normalize_label(food_name)

    if any(word in normalized for word in ["biryani", "chicken", "dal", "chana", "paneer", "kofta", "korma", "dum aloo"]):
        return 220
    if any(word in normalized for word in ["naan", "roti", "chapati", "bhatura", "puri", "kachori"]):
        return 90
    if any(word in normalized for word in ["lassi", "kheer", "basundi", "doodhpak", "phirni", "rabri", "misti doi", "shrikhand"]):
        return 180
    if any(word in normalized for word in ["jalebi", "laddu", "gulab", "rasgulla", "sandesh", "modak", "peda", "halwa", "mysore"]):
        return 80

    return 150


def _estimate_grams_from_box(food_name, image_size, box):
    image_width, image_height = image_size
    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
    box_area = max(0.0, float(x2 - x1)) * max(0.0, float(y2 - y1))
    image_area = max(1.0, float(image_width * image_height))
    area_ratio = _clamp(box_area / image_area, 0.05, 0.9)

    # Scale around a typical plated-food crop where the food covers about 35% of the image.
    base_grams = _serving_base_grams(food_name)
    scaled_grams = base_grams * (area_ratio / 0.35) ** 0.5
    rounded_grams = int(round(_clamp(scaled_grams, 50, 600) / 5) * 5)

    return rounded_grams, round(area_ratio * 100, 1)


def predict_serving_size(image, food_name=None):
    try:
        prepared_image = _prepare_image(image)
        model = load_serving_model()
        results = model.predict(prepared_image, imgsz=_model_image_size(model), verbose=False)

        if not results:
            raise ValueError("Serving-size model did not return a prediction.")

        result = results[0]
        boxes = getattr(result, "boxes", None)

        if boxes is None or len(boxes) == 0:
            raise ValueError("Serving-size model returned no food region.")

        names = result.names or getattr(model, "names", {}) or {}
        requested_label = _normalize_label(food_name)
        candidate_indexes = range(len(boxes))

        if requested_label:
            matching_indexes = []
            for index, class_index in enumerate(boxes.cls.cpu().numpy().astype(int)):
                label = names.get(int(class_index), str(class_index)) if isinstance(names, dict) else names[int(class_index)]
                if _normalize_label(label) == requested_label:
                    matching_indexes.append(index)

            if matching_indexes:
                candidate_indexes = matching_indexes

        best_index = max(candidate_indexes, key=lambda index: float(boxes.conf[index].item()))
        class_index = int(boxes.cls[best_index].item())
        label = names.get(class_index, str(class_index)) if isinstance(names, dict) else names[class_index]
        confidence = float(boxes.conf[best_index].item())
        grams, area_percent = _estimate_grams_from_box(label, prepared_image.size, boxes[best_index])

        return {
            "serving_grams": grams,
            "serving_confidence": f"{confidence * 100:.1f}%",
            "serving_confidence_value": round(confidence * 100, 1),
            "serving_food": _display_food_name(label),
            "serving_area_percent": area_percent,
            "serving_source": "Serving_Size.pt",
        }

    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Serving-size prediction failed: {exc}") from exc
