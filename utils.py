import os
import cv2
import numpy as np

SUPPORTED_FORMATS = (
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
)


def load_image(path):

    image = cv2.imread(path)

    if image is None:
        raise Exception(f"Cannot load image:\n{path}")

    return image


def get_image_files(folder):

    images = []

    for file in sorted(os.listdir(folder)):

        if file.lower().endswith(SUPPORTED_FORMATS):

            images.append(
                os.path.join(folder, file)
            )

    return images


def save_webp(image, output_path, quality):

    cv2.imwrite(
        output_path,
        image,
        [cv2.IMWRITE_WEBP_QUALITY, quality]
    )


def black_ratio(image):

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    black = np.sum(gray <= 15)

    total = gray.size

    return black / total


def white_ratio(image):

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    white = np.sum(gray >= 245)

    total = gray.size

    return white / total


def image_height(image):

    return image.shape[0]


def image_width(image):

    return image.shape[1]