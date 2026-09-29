"""Flask Backend — AI Room Detector

วิธีรัน: pip install flask flask-cors ultralytics opencv-python numpy
         python app.py
จากนั้นเปิด browser → http://localhost:5000
"""

import os
import gdown
import traceback
import uuid
import cv2
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import numpy as np
from ultralytics import YOLO

app = Flask(__name__, static_folder=".")
CORS(app)

# ── โหลด model ──
MODEL_PATH = "best.pt"

# ถ้ายังไม่มีไฟล์โมเดลในเซิร์ฟเวอร์ ให้ดาวน์โหลดจาก Google Drive
if not os.path.exists(MODEL_PATH):
    print("⏳ กำลังดาวน์โหลดไฟล์ Model จาก Google Drive...")
    DRIVE_FILE_ID = "1R0UIn9J2m3G6Ikdi4JCupqnvIEaMCKnW"
    url = f"https://drive.google.com/uc?id={DRIVE_FILE_ID}"
    gdown.download(url, MODEL_PATH, quiet=False)

try:
    model = YOLO(MODEL_PATH)
    print(f"✅ โหลด model สำเร็จ: {MODEL_PATH}")
except Exception as e:
    print(f"⚠️ โหลด model ไม่ได้: {e}")
    model = None

MIN_AREA_PIXELS = 500
METERS_PER_PIXEL = 0.025
CONF_THRESHOLD = 0.30

RESULTS_DIR = "results"
os.makedirs(RESULTS_DIR, exist_ok=True)

PALETTE = [
    (255, 99, 71),
    (100, 149, 237),
    (144, 238, 144),
    (255, 165, 0),
    (218, 112, 214),
    (64, 224, 208),
    (255, 215, 0),
    (135, 206, 235),
    (255, 182, 193),
    (152, 251, 152),
    (173, 216, 230),
    (255, 222, 173),
]


def bgr_to_hex(bgr):
  b, g, r = int(bgr[0]), int(bgr[1]), int(bgr[2])
  return f"#{r:02x}{g:02x}{b:02x}"


@app.route("/")
def index():
  return send_from_directory(".", "index.html")


@app.route("/results/<filename>")
def result_image(filename):
  return send_from_directory(RESULTS_DIR, filename)


@app.route("/analyze", methods=["POST"])
def analyze():
  if model is None:
    return jsonify({"error": "Model ยังไม่ได้โหลด — ตรวจสอบ MODEL_PATH"}), 500

  if "image" not in request.files:
    return jsonify({"error": "ไม่พบไฟล์ image"}), 400

  try:
    file_bytes = np.frombuffer(request.files["image"].read(), dtype=np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    if image is None:
      return jsonify({"error": "ไม่สามารถอ่านภาพได้"}), 400

    conf_thresh = float(request.form.get("conf", CONF_THRESHOLD))
    mpp = float(request.form.get("scale", METERS_PER_PIXEL))
    min_area = float(request.form.get("minArea", MIN_AREA_PIXELS))

    overlay = image.copy()
    results = model(image, conf=conf_thresh, verbose=False)

    rooms = []
    room_id = 1

    for r in results:
      if r.masks is None:
        continue

      masks = r.masks.xy
      confs = (
          r.boxes.conf.cpu().numpy() if r.boxes is not None else [1.0] * len(masks)
      )

      for i, mask in enumerate(masks):
        if len(mask) < 3:
          continue

        if i < len(confs) and confs[i] < conf_thresh:
          continue

        poly = np.array(mask, dtype=np.int32)
        area_pixels = cv2.contourArea(poly)
        if area_pixels < min_area:
          continue

        epsilon = 0.01 * cv2.arcLength(poly, True)
        approx = cv2.approxPolyDP(poly, epsilon, True)
        pts = approx.reshape(-1, 2)

        area_m2 = round(area_pixels * (mpp**2), 2)
        color = PALETTE[(room_id - 1) % len(PALETTE)]

        cv2.polylines(image, [pts], True, color, 2)
        cv2.fillPoly(overlay, [pts], color)

        M = cv2.moments(pts)
        if M["m00"] != 0:
          cx = int(M["m10"] / M["m00"])
          cy = int(M["m01"] / M["m00"])
        else:
          cx = int(np.mean(pts[:, 0]))
          cy = int(np.mean(pts[:, 1]))

        cv2.putText(
            image,
            f"Room {room_id}",
            (max(0, cx - 20), max(15, cy)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2,
        )
        cv2.putText(
            image,
            f"{area_m2} m2",
            (max(0, cx - 20), max(30, cy + 16)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            (220, 220, 220),
            1,
        )

        rooms.append({
            "room_id": room_id,
            "area_m2": area_m2,
            "area_px": int(area_pixels),
            "confidence": round(float(confs[i]), 3) if i < len(confs) else 1.0,
            "centroid": [cx, cy],
            "corners": pts.tolist(),
            "color": bgr_to_hex(color),
        })

        room_id += 1

    final = cv2.addWeighted(overlay, 0.25, image, 0.75, 0)
    filename = f"{uuid.uuid4().hex}.png"
    filepath = os.path.join(RESULTS_DIR, filename)
    cv2.imwrite(filepath, final)

    total_m2 = round(sum(r["area_m2"] for r in rooms), 2)

    return jsonify({
        "rooms": rooms,
        "total_area_m2": total_m2,
        "room_count": len(rooms),
        "result_image": f"/results/{filename}",
    })

  except Exception as e:
    print("❌ เกิด Error ใน analyze:")
    traceback.print_exc()
    return jsonify({"error": str(e)}), 500




if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)