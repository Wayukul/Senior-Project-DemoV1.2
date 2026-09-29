import cv2
import numpy as np
from ultralytics import YOLO

#------เลือก model มี train กับ train2------------
model = YOLO("runs/segment/train2/weights/best.pt")

#---------ใส่ชื่อไฟล์รูปที่จะทดสอบ (ถ้าไฟล์รูปอยู่ folder อื่นต้องเขียน path ให้ดี)----------------
IMAGE_PATH = "72.png"
image = cv2.imread(IMAGE_PATH)
overlay = image.copy()

results = model(IMAGE_PATH, conf=0.25)

room_id = 1

MIN_AREA_PIXELS = 500  # filter small noise

def snap_to_grid(pts, grid_size=10):
    return np.round(pts / grid_size) * grid_size

for r in results:

    if r.masks is None:
        continue

    masks = r.masks.xy
    confs = r.boxes.conf.cpu().numpy()

    for i, mask in enumerate(masks):

        # 🔹 Confidence filtering
        if confs[i] < 0.3:
            continue

        poly = np.array(mask, dtype=np.int32)

        # 🔹 Area filtering
        area_pixels = cv2.contourArea(poly)
        if area_pixels < MIN_AREA_PIXELS:
            continue

        # 🔹 Smooth polygon
        epsilon = 0.03 * cv2.arcLength(poly, True)
        approx = cv2.approxPolyDP(poly, epsilon, True)
        pts = approx.reshape(-1, 2)

        # 🔹 Draw polygon
        cv2.polylines(image, [pts], True, (0, 255, 0), 2)

        # 🔹 Fill overlay (only once!)
        cv2.fillPoly(overlay, [pts], (0, 255, 0))

        # 🔹 Compute centroid
        M = cv2.moments(pts)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
        else:
            cx, cy = pts[0]

        # 🔹 Compute area (pixels for now)
        area_text = f"{area_pixels:.0f}px"

        # 🔹 Label
        cv2.putText(
            image,
            f"Room {room_id}",
            (cx, cy),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 255),
            2
        )

        room_id += 1

# 🔹 Blend once (fix overlay issue)
pts = snap_to_grid(pts)
pts = pts.astype(int)
final = cv2.addWeighted(overlay, 0.2, image, 0.8, 0)

cv2.imshow("AI Room Detection", final)
cv2.waitKey(0)
cv2.destroyAllWindows()

cv2.imwrite("visualized_output.png", final)