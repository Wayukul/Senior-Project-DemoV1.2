# AI Room Detector — คู่มือโปรเจกต์
======================================

## วิธีรัน
```
pip install flask flask-cors ultralytics opencv-python numpy
python app.py
เปิด browser → http://localhost:5000
```

---

## โครงสร้างไฟล์
```
app.py        → Flask Backend (Python)
index.html    → Frontend (HTML + JS + Three.js)
```

---
---

# app.py — Backend (Python / Flask)

## ค่าตั้งต้น (ปรับได้)
| บรรทัด | ตัวแปร | ค่า | ความหมาย |
|--------|--------|-----|----------|
| 21 | MODEL_PATH | runs/segment/train/weights/best.pt | path ของ YOLO model ที่เทรนมา |
| 29 | MIN_AREA_PIXELS | 500 | พื้นที่ขั้นต่ำ (px²) ที่จะยอมรับ polygon |
| 30 | METERS_PER_PIXEL | 0.025 | อัตราส่วน 1px = กี่เมตร (ค่า default ถ้า frontend ไม่ส่งมา) |
| 31 | CONF_THRESHOLD | 0.30 | ค่าความมั่นใจขั้นต่ำของ YOLO (ค่า default) |

## ฟังก์ชัน
| บรรทัด | ฟังก์ชัน | หน้าที่ |
|--------|---------|--------|
| 40 | bgr_to_hex(bgr) | แปลงสี BGR (OpenCV) → HEX string (#rrggbb) ส่งให้ frontend |
| 44 | img_to_base64(img_bgr) | แปลง OpenCV image → base64 string ส่งกลับ frontend แสดงผล |
| 49 | GET / | serve ไฟล์ index.html ให้ browser |
| 54 | POST /analyze | รับภาพจาก frontend → รัน YOLO → คืนผลเป็น JSON |

## flow ของ /analyze
```
รับภาพ (multipart/form-data)
  ↓
รับค่า conf, scale, minArea จาก request (บรรทัด 68-70)
  ↓
แปลงภาพ → numpy array (OpenCV)
  ↓
รัน YOLO model (บรรทัด 72)
  ↓
วนลูปแต่ละ mask ที่ตรวจเจอ
  ├─ กรอง confidence < conf_thresh
  ├─ กรอง area < min_area
  ├─ smooth polygon ด้วย approxPolyDP
  ├─ คำนวณพื้นที่ (px² → m²)
  └─ วาด polygon + label ลงบนภาพ
  ↓
คืน JSON {rooms, total_area_m2, result_image (base64)}
```

## JSON ที่ส่งกลับ
```json
{
  "rooms": [
    {
      "room_id": 1,
      "area_m2": 12.5,
      "area_px": 20000,
      "confidence": 0.87,
      "centroid": [320, 240],
      "corners": [[x,y], [x,y], ...],
      "color": "#ff6347"
    }
  ],
  "total_area_m2": 45.0,
  "room_count": 3,
  "result_image": "data:image/png;base64,..."
}
```

---
---

# index.html — Frontend (HTML + JavaScript + Three.js)

---

## STATE VARIABLES (บรรทัด 293-302)
| บรรทัด | ตัวแปร | ความหมาย |
|--------|--------|----------|
| 293 | API | URL ของ backend = 'http://localhost:5000' |
| 294 | rooms | array ข้อมูลห้องทั้งหมดที่แก้ไขแล้ว |
| 294 | origRooms | สำเนาข้อมูลห้องตอนแรก ไว้ใช้ reset |
| 295 | selIdx | index ของห้องที่เลือกอยู่ (-1 = ไม่ได้เลือก) |
| 295 | activeCorner | index ของจุด corner ที่กำลังลาก (-1 = ไม่มี) |
| 300 | cvScale | อัตราส่วน canvas px / image px |
| 301 | isDrawing | true = กำลังวาดโซนใหม่ |
| 301 | drawPts | array จุดที่วางระหว่างวาดโซนใหม่ |
| 301 | mPos | ตำแหน่ง mouse ปัจจุบันบนภาพ [x, y] |
| 302 | snapInfo | ข้อมูล angle snap ปัจจุบัน |
| 432 | SNAP_DEG | ± องศาที่จะ snap เข้าแนวตรง (ค่า 8) |

---

## ฟังก์ชันทั้งหมด

### กลุ่ม Server
| บรรทัด | ฟังก์ชัน | หน้าที่ |
|--------|---------|--------|
| 305 | ping() | เช็คว่า backend รันอยู่ไหม ทุก 8 วินาที แสดงจุดสีเขียว/แดงที่ header |

---

### กลุ่ม File Upload
| บรรทัด | ฟังก์ชัน | หน้าที่ |
|--------|---------|--------|
| 334 | loadFile(file) | อ่านไฟล์ภาพ → แปลงเป็น base64 → แสดง preview → เปิดปุ่มวิเคราะห์ |
| 346 | clearImage() | เคลียร์ทุกอย่าง: ภาพ, ห้อง, canvas, ผลลัพธ์ |

---

### กลุ่ม Analyze (เชื่อมกับ Backend)
| บรรทัด | ฟังก์ชัน | หน้าที่ |
|--------|---------|--------|
| 363 | doAnalyze() | ส่งภาพ + ค่า settings ไปให้ /analyze → รับผล → โหลดลง canvas |

---

### กลุ่ม Canvas
| บรรทัด | ฟังก์ชัน | หน้าที่ |
|--------|---------|--------|
| 416 | initCV() | คำนวณ cvScale และตั้งขนาด canvas ให้พอดีกับ viewport |
| 479 | drawAll() | วาดทุกอย่างบน canvas: ภาพพื้นหลัง, polygon ห้อง, handle จุด, snap indicator, zone preview |

---

### กลุ่ม Angle Snap
| บรรทัด | ฟังก์ชัน | หน้าที่ |
|--------|---------|--------|
| 434 | angleSnap(mx,my,pts,cornerIdx) | เช็คว่าจุดที่ลากอยู่ใกล้แนว 0/90/180/270 องศาไหม ถ้าใช่ snap เข้าแกนอัตโนมัติ |

ค่าสำคัญ: SNAP_DEG = 8 (บรรทัด 432)
→ ถ้าเส้นที่ลากอยู่ภายใน ±8° จากแนวตรง จะ snap ทันที
→ เพิ่มได้ถึง 15-20 ถ้าอยากให้ snap ง่ายขึ้น

---

### กลุ่ม Mouse / Touch Events
| บรรทัด | ฟังก์ชัน | หน้าที่ |
|--------|---------|--------|
| 635 | cvXY(e) | แปลง mouse event coordinates → pixel coordinates บนภาพจริง |
| 640 | onDown(e) | mousedown: ถ้า isDrawing=วางจุด / ถ้าไม่=เช็ค handle hit หรือ select ห้อง |
| 677 | onMove(e) | mousemove: track mPos เสมอ / ถ้า isDrag=ลากจุด+angleSnap |
| 706 | onUp() | mouseup: จบการลาก, recalcRoom, อัปเดต JSON |

---

### กลุ่ม Helpers
| บรรทัด | ฟังก์ชัน | หน้าที่ |
|--------|---------|--------|
| 731 | ptInPoly(x,y,pts) | เช็คว่าจุด (x,y) อยู่ใน polygon ไหม (Ray casting algorithm) |
| 740 | polyArea(pts) | คำนวณพื้นที่ polygon จากจุด corners (Shoelace formula) |
| 747 | recalcRoom(idx) | คำนวณ area_px และ area_m2 ใหม่จาก corners ปัจจุบัน |
| 755 | updTotal() | อัปเดตตัวเลขรวม |
| 759 | updJson() | อัปเดต resultJson object จาก rooms ปัจจุบัน |
| 765 | updSelInfo() | อัปเดตแผงขวา แสดงข้อมูลห้องที่เลือก |

---

### กลุ่ม Room List
| บรรทัด | ฟังก์ชัน | หน้าที่ |
|--------|---------|--------|
| 775 | renderRoomList() | วาด room card ทั้งหมดในแผงซ้าย |
| 789 | selRoom(i) | เลือกห้อง index i → highlight card + วาด handle |

---

### กลุ่ม Polygon Actions
| บรรทัด | ฟังก์ชัน | หน้าที่ |
|--------|---------|--------|
| 799 | startAddZone() | เริ่มโหมดวาดโซนใหม่ (isDrawing=true) |
| 811 | finishZone() | จบโหมดวาด → สร้างห้องใหม่จาก drawPts (ต้องมี ≥3 จุด) |
| 830 | recalcRoom2(room) | คำนวณพื้นที่ห้องใหม่ที่เพิ่งวาด |
| 837 | cancelZone() | ยกเลิกการวาด → เคลียร์ drawPts, คืนปุ่มกลับปกติ |
| 847 | deleteSelectedCorner() | ลบจุด corner ที่เลือกอยู่ (activeCorner) ต้องมี ≥3 จุดเหลือ |
| 857 | resetRoom() | reset ห้องที่เลือกกลับเป็นข้อมูลตอนแรกจาก YOLO |
| 863 | deleteRoom() | ลบห้องที่เลือกออกจาก rooms array ทั้งหมด |

---

### กลุ่ม UI Utils
| บรรทัด | ฟังก์ชัน | หน้าที่ |
|--------|---------|--------|
| 874 | switchTab(t) | สลับ tab ระหว่าง "แก้ไข" กับ "ต้นฉบับ" |
| 880 | toggleJson() | เปิด/ปิด JSON raw viewer |
| 887 | dlJson() | ดาวน์โหลด JSON ที่แก้ไขแล้วเป็น .json file |
| 894 | setLoad(on) | เปิด/ปิด loading state ของปุ่มวิเคราะห์ |
| 900 | setStatus(type,msg) | แสดง status bar (info/success/error) |

---

### กลุ่ม 3D Engine (Three.js)
| บรรทัด | ฟังก์ชัน | หน้าที่ |
|--------|---------|--------|
| 912 | open3D() | เปิด 3D modal, init Three.js ถ้ายังไม่ได้ init, สร้าง 3D |
| 919 | close3D() | ปิด 3D modal |
| 921 | initThree() | สร้าง Scene, Camera, Renderer, Lights, เรียก setupOrbit3D |
| 947 | snapCorners(rList,px) | merge จุดของทุกห้องที่ใกล้กันภายใน px pixels (Union-Find) ค่าปัจจุบัน = 60px |
| 971 | straightenPolygon(pts) | แปลง edge ทุกเส้นให้ตรง 0° หรือ 90° อัตโนมัติ (วน 3 รอบ) |
| 1006 | straightenAllRooms(rList) | เรียก straightenPolygon กับทุกห้อง |
| 1013 | build3D() | สร้าง 3D: straighten → snap → wall mesh ทุกห้อง |
| 1065 | rebuild3D() | เรียก build3D() ใหม่เมื่อ user ปรับ slider |
| 1067 | setupOrbit3D() | ผูก mouse/touch events สำหรับ หมุน/เลื่อน/ซูม |
| 1082 | updOrbit() | คำนวณตำแหน่ง camera จาก theta, phi, radius |

### ค่าสำคัญใน 3D
| ตัวแปร | ค่า | บรรทัด | ความหมาย |
|--------|-----|--------|----------|
| SNAP_DEG | 8 | 432 | ± องศา angle snap ตอนลาก polygon |
| snapCorners px | 60 | 1022 | ระยะ merge กำแพง (px) เพิ่มถ้ากำแพงยังไม่ชิด |
| straightenPolygon pass | 3 | 971 | จำนวนรอบ straighten เพิ่มถ้าเส้นยังเบี้ยว |

### Pipeline สร้าง 3D (บรรทัด 1013-1065)
```
rooms (polygon จาก YOLO + user แก้ไข)
    ↓
straightenAllRooms()  → edge ทุกเส้นตรง 0°/90°
    ↓
snapCorners(60px)     → merge จุดที่ใกล้กัน
    ↓
center offset         → ย้าย origin ไปตรงกลางแปลน
    ↓
วนแต่ละห้อง:
  ├─ สร้าง wall mesh ทุก edge (BoxGeometry)
  └─ สร้าง label sprite (CanvasTexture)
    ↓
อัปเดต camera position
```

---

## Keyboard Shortcuts
| ปุ่ม | หน้าที่ |
|------|--------|
| Enter | จบการวาดโซน (ต้องมี ≥3 จุด) |
| Escape | ยกเลิกการวาดโซน / deselect ห้อง |
| Backspace | ลบจุดล่าสุดขณะวาดโซน / ลบ corner ที่เลือก |
| Delete | ลบ corner ที่เลือก |

---

## จุดที่ควรแก้ต่อ
1. Scale calibration — ให้ user วาดเส้นอ้างอิงแทนพิมพ์ตัวเลขเอง
2. Undo/Redo — ตอนนี้ถ้าลากผิดต้อง reset ทั้งห้อง
3. Export 3D — export เป็น .glb หรือ .obj
4. ชื่อห้อง — ตอนนี้แสดงแค่ Room 1, 2, 3... ไม่มีให้ตั้งชื่อจริง
5. Retrain model — แก้ปัญหา polygon ไม่ชิดกันที่ต้นเหตุ
