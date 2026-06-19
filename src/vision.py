"""Image handling for the vision feature.

Turns an uploaded failure photo into an Anthropic image content block, and builds the first
user message (text plus optional image). The model reads the image natively; there is no
separate vision model. A phone photo shows MACRO features only (deformation, fracture
orientation, corrosion, large beach marks), not the micron-scale striations or dimples that
need an SEM, and the agent is told to treat it that way.
"""

import base64
import os

_MEDIA = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp"}


def image_block_from_path(path):
    ext = os.path.splitext(path)[1].lower()
    media_type = _MEDIA.get(ext, "image/jpeg")
    with open(path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode()
    return {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": data}}


def image_block_from_bytes(data, media_type="image/jpeg"):
    return {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": base64.standard_b64encode(bytes(data)).decode()}}


def build_user_content(text, image=None):
    """image may be a file path (str), raw bytes, a prebuilt block (dict), or None."""
    if not image:
        return text
    if isinstance(image, dict):
        block = image
    elif isinstance(image, (bytes, bytearray)):
        block = image_block_from_bytes(image)
    else:
        block = image_block_from_path(image)
    # Image first, then the text, so the model looks before it reads the prompt.
    return [block, {"type": "text", "text": text}]
