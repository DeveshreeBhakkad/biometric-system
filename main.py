import tkinter as tk
from PIL import Image, ImageTk
import subprocess
import os
import sqlite3
import time
import requests

# =========================
# PATHS
# =========================
EXE_PATH = r"D:\DEVESHREE\GITHUB\biometric-system\MFS100Bridge\MFS100Bridge\bin\x86\Debug\MFS100Bridge.exe"
BASE_IMAGE_PATH = r"D:\DEVESHREE\GITHUB\biometric-system\MFS100Bridge\MFS100Bridge\bin\x86\Debug"

# =========================
# DATABASE
# =========================
def create_table():
    conn = sqlite3.connect("biometric.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            device TEXT,
            image_path TEXT,
            fingerprint BLOB,
            latitude REAL,
            longitude REAL,
            city TEXT,
            country TEXT,
            address TEXT
        )
    """)

    conn.commit()
    conn.close()


def save_to_db(name, device, image_path, fingerprint_data,
               lat, lon, city, country, address):

    conn = sqlite3.connect("biometric.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users
        (name, device, image_path, fingerprint, latitude, longitude, city, country, address)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, device, image_path, fingerprint_data,
          lat, lon, city, country, address))

    conn.commit()
    conn.close()


# =========================
# LOCATION
# =========================
def get_location():
    try:
        res = requests.get("http://ip-api.com/json/")
        data = res.json()

        lat = data.get("lat")
        lon = data.get("lon")
        city = data.get("city")
        region = data.get("regionName")
        country = data.get("country")

        address = f"{city}, {region}, {country}"

        return lat, lon, city, country, address
    except:
        return None, None, None, None, None


# =========================
# CAPTURE
# =========================
def capture_fingerprint(counter):
    image_path = os.path.join(BASE_IMAGE_PATH, f"fingerprint_{counter}.bmp")

    subprocess.run([EXE_PATH, image_path])

    for _ in range(15):
        if os.path.exists(image_path):
            with open(image_path, "rb") as f:
                return image_path, f.read()
        time.sleep(0.2)

    return None, None


# =========================
# UI
# =========================
class BiometricKYCApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Biometric Scanner")
        self.root.geometry("420x620")
        self.root.configure(bg="white")

        self.capture_count = 1

        tk.Label(root, text="Biometric Scanner",
                 font=("Arial", 18, "bold"),
                 bg="white").pack(pady=10)

        tk.Label(root, text="Enter Name:", bg="white").pack()
        self.name_entry = tk.Entry(root, width=30)
        self.name_entry.pack(pady=5)

        self.image_label = tk.Label(root, bg="white")
        self.image_label.pack(pady=20)

        self.status = tk.Label(root, text="", bg="white")
        self.status.pack()

        self.location_label = tk.Label(root, text="", bg="white", fg="blue")
        self.location_label.pack()

        self.address_label = tk.Label(root, text="", bg="white", fg="purple", wraplength=350)
        self.address_label.pack(pady=5)

        tk.Button(root,
                  text="Capture Fingerprint",
                  bg="black",
                  fg="white",
                  command=self.capture).pack(pady=10)

    def capture(self):
        name = self.name_entry.get().strip()

        if not name:
            self.status.config(text="Enter name first ❌", fg="red")
            return

        self.status.config(text="Capturing... Place finger", fg="blue")
        self.root.update_idletasks()

        image_path, data = capture_fingerprint(self.capture_count)

        if data and image_path:
            try:
                # Show image
                img = Image.open(image_path)
                img = img.resize((200, 250))
                img_tk = ImageTk.PhotoImage(img)

                self.img_tk = img_tk
                self.image_label.config(image=self.img_tk)

                # Get location
                lat, lon, city, country, address = get_location()

                # Save to DB
                save_to_db(name, "Mantra", image_path, data,
                           lat, lon, city, country, address)

                # UI updates
                self.status.config(text=f"Saved Capture #{self.capture_count} ✅", fg="green")

                if lat and lon:
                    self.location_label.config(text=f"Lat: {lat}, Lon: {lon}")
                    self.address_label.config(text=f"{city}, {country}\n{address}")
                else:
                    self.location_label.config(text="Location not available")
                    self.address_label.config(text="")

                self.capture_count += 1

            except Exception as e:
                self.status.config(text=f"Error: {str(e)}", fg="red")

        else:
            self.status.config(text="Capture failed ❌", fg="red")


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    create_table()

    root = tk.Tk()
    app = BiometricKYCApp(root)
    root.mainloop()