"""Image preprocessing module for screenshot contrast, sharpness, and cropping."""
import io
import math
from typing import Tuple, Optional
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import numpy as np


class ImageProcessor:
    """Preprocesses screenshot images for optimal OCR detection."""

    MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB
    ALLOWED_FORMATS = {"PNG", "JPEG", "JPG", "WEBP"}

    @classmethod
    def validate_image_bytes(cls, image_bytes: bytes, filename: str) -> Tuple[bool, str, Optional[str]]:
        """Validate size, magic headers, and format."""
        if len(image_bytes) == 0:
            return False, "Image file is empty", None
        if len(image_bytes) > cls.MAX_FILE_SIZE:
            return False, f"Image exceeds maximum allowable size of {cls.MAX_FILE_SIZE // (1024 * 1024)}MB", None

        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                fmt = (img.format or "").upper()
                if fmt not in cls.ALLOWED_FORMATS:
                    return False, f"Unsupported image format: {fmt}. Allowed: PNG, JPG, JPEG, WEBP", None
                return True, "Valid image", fmt
        except Exception as e:
            return False, f"Corrupted or invalid image file: {str(e)}", None

    @classmethod
    def preprocess_for_ocr(cls, image_bytes: bytes) -> Tuple[Image.Image, np.ndarray]:
        """Normalize orientation, enhance contrast, and prepare high-contrast grayscale for text detection."""
        with Image.open(io.BytesIO(image_bytes)) as raw_img:
            # Transpose according to EXIF if present
            img = ImageOps.exif_transpose(raw_img)
            img = img.convert("RGB")

            # Aviator multiplier pills usually have colored backgrounds (blue, purple, magenta) with white text.
            # Convert to high contrast grayscale
            gray = ImageOps.grayscale(img)
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(gray)
            high_contrast = enhancer.enhance(2.0)

            # Enhance sharpness
            sharpness = ImageEnhance.Sharpness(high_contrast)
            sharpened = sharpness.enhance(2.2)

            # Convert to numpy array for cv2/heuristic processing
            np_arr = np.array(sharpened)
            return sharpened, np_arr
