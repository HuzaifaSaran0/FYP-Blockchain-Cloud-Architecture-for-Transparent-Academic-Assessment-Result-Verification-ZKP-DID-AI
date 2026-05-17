import base64
import uuid
import os
import tempfile
import logging

logger = logging.getLogger(__name__)


def decode_base64_to_tempfile(base64_string: str) -> str:
    """
    Decodes a base64 image string into a temporary file.
    Returns the temp file path. Caller is responsible for cleanup.
    """
    try:
        if "," in base64_string:
            base64_string = base64_string.split(",")[1]
        image_data = base64.b64decode(base64_string)
        tmp = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".jpg",
            prefix=f"checkin_{uuid.uuid4().hex}_",
        )
        tmp.write(image_data)
        tmp.close()
        return tmp.name
    except Exception as e:
        logger.error(f"decode_base64_to_tempfile failed: {e}")
        raise ValueError("Invalid base64 image data. Could not decode image.")


def verify_face(live_image_path: str, stored_image_path: str) -> dict:
    """
    Compares two face images using DeepFace.
    Returns dict with keys: matched (bool), distance (float), threshold (float).
    """
    try:
        from deepface import DeepFace

        result = DeepFace.verify(
            img1_path=live_image_path,
            img2_path=stored_image_path,
            model_name="Facenet",
            detector_backend="opencv",
            distance_metric="cosine",
            enforce_detection=True,
        )
        return {
            "matched": result["verified"],
            "distance": round(result["distance"], 4),
            "threshold": round(result["threshold"], 4),
        }
    except ValueError as e:
        # DeepFace raises ValueError when no face is detected
        error_msg = str(e).lower()
        if "face" in error_msg or "detect" in error_msg:
            raise ValueError(
                "No face detected in the captured image. "
                "Please ensure your face is clearly visible and try again."
            )
        raise ValueError(f"Face verification error: {str(e)}")
    except Exception as e:
        logger.error(f"verify_face unexpected error: {e}")
        raise ValueError(
            "Face verification failed due to an unexpected error. Please try again."
        )


def cleanup_tempfile(path: str):
    """Silently removes a temp file."""
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass