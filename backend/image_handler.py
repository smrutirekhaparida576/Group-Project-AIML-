"""
Image handling utilities for NutriScan.

This module is the first backend step only. It receives images uploaded from
Streamlit, validates them, saves them safely, and prepares image arrays for a
future ML model.
"""

import os
import uuid

import cv2
import numpy as np
import streamlit as st
from PIL import Image, UnidentifiedImageError


ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
UPLOAD_FOLDER = "uploads"
IMAGE_SIZE = (224, 224)


def validate_image(uploaded_file):
    """
    Validate a Streamlit uploaded image.

    Returns:
        tuple: (is_valid, message)
    """
    if uploaded_file is None:
        return False, "No image uploaded. Please choose an image file."

    filename = uploaded_file.name
    if not filename or "." not in filename:
        return False, "Invalid file name. Please upload a JPG, JPEG, or PNG image."

    extension = filename.rsplit(".", 1)[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        return False, "Unsupported file format. Only JPG, JPEG, and PNG are allowed."

    try:
        uploaded_file.seek(0)
        image = Image.open(uploaded_file)
        image.verify()
        uploaded_file.seek(0)
    except UnidentifiedImageError:
        return False, "The uploaded file is not a valid image."
    except Exception:
        return False, "The image appears to be corrupted or unreadable."

    return True, "Image is valid."


def save_uploaded_image(uploaded_file, upload_folder=UPLOAD_FOLDER):
    """
    Save a valid Streamlit uploaded image with a unique file name.

    Returns:
        tuple: (saved_path, message)
    """
    is_valid, message = validate_image(uploaded_file)
    if not is_valid:
        return None, message

    try:
        os.makedirs(upload_folder, exist_ok=True)

        extension = uploaded_file.name.rsplit(".", 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{extension}"
        saved_path = os.path.join(upload_folder, unique_filename)

        uploaded_file.seek(0)
        with open(saved_path, "wb") as image_file:
            image_file.write(uploaded_file.getbuffer())

        uploaded_file.seek(0)
        return saved_path, "Image saved successfully."
    except OSError:
        return None, "Could not create the uploads folder or save the image."
    except Exception:
        return None, "An unexpected error occurred while saving the image."


def resize_image(image, size=IMAGE_SIZE):
    """
    Convert an image to RGB and resize it to the target model input size.

    Args:
        image: PIL Image object.
        size: Output size as (width, height).

    Returns:
        PIL.Image.Image: resized RGB image.
    """
    if image is None:
        raise ValueError("Cannot resize an empty image.")

    rgb_image = image.convert("RGB")
    return rgb_image.resize(size)


def convert_to_array(image):
    """
    Convert a PIL image into a NumPy array prepared for future ML prediction.

    OpenCV is used to keep this backend compatible with image pipelines that
    may later depend on cv2 preprocessing.

    Returns:
        np.ndarray: image array with shape (1, 224, 224, 3).
    """
    if image is None:
        raise ValueError("Cannot convert an empty image to an array.")

    image_array = np.array(image)
    image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
    image_array = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
    image_array = image_array.astype("float32") / 255.0

    return np.expand_dims(image_array, axis=0)


def preprocess_image(uploaded_file):
    """
    Validate, resize, and convert a Streamlit uploaded image for model use.

    Returns:
        tuple: (processed_array, resized_image, message)
    """
    is_valid, message = validate_image(uploaded_file)
    if not is_valid:
        return None, None, message

    try:
        uploaded_file.seek(0)
        image = Image.open(uploaded_file)
        resized_image = resize_image(image)
        processed_array = convert_to_array(resized_image)
        uploaded_file.seek(0)

        return processed_array, resized_image, "Image processed successfully."
    except UnidentifiedImageError:
        return None, None, "The uploaded file is not a valid image."
    except ValueError as error:
        return None, None, str(error)
    except Exception:
        return None, None, "An unexpected error occurred while processing the image."


def get_image_details(uploaded_file):
    """
    Return basic image details useful for displaying in Streamlit.

    Returns:
        dict: image metadata, or None if details cannot be read.
    """
    is_valid, message = validate_image(uploaded_file)
    if not is_valid:
        return None

    try:
        uploaded_file.seek(0)
        image = Image.open(uploaded_file)
        details = {
            "filename": uploaded_file.name,
            "format": image.format,
            "mode": image.mode,
            "width": image.width,
            "height": image.height,
            "size": uploaded_file.size,
        }
        uploaded_file.seek(0)
        return details
    except Exception:
        return None


def handle_uploaded_image(uploaded_file):
    """
    Complete image-handling flow for Streamlit.

    This function does not predict calories. It only prepares the uploaded image
    so future modules like preprocess.py or predict.py can use it.

    Returns:
        dict: status, saved path, image details, processed array, and message.
    """
    saved_path, save_message = save_uploaded_image(uploaded_file)
    if saved_path is None:
        return {
            "success": False,
            "saved_path": None,
            "details": None,
            "processed_array": None,
            "message": save_message,
        }

    processed_array, resized_image, process_message = preprocess_image(uploaded_file)
    if processed_array is None:
        return {
            "success": False,
            "saved_path": saved_path,
            "details": get_image_details(uploaded_file),
            "processed_array": None,
            "resized_image": None,
            "message": process_message,
        }

    return {
        "success": True,
        "saved_path": saved_path,
        "details": get_image_details(uploaded_file),
        "processed_array": processed_array,
        "resized_image": resized_image,
        "message": "Image saved and processed successfully.",
    }


def show_streamlit_message(success, message):
    """
    Optional helper for displaying clean Streamlit messages.
    """
    if success:
        st.success(message)
    else:
        st.error(message)
