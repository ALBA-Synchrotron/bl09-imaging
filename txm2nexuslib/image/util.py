#!/usr/bin/python

"""
(C) Copyright 2018 ALBA-CELLS
Authors: Marc Rosanes, Carlos Falcon, Zbigniew Reszela, Carlos Pascual
The program is distributed under the terms of the
GNU General Public License (or the Lesser GPL).

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


import os
import h5py
import cv2
import numpy as np


def roi_parameters_selection(image, roi_size=0.5):
    """Compute ROI parameters. 'size' is given on 'tant per one' of
    the input image."""

    numrows, numcols = np.shape(image)
    # Take half of the pixels and round to the next closest even number
    width_template = numrows * roi_size
    width_template = int(np.ceil(width_template / 2.) * 2)
    height_template = numcols * roi_size
    height_template = int(np.ceil(height_template / 2.) * 2)

    # central image pixel
    central_pixel_rows = int(numrows / 2)
    central_pixel_cols = int(numcols / 2)

    row_template_from = central_pixel_rows - height_template/2
    col_template_from = central_pixel_cols - width_template/2

    roi_parameters = [row_template_from, col_template_from,
                      height_template, width_template]
    return roi_parameters


def find_mv_vector(coords_base_roi, coords_mv_roi):
    """ How much to move a projection """

    # coords_base_roi being the base template coordinates
    # (the one that will not move)
    coords_base_roi = np.array(coords_base_roi)
    coords_mv_roi = np.array(coords_mv_roi)

    # The vector should bring the image to be aligned (mv_image)
    # to the base image (fixed image)
    mv_vector = coords_base_roi - coords_mv_roi
    # print(mv_vector)
    return mv_vector


def mv_projection(image, mv_vector):
    """Move a given image by a certain amount"""
    rows = image.shape[0]
    cols = image.shape[1]
    mvr = abs(mv_vector[0])
    mvc = abs(mv_vector[1])
    ei = np.zeros((rows, cols), dtype='float32')
    pt = image

    if mv_vector[0] == 0 and mv_vector[1] == 0:
        ei[:, :] = pt[:, :]

    elif mv_vector[0] > 0 and mv_vector[1] == 0:
        ei[mvr:rows, :] = pt[0:rows - mvr, :]

    elif mv_vector[0] < 0 and mv_vector[1] == 0:
        ei[0:rows - mvr, :] = pt[mvr:rows, :]

    elif mv_vector[0] == 0 and mv_vector[1] > 0:
        ei[:, mvc:cols] = pt[:, 0:cols - mvc]

    elif mv_vector[0] == 0 and mv_vector[1] < 0:
        ei[:, 0:cols - mvc] = pt[:, mvc:cols]

    elif mv_vector[0] > 0 and mv_vector[1] > 0:
        ei[mvr:rows, mvc:cols] = pt[0:rows - mvr, 0:cols - mvc]

    elif mv_vector[0] > 0 and mv_vector[1] < 0:
        ei[mvr:rows, 0:cols - mvc] = pt[0:rows - mvr, mvc:cols]

    elif mv_vector[0] < 0 and mv_vector[1] > 0:
        ei[0:rows - mvr, mvc:cols] = pt[mvr:rows, 0:cols - mvc]

    elif mv_vector[0] < 0 and mv_vector[1] < 0:
        ei[0:rows - mvr, 0:cols - mvc] = pt[mvr:rows, mvc:cols]

    moved_image = ei
    return moved_image


def align(image_ref, image_to_align, align_method='cv2.TM_CCOEFF_NORMED',
          roi_size=0.5):
    """Align an image taking by reference another image. roi_size
    is entered as input parameter as tant per one of the original
    image size"""
    roi_parameters = roi_parameters_selection(image_ref, roi_size)
    row_tem_from = roi_parameters[0]
    col_tem_from = roi_parameters[1]
    h = roi_parameters[2]
    w = roi_parameters[3]

    template = image_ref[row_tem_from:row_tem_from+h,
                         col_tem_from:col_tem_from+w]
    #template = np.array(template)

    # template matching from cv2 only works with float 32, or
    # with uint8 (from 0 to 256)
    if isinstance(template[0][0], (np.floating, float)):
        if type(template[0][0]) != np.float32:
            template = template.astype(np.float32)
    else:
        template = template.astype(np.uint8)

    if isinstance(image_to_align[0][0], (np.floating, float)):
        if type(image_to_align[0][0]) != np.float32:
            image_to_align = image_to_align.astype(np.float32)
    else:
        image_to_align = image_to_align.astype(np.uint8)

    # Apply template Matching from cv2
    result = cv2.matchTemplate(image_to_align, template,
                               eval(align_method))
    (min_val, max_val, min_loc, max_loc) = cv2.minMaxLoc(result)

    # In openCV first indicate the columns and then the rows.
    top_left_base = (col_tem_from, row_tem_from)

    # If you are using cv2.TM_SQDIFF as comparison method,
    # minimum value gives the best match.
    if align_method in ['cv2.TM_SQDIFF', 'cv2.TM_SQDIFF_NORMED']:
        top_left_move = (min_loc[0], min_loc[1])
    else:
        top_left_move = (max_loc[0], max_loc[1])

    mv_vector = find_mv_vector(top_left_base, top_left_move)
    rows = mv_vector[1]
    cols = mv_vector[0]
    mv_vector = (rows, cols)
    # print(mv_vector)

    # Move the projection thanks to the found move vector
    aligned_image = mv_projection(image_to_align, mv_vector)

    return aligned_image, mv_vector
