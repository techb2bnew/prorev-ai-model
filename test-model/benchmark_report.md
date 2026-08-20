# Model speed benchmark report

- Device used: **cpu** (CPU-only, 4 CPUs, torch 2.13.0+cpu, 4 torch threads)
- Model load time: 200 ms (once per worker process)

## Per-image timing (production settings, imgsz=1024)

| Image | Prep (ms) | Inference (ms) | TTA fallback (ms) | Detections | Total (ms) |
|---|---|---|---|---|---|
| test_1.jpg | 56 | 2807 | - | 12 | 2863 |
| test_2.jpg | 18 | 2585 | - | 7 | 2603 |
| test_3.jpg | 29 | 4021 | - | 18 | 4050 |
| test_4.jpg | 31 | 2924 | - | 3 | 2955 |
| test_5.jpg | 21 | 4300 | - | 11 | 4321 |

**Sequential total for 5 images, model only (no network/DB): 16.8s** (3358 ms/image avg)

## TTA fallback cost (augment=True, fires when nothing found at the 0.15 floor)

Single pass: 3519 ms avg  |  TTA pass: 6933 ms avg  |  **2.0x** the single pass, paid *in addition* to it.

## Inference time vs. imgsz

| imgsz | ms (avg) |
|---|---|
| 1024 | 3594 |
| 768 | 1754 |
| 640 | 1314 |
| 512 | 967 |

## Batched vs. sequential predict()

Sequential: 15862 ms  |  Batched: 20146 ms  -> batching was **slower or no better** on this hardware.

## Bottom line

If this total is close to what users see in the frontend, the model (inference at the configured imgsz, plus any TTA fallback passes) is the bottleneck, not the backend/network/DB path. Biggest levers, in order of effort: lower `MODEL_INPUT_SIZE`, run on GPU, or reduce how often the TTA fallback fires.