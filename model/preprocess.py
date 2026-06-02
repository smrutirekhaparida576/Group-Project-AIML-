"""
Image preprocessing module for NutriScan - Food Calorie Detector.

This file prepares uploaded food images for future TensorFlow/Keras model
prediction. It does not contain any model training or prediction logic.
"""

import os

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError


TARGET_SIZE = (224, 224)


def load_image(image_source):
    """
    Load an image from a file path or an uploaded image object.

    Args:
        image_source: Image file path, PIL image, or uploaded file object.

    Returns:
        Image as an OpenCV BGR NumPy array.

    Raises:
        ValueError: If the image cannot be loaded.
    """
    try:
        if isinstance(image_source, str):
            if not os.path.exists(image_source):
                raise ValueError(f"Invalid image path: {image_source}")

            image = cv2.imread(image_source)
            if image is None:
                raise ValueError("Unable to read image. File may be corrupted or unsupported.")

            return image

        if isinstance(image_source, Image.Image):
            pil_image = image_source.convert("RGB")
        else:
            pil_image = Image.open(image_source).convert("RGB")

        image_array = np.array(pil_image)
        return cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)

    except UnidentifiedImageError as exc:
        raise ValueError("Unsupported or corrupted image format.") from exc
    except OSError as exc:
        raise ValueError("Unable to open image. File may be corrupted.") from exc
    except Exception as exc:
        raise ValueError(f"Image loading failed: {exc}") from exc


def resize_image(image, target_size=TARGET_SIZE):
    """
    Resize image to the target size required by future ML models.

    Args:
        image: OpenCV image array.
        target_size: Desired image size as (width, height).

    Returns:
        Resized image array.
    """
    try:
        return cv2.resize(image, target_size)
    except Exception as exc:
        raise ValueError(f"Image resizing failed: {exc}") from exc


def convert_to_rgb(image):
    """
    Convert an OpenCV BGR image to RGB format.

    Args:
        image: OpenCV BGR image array.

    Returns:
        RGB image array.
    """
    try:
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    except Exception as exc:
        raise ValueError(f"Color conversion failed: {exc}") from exc


def normalize_image(image):
    """
    Normalize pixel values from 0-255 to 0-1.

    Args:
        image: Image array with pixel values from 0 to 255.

    Returns:
        Normalized float32 image array.
    """
    try:
        return image.astype(np.float32) / 255.0
    except Exception as exc:
        raise ValueError(f"Image normalization failed: {exc}") from exc


def image_to_array(image):
    """
    Convert image data to a NumPy array.

    Args:
        image: Image data.

    Returns:
        NumPy image array.
    """
    try:
        return np.array(image, dtype=np.float32)
    except Exception as exc:
        raise ValueError(f"Image to array conversion failed: {exc}") from exc


def expand_dimensions(image_array):
    """
    Add a batch dimension for future model prediction.

    Example:
        (224, 224, 3) becomes (1, 224, 224, 3)

    Args:
        image_array: Preprocessed image array.

    Returns:
        Image array with batch dimension.
    """
    try:
        return np.expand_dims(image_array, axis=0)
    except Exception as exc:
        raise ValueError(f"Expanding image dimensions failed: {exc}") from exc


def preprocess_image(image_source):
    """
    Run the complete image preprocessing pipeline.

    Pipeline:
        Load Image -> Resize -> Convert RGB -> Normalize -> Convert to Array
        -> Expand Dimensions

    Args:
        image_source: Image file path, PIL image, or uploaded file object.

    Returns:
        ML-ready NumPy array with shape (1, 224, 224, 3).
    """
    try:
        image = load_image(image_source)
        image = resize_image(image)
        image = convert_to_rgb(image)
        image = normalize_image(image)
        image_array = image_to_array(image)
        processed_image = expand_dimensions(image_array)

        return processed_image

    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Image preprocessing failed: {exc}") from exc
