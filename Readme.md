# 🧠 Biometric KYC System

A desktop-based biometric system built using Python + C# integration for capturing, storing, and managing fingerprint data with location tracking.

---

## 🚀 Features

- 🔐 Fingerprint Capture using Mantra MFS100 device
- 🖼️ Real-time fingerprint image preview
- 💾 SQLite database storage
- 📍 Location tracking (Latitude, Longitude, City, Country)
- 🧾 Multiple fingerprint capture support
- 🎨 Simple and clean UI using Tkinter

---

## 🛠️ Tech Stack

- Python (Tkinter, SQLite)
- C# (.NET Framework for device bridge)
- MANTRA MFS100 SDK
- PIL (Image Processing)
- Requests (Location API)

---

## 🧩 Project Structure
```bash
biometric-system/
│
├── main.py # Main UI application
├── fingerprint_handler.py # Capture logic
├── database.py # DB operations
├── biometric.db # Local database (ignored in Git)
│
├── MFS100Bridge/ # C# bridge for device
│ ├── Program.cs
│ ├── MFS100Bridge.csproj
│
└── .gitignore
```


---

## ⚙️ How it Works

1. Python UI triggers fingerprint capture  
2. Calls C# executable (`MFS100Bridge.exe`)  
3. Device captures fingerprint  
4. Image is saved and loaded in UI  
5. Location is fetched using IP API  
6. Data stored in SQLite DB  

---

## 📸 Demo

(Add screenshot here later)

---

## ⚠️ Note

- Requires Mantra MFS100 device & drivers installed
- Location is IP-based (approximate)

---

## 📈 Future Improvements

- Fingerprint matching system
- User dashboard
- Export data to CSV
- Google Maps integration
- Multi-device support (HamsterX, MFS110)

---

## 👩‍💻 Author

**Deveshree Bhakkad**  
B.Tech AIML | Aspiring AI/ML Engineer  