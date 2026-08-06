import os
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


def main():

    os.makedirs(
        OUTPUT_FOLDER,
        exist_ok=True
    )

    image_files = get_image_files(
        INPUT_FOLDER
    )

    if not image_files:

        print("No images found.")

        return

    panel_number = 1

    for image_path in image_files:

        print("-" * 50)

        print(
            f"Processing {os.path.basename(image_path)}"
        )

        image = load_image(image_path)

        gaps = find_panel_gaps(image)

        print(
            f"Detected {len(gaps)} gaps"
        )

        panel_number = save_panels(
            image,
            gaps,
            OUTPUT_FOLDER,
            panel_number
        )

    print("-" * 50)

    print("Finished Successfully!")


if __name__ == "__main__":
    main()