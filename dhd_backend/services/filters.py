# /services/filters.py
import cv2
import numpy as np
import math

def apply_clahe(image):
    # Dynamically calculate frame contrast
    std_contrast = np.std(image)
    # Increase the clip limit for very low-contrast (hazy/flat) frames
    adaptive_clip = 4.0 if std_contrast < 40 else 2.0

    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(
        clipLimit=adaptive_clip,
        tileGridSize=(8, 8)
    )

    l = clahe.apply(l)

    return cv2.cvtColor(
        cv2.merge((l, a, b)),
        cv2.COLOR_LAB2BGR
    )


def apply_gaussian(image):
    return cv2.GaussianBlur(image, (5, 5), 0)


def apply_sharpen(image):
    # Fast unsharp mask: amplifies original details by subtracting minor blur
    blurred = cv2.GaussianBlur(image, (3, 3), 0)
    return cv2.addWeighted(image, 1.5, blurred, -0.5, 0)


def apply_gamma(image):
    # Dynamically calculate frame brightness
    mean_brightness = np.mean(image)
    # Clamp to prevent division by zero or log of zero errors
    safe_brightness = max(1.0, min(mean_brightness, 254.0))

    # Target a mid-tone brightness of roughly 127
    adaptive_gamma = math.log(0.5) / math.log(safe_brightness / 255.0)
    # Clamp extreme gamma adjustments so it doesn't blow out the image
    adaptive_gamma = max(0.5, min(adaptive_gamma, 2.5))

    invGamma = 1.0 / adaptive_gamma
    table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    return cv2.LUT(image, table)


def apply_bilateral(image):
    return cv2.bilateralFilter(
        image,
        d=9,
        sigmaColor=75,
        sigmaSpace=75
    )


def apply_dehaze(image):
    """
    Applies a fast dehazing effect using a simplified Dark Channel Prior approach.
    """
    img_float = image.astype('float64') / 255.0

    dark_channel = np.min(img_float, axis=2)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    dark_channel = cv2.erode(dark_channel, kernel)

    num_pixels = dark_channel.size
    num_brightest = max(int(num_pixels * 0.001), 1)

    flat_dark = dark_channel.flatten()
    indices = np.argsort(flat_dark)[-num_brightest:]

    flat_img = img_float.reshape(num_pixels, 3)
    atmosphere = np.mean(flat_img[indices], axis=0)

    omega = 0.95
    transmission = 1.0 - omega * cv2.erode(np.min(img_float / atmosphere, axis=2), kernel)
    transmission = np.maximum(transmission, 0.1)

    dehazed = np.zeros(img_float.shape)
    for channel in range(3):
        dehazed[:, :, channel] = (img_float[:, :, channel] - atmosphere[channel]) / transmission + atmosphere[channel]

    dehazed = np.clip(dehazed * 255, 0, 255).astype('uint8')

    return dehazed


def preprocess_image(image, selected_filters):
    processed = image.copy()

    for filter_name in selected_filters:
        func = FILTERS.get(filter_name)
        if func is not None:
            processed = func(processed)

    return processed


FILTERS = {
    "sharpen": apply_sharpen,
    "clahe": apply_clahe,
    "gamma-correction": apply_gamma,
    # "gaussian-blur": apply_gaussian,
    "bilateral-filter": apply_bilateral,
    "dehaze": apply_dehaze,
}
