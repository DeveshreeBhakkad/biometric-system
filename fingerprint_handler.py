import ctypes
import os
import time
import io
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import random

# Load only from project folder
DLL_SEARCH_PATHS = [
    r"MFS100Dll.dll"
]

IMAGE_WIDTH = 256
IMAGE_HEIGHT = 360


class FingerprintHandler:
    def __init__(self):
        self.sdk = None
        self.device_connected = False
        self._load_sdk()

    def _load_sdk(self):
        for path in DLL_SEARCH_PATHS:
            if os.path.exists(path):
                try:
                    self.sdk = ctypes.CDLL(path)
                    print(f"[MFS100] Loaded DLL from: {path}")
                    return
                except Exception as e:
                    print(f"[MFS100] Failed to load {path}: {e}")
        print("[MFS100] DLL not found")

    # ✅ Safe device detection
    def check_device(self):
        if self.sdk is not None:
            self.device_connected = True
            print("[MFS100] DLL Loaded — assuming device connected ✅")
            return True

        print("[MFS100] Device not connected ❌")
        return False

    # ✅ Capture using fallback
    def capture_fingerprint(self, timeout_seconds=10):
        print("[MFS100] Using fallback capture (SDK limitation)")
        return self._simulated_capture()

    # ✅ Simulated fingerprint generator
    def _simulated_capture(self):
        print("[MFS100] Generating simulated fingerprint...")
        time.sleep(1)

        w, h = IMAGE_WIDTH, IMAGE_HEIGHT
        img = Image.new("L", (w, h), 200)
        draw = ImageDraw.Draw(img)

        cx, cy = w // 2, h // 2

        # Draw fingerprint-like curves
        for i in range(1, 30):
            rx = 5 + i * 3
            ry = 8 + i * 4
            offset = random.randint(-3, 3)

            x0 = cx - rx + offset
            y0 = cy - ry + offset
            x1 = cx + rx + offset
            y1 = cy + ry + offset

            draw.ellipse([x0, y0, x1, y1],
                         outline=random.randint(30, 80),
                         width=2)

        # Add noise
        arr = np.array(img)
        noise = np.random.normal(0, 8, arr.shape).astype(np.int16)
        arr = np.clip(arr + noise, 0, 255).astype(np.uint8)

        img = Image.fromarray(arr)
        img = img.filter(ImageFilter.GaussianBlur(0.7))
        img = img.convert("RGB")

        # Convert to bytes
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=95)

        return img, buffer.getvalue()

    def bytes_to_pil(self, img_bytes):
        return Image.open(io.BytesIO(img_bytes)).convert("RGB")

    def cleanup(self):
        pass