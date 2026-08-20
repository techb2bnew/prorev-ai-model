# Model speed benchmark report

- Device used: **cpu** (CPU-only, 4 CPUs, torch 2.13.0+cpu, 4 torch threads)
- Model load time: 282 ms (once per worker process)

## Per-image timing (production settings, imgsz=1024)

| Image | Prep (ms) | Inference (ms) | TTA fallback (ms) | Detections | Total (ms) |
|---|---|---|---|---|---|
| test_1.jpg | 71 | 2760 | - | 12 | 2832 |
| test_2.jpg | 21 | 2734 | - | 7 | 2755 |
| test_3.jpg | 34 | 3935 | - | 18 | 3968 |
| test_4.jpg | 32 | 2730 | - | 3 | 2762 |
| test_5.jpg | 23 | 2980 | - | 11 | 3003 |

**Sequential total for 5 images, model only (no network/DB): 15.3s** (3064 ms/image avg)

## TTA fallback cost (augment=True, fires when nothing found at the 0.15 floor)

Single pass: 2786 ms avg  |  TTA pass: 5891 ms avg  |  **2.1x** the single pass, paid *in addition* to it.

## Inference time vs. imgsz

| imgsz | ms (avg) |
|---|---|
| 1024 | 2952 |
| 768 | 1560 |
| 640 | 1035 |
| 512 | 732 |

## Batched vs. sequential predict()

Sequential: 14530 ms  |  Batched: 19624 ms  -> batching was **slower or no better** on this hardware.

## Bottom line

If this total is close to what users see in the frontend, the model (inference at the configured imgsz, plus any TTA fallback passes) is the bottleneck, not the backend/network/DB path. Biggest levers, in order of effort: lower `MODEL_INPUT_SIZE`, run on GPU, or reduce how often the TTA fallback fires.