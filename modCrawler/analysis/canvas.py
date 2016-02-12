# This module extracts image features from PNG dataurls such as image
# dimensions and number of colors. These features are then used to detect
# possible attempts of canvas fingerprinting.
#
# The main method for canvas fingerprinting detection is
# `is_canvas_false_positive` is the main method canvas fingerprinting detection
# and it checks whether the extracted image...
#     * is large enough for fingerprinting (> 16x16 px)
#     * contains at least two colors
#     * is a PNG image
# See Section 3 of the paper for details:
# https://securehomes.esat.kuleuven.be/~gacar/persistent/the_web_never_forgets.pdf
#
# Limitations:
#     * Only supports PNG images.
#     * Might result in false positives (was extremely rare in our experiments)

from __future__ import division

import png
import base64
import itertools
from io import BytesIO
import traceback
# import Image as pil
from PIL import Image as pil
import numpy as np


MIN_CANVAS_FP_WIDTH = 16
MIN_CANVAS_FP_HEIGHT = 16


def decode(dataurl, silence=False):
    """Return decoded data from a base64 data URL."""
    dec_imgdata = None
    try:
        b64_imgdata = dataurl.split(",")[1]
        dec_imgdata = base64.b64decode(b64_imgdata)
    except Exception as dec_exc:
        if not silence:
            print "Error decoding data URL: %s" % dec_exc
    return dec_imgdata


def read_img(dataurl):
    """Return PIL image object

    Or return `None` if exception.
    """
    img = None
    dec_imgdata = decode(dataurl)
    try:
        f = BytesIO(dec_imgdata)
        img = pil.open(f)
    except Exception as read_exc:
        print "Error reading image: %s" % read_exc
    return img


def img_dims(dataurl):
    """Return dimensions (width, height) of the image."""
    dims = (0, 0)
    img = read_img(dataurl)
    if img:
        dims = img.size
    return dims


def get_pypng_tuple(dataurl):
    """Return pypng tuple for the image.

    Format: (row_count, column_count, pngdata, metadata)
    """
    pypng_tuple = None
    dec_imgdata = decode(dataurl)
    try:
        pypng_reader = png.Reader(bytes=dec_imgdata)
        pypng_tuple = pypng_reader.read()
    except TypeError as inst_exc:
        print "Error creating png reader: %s" % inst_exc
    except Exception as read_exc:
        print "Error reading png data: %s" % read_exc
    return pypng_tuple


def get_img_array_from_pypng_tuple(pypng_tuple):
    """Return array representation of the image data."""
    img_arr = []
    png_props = pypng_tuple[-1]
    pngdata = pypng_tuple[2]
    row_count, column_count = png_props['size']
    channels = png_props['planes']
    try:
        img_arr = np.vstack(itertools.imap(np.uint16, pngdata))
        img_arr = np.reshape(img_arr,
                             (row_count, column_count, channels))
    except Exception as arr_exc:
        print "Error creating array from png data: %s" % arr_exc
    return img_arr


def img_color_tuples(pypng_tuple):
    """Return image array in tuples of colors."""
    png_props = pypng_tuple[-1]
    rows, columns = png_props['size']
    channels = png_props['planes']
    img_arr = get_img_array_from_pypng_tuple(pypng_tuple)
    stacked_arr = np.vstack([img_arr.T])
    return np.reshape(stacked_arr, (rows * columns, channels))


def count_distinct_colors(dataurl):
    """Return number of distinct colors in the image."""
    col_pixels = img_color_tuples(get_pypng_tuple(dataurl))
    uniq_colors = set(tuple(col_pixel) for col_pixel in col_pixels)
    return len(uniq_colors)


def is_png(dataurl):
    """Return `True` if dataURL is an image, and `False` otherwise."""
    return dataurl.startswith("data:image/png")


def is_canvas_false_positive(canvas_events):
    """Check whether this is likely to be a false positive.

    Conditions for being false positive:
        * `canvas_events` doesn't contain any ToDataURL call.
        * The dataurl element is not a PNG image.
        * Num of colors < 2 or width and height are less than minimums.
    """
    for ev in canvas_events:
        if not ev[2] == "ToDataURL":
            continue
        dataurl = ev[1]
        if not is_png(dataurl):
            return True
        w, h = img_dims(dataurl)
        colors = 2  # To not to lose a TP
        try:
            colors = count_distinct_colors(dataurl)
        except Exception as col_exc:
            print "Exception: count_distinct_colors %s\n%s" %\
                (col_exc, traceback.format_exc())
        print "Colors", colors, "WxH", w, h
        if colors > 1 and \
                (w > MIN_CANVAS_FP_WIDTH and h > MIN_CANVAS_FP_HEIGHT):
            return False
    return True
