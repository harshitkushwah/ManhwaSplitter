import os
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
import cv2

from utils import (
    load_image,
    get_image_files,
    save_webp,
)

from detector import find_panel_gaps

from config import (
    INPUT_FOLDER,
    OUTPUT_FOLDER,
    MIN_PANEL_HEIGHT,
    WEBP_QUALITY,
)


def save_panels(image, gaps, output_folder, start_number):

    panel_number = start_number

    panel_start = 0

    pending_small = None

    for gap_start, gap_end in gaps:

        panel = image[panel_start:gap_start]

        if panel.shape[0] < MIN_PANEL_HEIGHT:

            if pending_small is None:

                pending_small = panel

            else:

                pending_small = cv2.vconcat(
                    [pending_small, panel]
                )

        else:

            if pending_small is not None:

                panel = cv2.vconcat(
                    [pending_small, panel]
                )

                pending_small = None

            filename = f"{panel_number:04d}.webp"

            save_webp(
                panel,
                os.path.join(output_folder, filename),
                WEBP_QUALITY
            )

            print(f"Saved {filename}")

            panel_number += 1

        panel_start = gap_end

    panel = image[panel_start:]

    if pending_small is not None:

        panel = cv2.vconcat(
            [pending_small, panel]
        )

    if panel.shape[0] > 0:

        filename = f"{panel_number:04d}.webp"

        save_webp(
            panel,
            os.path.join(output_folder, filename),
            WEBP_QUALITY
        )

        print(f"Saved {filename}")

        panel_number += 1

    return panel_number


def natural_key(value):
    """Sort chapter/page names naturally (2 before 10)."""
    return [int(part) if part.isdigit() else part.casefold()
            for part in re.split(r"(\d+)", str(value))]


def get_archive_images(archive_path, extract_root, unique_folder=None):
    """Extract one CBZ safely and return its image paths in natural order."""
    archive_path = Path(archive_path)
    chapter_folder = Path(extract_root) / (unique_folder or archive_path.stem)
    chapter_folder.mkdir(parents=True, exist_ok=True)
    supported = (".png", ".jpg", ".jpeg", ".webp")

    with zipfile.ZipFile(archive_path, "r") as archive:
        members = [m for m in archive.infolist()
                   if not m.is_dir() and Path(m.filename).suffix.lower() in supported]
        members.sort(key=lambda item: natural_key(item.filename))
        for member in members:
            # Ignore absolute paths and traversal entries in untrusted archives.
            relative = Path(member.filename.replace("\\", "/"))
            if relative.is_absolute() or ".." in relative.parts:
                continue
            target = chapter_folder / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)

    images = [str(path) for path in chapter_folder.rglob("*")
              if path.is_file() and path.suffix.lower() in supported]
    return sorted(images, key=natural_key)


def choose_cbz_files():
    """Use the standard file picker without introducing a GUI dependency."""
    root = tk.Tk()
    root.withdraw()
    try:
        paths = filedialog.askopenfilenames(
            title="Select CBZ Chapters",
            filetypes=[("CBZ Files", "*.cbz")]
        )
    finally:
        root.destroy()
    if paths:
        return sorted(paths, key=lambda path: natural_key(Path(path).name))

    # The optimizer emits a shared folder of JPEG strips, so allow that folder
    # to be consumed directly without manually copying files into Input.
    root = tk.Tk()
    root.withdraw()
    try:
        selected_folder = filedialog.askdirectory(
            title="Select a folder of strip images (Cancel to use Input)"
        )
    finally:
        root.destroy()
    return ["__IMAGE_FOLDER__" + selected_folder] if selected_folder else []


def process_image_files(image_files, output_folder, panel_number=1):
    total = len(image_files)
    for index, image_path in enumerate(image_files, start=1):
        print("-" * 50)
        print(f"[{index}/{total}] Processing {os.path.basename(image_path)}")
        image = load_image(image_path)
        try:
            gaps = find_panel_gaps(image)
            print(f"Detected {len(gaps)} gaps")
            panel_number = save_panels(image, gaps, output_folder, panel_number)
        finally:
            del image
    return panel_number


def main():
    # Default workflow: automatically process strip images placed in Input/
    # and save the resulting WebP panels in Output/.
    os.makedirs(INPUT_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    input_images = sorted(get_image_files(INPUT_FOLDER), key=natural_key)
    if input_images:
        print(f"Found {len(input_images)} strip image(s) in '{INPUT_FOLDER}'.")
        process_image_files(input_images, OUTPUT_FOLDER, panel_number=1)
        print("-" * 50)
        print(f"Finished successfully. Cut images are in '{OUTPUT_FOLDER}'.")
        return

    # Keep multi-CBZ support as a fallback when Input/ has no images.
    print(f"No supported images found in '{INPUT_FOLDER}'.")
    print("Select CBZ chapter files, or choose a folder containing strip images.")
    cbz_files = choose_cbz_files()

    if cbz_files and cbz_files[0].startswith("__IMAGE_FOLDER__"):
        selected_folder = cbz_files[0][len("__IMAGE_FOLDER__"):]
        image_files = sorted(get_image_files(selected_folder), key=natural_key)
        if not image_files:
            print(f"No supported images found in {selected_folder}.")
            return
        process_image_files(image_files, OUTPUT_FOLDER, panel_number=1)
        print(f"Finished processing strip images. Cut images are in '{OUTPUT_FOLDER}'.")
        return

    if cbz_files:
        with tempfile.TemporaryDirectory(prefix="manhwa_splitter_") as temp_root:
            total = len(cbz_files)
            for index, cbz_path in enumerate(cbz_files, start=1):
                chapter_name = Path(cbz_path).stem
                chapter_output = os.path.join(OUTPUT_FOLDER, chapter_name)
                if os.path.exists(chapter_output):
                    suffix = 2
                    while os.path.exists(f"{chapter_output}_{suffix}"):
                        suffix += 1
                    chapter_output = f"{chapter_output}_{suffix}"
                os.makedirs(chapter_output, exist_ok=True)
                print(f"\n[{index}/{total}] Extracting chapter: {chapter_name}")
                try:
                    image_files = get_archive_images(
                        cbz_path, temp_root,
                        unique_folder=f"{index}_{chapter_name}"
                    )
                    if not image_files:
                        print(f"No supported images found in {chapter_name}; skipping.")
                        continue
                    process_image_files(image_files, chapter_output, panel_number=1)
                except Exception as exc:
                    print(f"ERROR processing {chapter_name}: {exc}")
            print("-" * 50)
            print("Finished processing selected CBZ files.")
        return

    print(f"Input folder '{INPUT_FOLDER}' is empty. Add the Optimizer's strip images there and run again.")


if __name__ == "__main__":
    main()
