# 📖 AutoDent PRO — Complete Technical Documentation & Backend Optimization Guide

This document provides a comprehensive technical breakdown of the **AutoDent PRO** Vehicle Damage Inspection System, including architecture, API specifications, data contracts, and detailed instructions for backend modifications when damages are not detected.

---

## 📑 Index
1. [System Overview & Architecture](#1-system-overview--architecture)
2. [Dataset & Model Specification](#2-dataset--model-specification)
3. [Backend Pipeline Breakdown](#3-backend-pipeline-breakdown)
4. [Frontend Architecture & UI Features](#4-frontend-architecture--ui-features)
5. [API Specification & Contract](#5-api-specification--contract)
6. [Why Detections Might Be Missed (Root Causes)](#6-why-detections-might-be-missed-root-causes)
7. [Step-by-Step Backend Modifications for Missed Detections](#7-step-by-step-backend-modifications-for-missed-detections)
8. [Production Deployment Recommendations](#8-production-deployment-recommendations)

---

## 1. System Overview & Architecture

AutoDent PRO is a full-stack, AI-powered vehicle inspection tool. It allows auto insurers, fleet managers, bodyshops, and car owners to upload or capture photos of damaged vehicles and instantly receive:
- Exact bounding box coordinates and classification of damages.
- Visual vector overlays and baked OpenCV image annotations.
- Surface damage area percentages relative to the vehicle panel.
- Aggregate physical damage severity scoring (0–100).
- Instant downloadable text inspection certificates.

```
+-------------------------------------------------------------+
|                     CLIENT APPLICATION                      |
|  - React 18 + Vite (SPA)                                    |
|  - Live WebRTC Camera Capture                               |
|  - SVG Vector Overlays / OpenCV Previews                    |
|  - Inspection Certificate Exporter                          |
+------------------------------+------------------------------+
                               |
                   HTTP POST /predict (Multipart)
                               |
+------------------------------v------------------------------+
|                    FLASK BACKEND SERVER                     |
|  - CORS Middleware & Request Validation                     |
|  - PIL & OpenCV Image Decoding & Normalization              |
|  - YOLOv8 PyTorch Inference Pipeline (weights/best.pt)      |
|  - Class-Aware Non-Maximum Suppression (cv2.dnn.NMSBoxes)   |
|  - OpenCV Damage Annotation Engine & Base64 Encoder         |
+-------------------------------------------------------------+
```

---

## 2. Dataset & Model Specification

The AI model is an Ultralytics **YOLOv8** object detection network trained on annotated vehicle damage datasets.

### Model Weights Location
`backend/weights/best.pt`

### Target Damage Classes & Color Codes
| Index | Class Name | OpenCV Color (BGR) | UI Hex Color | Description |
|---|---|---|---|---|
| `0` | **dent** | `(248, 189, 56)` | `#38bdf8` | Indentations, dings, sheet metal compressions |
| `1` | **scratch** | `(11, 158, 245)` | `#f59e0b` | Paint abrasions, scrape lines, clear-coat scuffs |
| `2` | **crack** | `(94, 63, 244)` | `#f43f5e` | Windshield fissures, bumper/fender cracks |
| `3` | **glass shatter** | `(252, 132, 192)` | `#c084fc` | Webbed breaks, shattered window panels |
| `4` | **lamp broken** | `(71, 224, 253)` | `#fde047` | Broken headlight, taillight, or turn signal lenses |
| `5` | **tire flat** | `(153, 211, 52)` | `#34d399` | Deflated tire, punctured sidewall, exposed rims |

---

## 3. Backend Pipeline Breakdown

The backend request cycle executes the following stages:

1. **Request Intake**:
   Receives raw image bytes via `UploadFile` along with form hyperparameters:
   - `conf`: Confidence threshold (default `0.35`).
   - `iou`: Intersection-over-Union threshold (default `0.45`).
   - `imgsz`: Input image resize dimension (default `1024`).
   - `augment`: Test-Time Augmentation boolean flag.
   - `classes`: Target class filter list.

2. **Image Ingestion & Conversion**:
   Decodes image stream via `PIL.Image.open(BytesIO(contents)).convert("RGB")` and transforms to NumPy array `(H, W, 3)`.

3. **YOLO Model Prediction**:
   Executes PyTorch GPU/CPU inference:
   ```python
   results = model.predict(
       source=image_np,
       imgsz=imgsz,
       conf=conf,
       iou=iou,
       device=DEVICE,
       augment=augment,
       verbose=False
   )
   ```

4. **Coordinate Normalization & Clamping**:
   - Clamps bounding box corners `[x1, y1, x2, y2]` to image boundaries `[0..W, 0..H]`.
   - Filters out degenerate boxes (`width < 2px` or `height < 2px`).
   - Calculates bounding box pixel area and percentage of image area:
     $$\text{area\_percentage} = \frac{\text{width} \times \text{height}}{\text{total\_image\_area}} \times 100$$

5. **Class-Aware Non-Maximum Suppression (NMS)**:
   Groups detections by class ID and applies `cv2.dnn.NMSBoxes` to prevent multiple overlapping boxes from flagging the same damage spot.

6. **Image Annotation**:
   Draws semi-transparent bounding boxes (`alpha=0.15`), solid corner brackets, and high-contrast text badges using OpenCV. Encodes to JPEG Base64 (`quality=92`).

7. **JSON Payload Assembly**:
   Returns detected damage objects array, count, original image dimensions, and Base64-encoded annotated image.

---

## 4. Frontend Architecture & UI Features

- **Dynamic Preset Modes**:
  - **Balanced Mode**: `conf: 0.35`, `imgsz: 1024` — Standard for high-quality photos.
  - **Sensitive (Micro-Damage) Mode**: `conf: 0.22`, `imgsz: 1024` — Detects faint scratches and shallow dings.
  - **Strict Mode**: `conf: 0.50`, `imgsz: 1024` — Minimizes false positives for official insurance claims.
- **Three-Way View Switcher**:
  - `vector`: Crisp SVG vectors drawn over original image, enabling hover sync with damage cards.
  - `annotated`: OpenCV baked image preview.
  - `raw`: Clean input image without overlays.
- **Severity Scoring Formula**:
  $$\text{Score} = \min(100, (\text{Critical Count} \times 25) + (\text{Damage Count} \times 8) + \min(40, \text{Total Area \%} \times 4))$$

---

## 5. API Specification & Contract

### Endpoint: `POST /predict`

#### Request (multipart/form-data):
| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `file` | Binary File | Yes | - | Supported formats: `.jpg`, `.jpeg`, `.png`, `.webp` |
| `conf` | Float | No | `0.35` | Minimum confidence score (0.01 – 1.0) |
| `iou` | Float | No | `0.45` | IoU threshold for NMS |
| `imgsz` | Integer | No | `1024` | Input resolution for model |
| `augment` | Boolean | No | `false` | Enable Test-Time Augmentation (TTA) |
| `classes` | String | No | `null` | JSON array or comma-separated class list |

#### Response (`application/json`):
```json
{
  "success": true,
  "filename": "car_scratch.jpg",
  "image_dimensions": {
    "width": 1920,
    "height": 1080
  },
  "parameters": {
    "conf": 0.35,
    "iou": 0.45,
    "imgsz": 1024,
    "augment": false,
    "allowed_classes": ["dent", "scratch", "crack", "glass shatter", "lamp broken", "tire flat"]
  },
  "detections": [
    {
      "class_id": 1,
      "class_name": "scratch",
      "confidence": 0.8421,
      "confidence_percent": 84.2,
      "bbox": {
        "x1": 420.5,
        "y1": 310.2,
        "x2": 680.0,
        "y2": 395.4
      },
      "width": 259.5,
      "height": 85.2,
      "area": 22109.4,
      "area_percentage": 1.07
    }
  ],
  "detection_count": 1,
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQ..."
}
```

---

## 6. Why Detections Might Be Missed (Root Causes)

If the AI fails to find damage or produces 0 detections on a damaged car photo, it is usually caused by one of the following factors:

1. **Overly High Confidence Threshold (`conf`)**:
   - Small scratches, minor door dings, or cracks under dark lighting often have confidence scores in the range `0.15 – 0.30`.
   - If the backend threshold is set to `0.35` or `0.50`, these valid detections are discarded.

2. **Smartphone EXIF Orientation Flag**:
   - Photos taken with iPhone or Android contain EXIF metadata specifying rotation (e.g., 90° or 270°).
   - Standard PIL or OpenCV loaders without EXIF handling load the image rotated sideways or upside-down. Since YOLO is trained on upright cars, rotated cars yield 0 detections.

3. **Lighting, Glare & Low Contrast**:
   - Car clear coats reflect sunlight, sky, or indoor fluorescent lighting, which washes out subtle scratches.
   - Without dynamic contrast enhancement, the model features cannot resolve faint paint abrasions.

4. **Resolution Mismatch & Scale Discrepancy**:
   - High-resolution photos (4K/12MP) scaled down to 640px cause micro-scratches (e.g., 5px wide) to shrink down to less than 1 pixel.

5. **Aggressive NMS Suppression**:
   - If multiple damages are close together (e.g. a dent surrounded by multiple scratches), an overly strict IoU threshold or non-class-aware NMS may suppress valid detections.

6. **Out-of-Distribution Angles or Blurry Images**:
   - Severe motion blur or out-of-focus camera captures degrade edge features.

---

## 7. Step-by-Step Backend Modifications for Missed Detections

Here are concrete code implementations to improve detection recall in `backend/main.py`:

### Enhancement 1: Auto-Correct Mobile EXIF Image Rotation
Add `ImageOps.exif_transpose` to ensure camera pictures are always upright:

```python
from PIL import Image, ImageOps

# In the predict() function:
contents = await file.read()
pil_image = Image.open(BytesIO(contents))
# Auto-rotate based on EXIF tag from smartphones
pil_image = ImageOps.exif_transpose(pil_image).convert("RGB")
image_np = np.array(pil_image)
```

---

### Enhancement 2: Multi-Pass Adaptive Fallback Threshold
If initial inference with user `conf` (e.g. 0.35) yields 0 detections, automatically fall back to a sensitive secondary scan (e.g. `conf = 0.18` or `0.15`):

```python
# Pass 1: Standard inference
results = model.predict(
    source=image_np,
    imgsz=imgsz,
    conf=conf,
    iou=iou,
    device=DEVICE,
    augment=augment,
    verbose=False
)

# Pass 2: Automatic Fallback if 0 detections found
if (results[0].boxes is None or len(results[0].boxes) == 0) and conf > 0.20:
    fallback_conf = max(0.15, conf * 0.55)
    results = model.predict(
        source=image_np,
        imgsz=imgsz,
        conf=fallback_conf,
        iou=iou,
        device=DEVICE,
        augment=True, # enable TTA on fallback
        verbose=False
    )
```

---

### Enhancement 3: Contrast Enhancement Preprocessing (CLAHE)
For images with shadows, glare, or low light, apply Contrast Limited Adaptive Histogram Equalization to the luminance channel:

```python
def enhance_damage_contrast(image_rgb: np.ndarray) -> np.ndarray:
    """
    Applies CLAHE on the L channel in LAB color space to reveal faint scratches & dents.
    """
    lab = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    
    enhanced_lab = cv2.merge((cl, a, b))
    return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2RGB)
```

---

### Enhancement 4: Image Quality Diagnostics (Blur & Exposure Check)
Return diagnostic feedback in the API response if the uploaded photo has issues like blurriness or extreme darkness:

```python
def analyze_image_quality(image_rgb: np.ndarray) -> dict:
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    # Variance of Laplacian for blur detection (< 100 indicates blurry image)
    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
    # Mean brightness (0-255, < 40 is too dark, > 220 is overexposed)
    brightness = float(np.mean(gray))
    
    warnings = []
    if blur_score < 80.0:
        warnings.append("Image appears blurry or out of focus. Damage edges may be missed.")
    if brightness < 40.0:
        warnings.append("Image is underexposed/too dark. Consider taking a photo in better lighting.")
    elif brightness > 225.0:
        warnings.append("Image has strong glare or overexposure.")

    return {
        "blur_score": round(blur_score, 2),
        "brightness": round(brightness, 2),
        "is_blurry": blur_score < 80.0,
        "warnings": warnings
    }
```

---

### Enhancement 5: High-Resolution Sliding Window / Tiling (SAHI Pattern)
For high-res images containing tiny scratches, slicing the image into overlapping sub-windows boosts detection without losing resolution:

```python
def slice_and_infer(model, image_np, tile_size=640, overlap=0.2, conf=0.25):
    h, w = image_np.shape[:2]
    step = int(tile_size * (1 - overlap))
    all_boxes = []
    
    for y in range(0, max(1, h - tile_size + 1), step):
        for x in range(0, max(1, w - tile_size + 1), step):
            tile = image_np[y:y+tile_size, x:x+tile_size]
            res = model.predict(tile, conf=conf, verbose=False)[0]
            if res.boxes:
                for box in res.boxes:
                    xyxy = box.xyxy[0].tolist()
                    # Offset back to global coordinates
                    all_boxes.append({
                        "cls": int(box.cls[0].item()),
                        "conf": float(box.conf[0].item()),
                        "xyxy": [xyxy[0] + x, xyxy[1] + y, xyxy[2] + x, xyxy[3] + y]
                    })
    return all_boxes
```

---

## 8. Production Deployment Recommendations

1. **CUDA GPU Acceleration**:
   Ensure PyTorch with CUDA is installed (`pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121`) for ~15ms inference latency.
2. **Batch & Asynchronous Processing**:
   For multi-image batch inspections (e.g. 360° vehicle walkaround), implement `asyncio` or Celery task queues.
3. **Continuous Fine-Tuning**:
   Log low-confidence edge cases (`0.15 < conf < 0.30`) to an active-learning annotation queue to regularly re-train `best.pt`.
