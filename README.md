# ManhwaSplitter

A Python application that automatically detects and splits long manhwa/webtoon strip images into individual WebP panels.

## Default workflow

1. Run `python split.py`.
2. Put the strip images (for example, the `.jpg` strips created by CBZ to PDF Optimizer) in the `Input` folder beside `split.py`.
3. The application automatically processes the images in natural filename order and saves the cut WebP panels to `Output`.
4. The `Input` and `Output` folders are created automatically if missing.

If `Input` is empty, the app offers a file picker for selecting multiple CBZ chapters, or a folder picker for another strip-image folder.

## Install and run

```bash
pip install -r requirements.txt
python split.py
```

## Notes

The existing panel-gap detection and cutting logic is retained. Output from direct CBZ processing is separated by chapter to avoid name collisions.
