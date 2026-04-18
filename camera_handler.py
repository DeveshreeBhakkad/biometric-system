"""
camera_handler.py
Handles webcam capture for customer photo.
"""

import cv2
import io
from PIL import Image


class CameraHandler:
    def __init__(self):
        self.cap = None

    def open_camera(self, index=0):
        """Open webcam. Returns cap object or None."""
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            self.cap = cap
            return cap
        return None

    def read_frame(self):
        """Read one frame from open camera. Returns PIL image or None."""
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                return Image.fromarray(frame_rgb)
        return None

    def release(self):
        """Release the webcam."""
        if self.cap:
            self.cap.release()
            self.cap = None

    def pil_to_bytes(self, pil_img):
        """Convert PIL image to JPEG bytes for storing in DB."""
        buffer = io.BytesIO()
        pil_img.save(buffer, format="JPEG", quality=95)
        return buffer.getvalue()

    def bytes_to_pil(self, img_bytes):
        """Convert stored bytes back to PIL image."""
        return Image.open(io.BytesIO(img_bytes)).convert("RGB")
    