# Model speed benchmark

Isolates the YOLO11m model (`model/best.pt`) from the rest of the backend -
no Flask, no DB, no network - so it answers "is it the model or the backend?"

## Run it

```
cd test-model
python generate_test_images.py   # once, creates images/*.jpg (~1024px synthetic photos)
python benchmark.py              # runs everything, prints a report to the console
```

That's it - one file, one command. It writes two output files next to the
script:

- `benchmark_report.md` - the short, human-readable summary (open this first)
- `benchmark_results.json` - full raw numbers behind it

Optionally compare against what the frontend actually measured:

```
python benchmark.py --observed-seconds 20
```

This adds a line to the report saying what % of the observed latency the
model accounts for.

### Running this on the server

Copy the whole `test-model/` folder (script + `model/best.pt` + `images/`) to
the server and run the same command there - it needs no Flask app, no DB, and
no network access, only the venv (`ultralytics`, `torch`, `opencv`, `PIL`).
Device (CPU vs GPU) is auto-detected the same way `app/inference/ultralytics_adapter.py`
does, so if the server has a GPU the report will reflect that automatically -
no code changes needed.

## What it measured on this machine (CPU-only, 4 threads)

- **5 images, sequential, no network/DB: ~21.7s** - this alone accounts for
  essentially all of the ~20s seen from the frontend for 5 images.
- Per-image inference at the production setting (`imgsz=1024`) averaged
  **~3.4s/image** on CPU. Pre-processing (decode, EXIF, quality check) is
  negligible (20-80ms/image) by comparison.
- **imgsz is the single biggest lever**: 1024→512 cut inference from ~3.45s to
  ~0.77s per image (~4.5x). All three detection presets (`balanced`,
  `sensitive`, `strict` in `app/config.py`) currently hard-code `imgsz: 1024`.
- The automatic TTA fallback pass (`augment=True`, triggered when nothing is
  found at the 0.15 floor) costs ~1.8x a single pass on top of the pass that
  already ran - so an image with no obvious damage can pay for both.
- Batching all 5 images into one `predict()` call was *slower* than 5
  sequential calls on this CPU - not worth pursuing here.

## Conclusion

**The model is the bottleneck, not the backend.** CPU inference at the
configured `imgsz=1024` alone reproduces the reported ~20s for 5 images, with
no network or DB involved. Options, roughly in order of effort:

1. **Lower `MODEL_INPUT_SIZE`** (e.g. 1024 → 640) if accuracy holds up on real
   photos - biggest win for the least effort, no infra change.
2. **Run on GPU** if one is available in deployment - CPU YOLO11m at 1024 is
   inherently slow; this hardware has none (`cuda_available: false`).
3. **Process an inspection's images concurrently** (thread/process pool)
   instead of the current sequential loop in `app/tasks/inspection_job.py` -
   doesn't reduce total CPU work but cuts wall-clock time if multiple cores
   are free.
4. Re-check how often the TTA fallback actually fires on real photos - if
   it's common, that's ~1.8x cost being paid regularly.

Re-run this script after any change to see the effect before touching the
real pipeline. Note: this uses synthetic images (random shapes, no real
damage), so absolute detection counts are meaningless - only timing matters.
