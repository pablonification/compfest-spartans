# ♻️ SmartBin – AI-Powered Recycling System

SmartBin adalah sistem bank sampah berbasis Web, AI, dan IoT untuk memvalidasi serta memberi reward setiap kali user membuang botol plastik.

## 🏗️ Arsitektur Singkat

```
Next.js (frontend) ↔ FastAPI (backend) ↔ MongoDB
                               ↘︎ Roboflow (YOLO model)
                               ↘︎ OpenCV measurement
                               ↘︎ IoT (WebSocket → ESP32 simulator)
```

* Frontend : Next.js App Router + WebSocket client untuk status realtime.
* Backend  : FastAPI + Motor (MongoDB), layanan OpenCV, Roboflow, IoT.
* IoT      : Simulator ESP32 via WebSocket (port 8080) untuk membuka / menutup tutup tong.

---

## 🚀 Quick Start (Docker Compose)

```bash
# salin file env contoh
cp .env.example .env
# isi ROBOFLOW_API_KEY Anda

# build & start all services
docker compose up --build
```

Service yang berjalan:

| Service | Port | Deskripsi |
|---------|------|-----------|
| Frontend (Next.js) | 3000 | UI & kamera web |
| Backend (FastAPI)  | 8000 | REST API + WebSocket |
| MongoDB            | 27017 | Database |
| Redis              | 6379  | Cache (opsional) |
| IoT Simulator      | 8080 | WebSocket ESP32 virtual |

---

## ⚙️ Environment Variables

```
ROBOFLOW_API_KEY=<your_key>
MONGODB_URL=mongodb://mongodb:27017/smartbin
IOT_WS_URL=ws://iot_simulator:8080
```

`ROBOFLOW_API_KEY` bisa didapat dari halaman model [klasifikasi-per-merk/3](https://universe.roboflow.com/uascv/klasifikasi-per-merk/model/3).

---

## 📚 API Reference

### Health
```
GET /health → { "status": "healthy" }
```

### Scan Bottle
```
POST /scan
Header : Content-Type: multipart/form-data
         X-User-Email: user@example.com (optional)
Body   : image=<file>
```
Response `200 OK` (example)
```json
{
  "is_valid": true,
  "brand": "aqua",
  "confidence": 0.92,
  "diameter_mm": 64.5,
  "height_mm": 185.2,
  "volume_ml": 600.4,
  "points_awarded": 10,
  "total_points": 120
}
```

### WebSocket Realtime
```
ws://<backend-host>/ws/status
```
Client akan menerima pesan JSON setiap selesai proses scan:
```json
{
  "type": "scan_result",
  "data": {
    "brand": "aqua",
    "confidence": 0.92,
    "diameter_mm": 64.5,
    "height_mm": 185.2,
    "volume_ml": 600.4,
    "points": 10,
    "total_points": 120,
    "valid": true,
    "events": ["ACK", "lid_opened", "sensor_triggered", "lid_closed"],
    "email": "user@example.com"
  }
}
```

---

## 🤖 IoT Simulator

Simulator berada di folder `iot_simulator/` dan otomatis berjalan via docker compose.

Manual run:
```bash
cd iot_simulator
python websocket_server.py
```
Perintah JSON:
* `{ "cmd": "open" }` – membuka tutup, akan mengirim event berurutan (`lid_opened`, `sensor_triggered`, `lid_closed`).
* `{ "cmd": "close" }` – langsung menutup tutup.

---

## 🧪 Testing

```bash
docker compose exec backend pytest -q
```
Unit test berada di `backend/tests/` dan mencakup validation engine.

---

## 📄 Lisensi
MIT © 2025 SmartBin Team
