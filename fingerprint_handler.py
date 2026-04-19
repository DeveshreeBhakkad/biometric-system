"""
fingerprint_handler.py
Handles Mantra MFS100 fingerprint scanner via MFS100.dll
Falls back to simulation mode if device not connected.
"""

import ctypes
import os
import time
import io
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import random

# ─── MFS100 DLL Search Paths ───
DLL_SEARCH_PATHS = [
    r"C:\Program Files\Mantra\MFS100\Driver\MFS100Test\MFS100Dll.dll",
    r"C:\Program Files\Mantra\MFS100\Driver\Driver\Win-10-X64\MFS100CI.dll",
    r"C:\Windows\System32\MFS100.dll",
    r"C:\Mantra\MFS100\MFS100.dll",
    r"C:\Program Files\Mantra\MFS100.dll",
    r"C:\Program Files (x86)\Mantra\MFS100.dll",
    r"MFS100.dll",
]

# ─── MFS100 Constants ───
MFS100_SUCCESS          = 0
MFS100_DEVICE_NOT_FOUND = -1
MFS100_NO_FINGER        = -2

IMAGE_WIDTH  = 256
IMAGE_HEIGHT = 360


class FingerprintHandler:
    def __init__(self):
        self.sdk             = None
        self.device_connected = False
        self._load_sdk()

    # ─────────────── SDK LOAD ───────────────
    def _load_sdk(self):
        """Try to load MFS100.dll from known paths."""
        for path in DLL_SEARCH_PATHS:
            if os.path.exists(path):
                try:
                    self.sdk = ctypes.CDLL(path)
                    print(f"[MFS100] Loaded DLL from: {path}")
                    return
                except Exception as e:
                    print(f"[MFS100] Failed to load {path}: {e}")
        print("[MFS100] DLL not found — simulation mode active")

    # ─────────────── DEVICE CHECK ───────────────
    def check_device(self):
        """Check if MFS100 is connected."""
        if self.sdk is None:
            self.device_connected = False
            return False
        try:
            result = self.sdk.MFS100_Init()
            if result == MFS100_SUCCESS:
                self.device_connected = True
                print("[MFS100] Device connected ✅")
                return True
        except Exception as e:
            print(f"[MFS100] Device check error: {e}")
        self.device_connected = False
        return False

    # ─────────────── CAPTURE ───────────────
    def capture_fingerprint(self, timeout_seconds=10):
        """
        Capture fingerprint from MFS100.
        Returns: (pil_image, image_bytes) or (None, None) on failure.
        Falls back to simulation if device not connected.
        """
        if self.device_connected and self.sdk:
            return self._real_capture(timeout_seconds)
        else:
            return self._simulated_capture()

    def _real_capture(self, timeout_seconds):
        """Capture using MFS100 SDK."""
        try:
            img_size   = IMAGE_WIDTH * IMAGE_HEIGHT
            img_buffer = (ctypes.c_ubyte * img_size)()

            print("[MFS100] Waiting for finger...")
            start = time.time()
            while time.time() - start < timeout_seconds:
                result = self.sdk.MFS100_GetImage(
                    ctypes.byref(img_buffer),
                    ctypes.c_int(img_size)
                )
                if result == MFS100_SUCCESS:
                    print("[MFS100] Fingerprint captured!")
                    pil_img = self._buffer_to_pil(img_buffer)
                    return pil_img, self._pil_to_bytes(pil_img)
                elif result == MFS100_NO_FINGER:
                    time.sleep(0.3)
                else:
                    print(f"[MFS100] Error code: {result}")
                    return None, None

            print("[MFS100] Timeout waiting for finger")
            return None, None

        except Exception as e:
            print(f"[MFS100] Capture error: {e}")
            return None, None

    def _buffer_to_pil(self, buffer):
        """Convert raw byte buffer to PIL grayscale image."""
        try:
            arr = np.frombuffer(buffer, dtype=np.uint8).reshape(
                (IMAGE_HEIGHT, IMAGE_WIDTH)
            )
            return Image.fromarray(arr, mode="L").convert("RGB")
        except Exception as e:
            print(f"[MFS100] Buffer conversion error: {e}")
            return None

    # ─────────────── SIMULATION ───────────────
    def _simulated_capture(self):
        """
        Generate a realistic-looking synthetic fingerprint for testing.
        Used when device is not connected.
        """
        print("[MFS100] Simulation mode — generating fake fingerprint")
        time.sleep(1.2)

        w, h = IMAGE_WIDTH, IMAGE_HEIGHT
        img  = Image.new("L", (w, h), 200)
        draw = ImageDraw.Draw(img)

        cx, cy = w // 2, h // 2
        for i in range(1, 35):
            rx     = 8 + i * 3
            ry     = 10 + i * 4
            offset = random.randint(-3, 3)
            x0     = cx - rx + offset
            y0     = cy - ry + offset
            x1     = cx + rx + offset
            y1     = cy + ry + offset
            color  = random.randint(20, 90)
            draw.ellipse([x0, y0, x1, y1], outline=color, width=2)

        arr   = np.array(img)
        noise = np.random.normal(0, 8, arr.shape).astype(np.int16)
        arr   = np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        img   = Image.fromarray(arr, mode="L")
        img   = img.filter(ImageFilter.GaussianBlur(radius=0.8))
        img   = img.convert("RGB")

        return img, self._pil_to_bytes(img)

    # ─────────────── UTILS ───────────────
    def _pil_to_bytes(self, pil_img):
        """Convert PIL image to JPEG bytes for storing in DB."""
        buffer = io.BytesIO()
        pil_img.save(buffer, format="JPEG", quality=95)
        return buffer.getvalue()

    def bytes_to_pil(self, img_bytes):
        """Convert stored JPEG bytes back to PIL image (for display)."""
        return Image.open(io.BytesIO(img_bytes)).convert("RGB")

    # ─────────────── CLEANUP ───────────────
    def cleanup(self):
        if self.sdk and self.device_connected:
            try:
                self.sdk.MFS100_Close()
            except Exception:
                pass


# ─── Quick test ───
if __name__ == "__main__":
    handler = FingerprintHandler()
    connected = handler.check_device()
    print(f"Device connected: {connected}")
    print("Capturing fingerprint...")
    img, img_bytes = handler.capture_fingerprint()
    if img:
        print(f"Captured! Image size: {img.size}, Bytes: {len(img_bytes)}")
        img.save("test_fingerprint.jpg")
        print("Saved as test_fingerprint.jpg")
    else:
        print("Capture failed.")