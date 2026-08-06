import cv2
import numpy as np

from config import (
    WHITE_THRESHOLD,
    BLACK_THRESHOLD,
    GAP_COVERAGE,
    MIN_GAP_HEIGHT,
)


def preprocess(gray):
    """
    Reduce noise before gap detection.
    """

    kernel = np.ones((3, 3), np.uint8)

    gray = cv2.morphologyEx(
        gray,
        cv2.MORPH_OPEN,
        kernel
    )

    gray = cv2.GaussianBlur(
        gray,
        (3, 3),
        0
    )

    return gray


def row_scores(gray):

    height = gray.shape[0]

    scores = []

    for y in range(height):

        row = gray[y]

        white_ratio = np.mean(row >= WHITE_THRESHOLD)

        black_ratio = np.mean(row <= BLACK_THRESHOLD)

        score = max(
            white_ratio,
            black_ratio
        )

        scores.append(score)

    return np.array(scores)


def find_panel_gaps(image):

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    gray = preprocess(gray)

    scores = row_scores(gray)

    gaps = []

    inside = False

    start = 0

    for y, score in enumerate(scores):

        if score >= GAP_COVERAGE:

            if not inside:

                inside = True

                start = y

        else:

            if inside:

                end = y

                if end - start >= MIN_GAP_HEIGHT:

                    gaps.append((start, end))

                inside = False

    if inside:

        end = len(scores)

        if end - start >= MIN_GAP_HEIGHT:

            gaps.append((start, end))

    return gaps