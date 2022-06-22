# import all needed modules from the python standard library
try:
    import glob
    import logging
    import math
    import os
    import sys
    import time
    import datetime
    import calendar
    import re
except ModuleNotFoundError as b:
    print('ModuleNotFoundError: Missing basic libraries (required: glob, logging, math, os, sys, time, datetime, '
          'calendar, re')
    print(b)

# import additional python libraries
try:
    import gdal
    from osgeo import ogr
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import scipy
    from tqdm import tqdm
except ModuleNotFoundError as e:
    print('ModuleNotFoundError: Missing fundamental packages (required: gdal, maptlotlib.pyplot, numpy, '
          'pandas, rasterstats, scipy, tqdm')
    print(e)

"""
Author: María Fernanda Morales 

File contains direct raster calculation functions, including .tif files (using gdal) and ASCII .txt files. 
"""

def get_snap_raster_data(raster_path):
    """
    Function extracts the raster from input file and gets the basic information such as: GeoTransform, Projection,
    Extension (as an array with ulx, uly, lrx, lry) and cell resolution

    Args:
    :param raster_path: string, with path where the snap raster is located (including name and .tif extension)

    :return: tuples, with geotransform, tuple with projection, list with snap raster extension, float with cell size
    """
    raster = gdal.Open(raster_path)  # Extract raster from path
    gt = raster.GetGeoTransform()  # Get GEOTransform Data: (Top left corner X, cell size, 0, Top left corner Y, 0,
    # -cell size)
    proj = raster.GetProjection()  # Get projection of raster
    x_size = raster.RasterXSize  # Number of columns
    y_size = raster.RasterYSize  # Number of rows

    cell_size = gt[1]  # Cell resolution
    ulx = gt[0]  # Upper left X or Xmin
    lrx = ulx + cell_size * x_size  # Lower right X or Xmax

    uly = gt[3]  # Upper left Y or Ymax
    lry = uly - cell_size * y_size  # Lower right Y or Ymin

    snap_data = [ulx, uly, lrx, lry]  # Upper left X, Upper left Y, Lower right X, Lower right Y

    return gt, proj, snap_data, cell_size  # Return all 4 variables


def get_raster_data(raster_path):
    """
    Function extracts only the GEOTransform and projection from a raster file

    Args:
    :param raster_path: string, raster file path

    :return: tuples with GEOTransform and projection
    """
    raster = gdal.Open(raster_path)  # Extract raster from path
    gt = raster.GetGeoTransform()  # Get GEOTransform Data: (Top left corner X, cell size, 0, Top left corner Y, 0,
    # -cell size)
    proj = raster.GetProjection()  # Get projection of raster

    return gt, proj


def create_masked_array(array, no_data):
    """
    Function masks the no_data values in an input array, which contains the data values from a raster file

    Args:
    :param array: np.array to mask
    :param no_data: float with value to mask in array
    :return: masked np.array
    """
    mskd_array = np.ma.array(array, mask=(array == no_data))  # Mask all nodata values from the array
    if math.isnan(no_data):  # if no data value is 'nan'
        mskd_array = np.ma.masked_invalid(array)
    return mskd_array


def raster_to_array(raster_path, mask):
    """
    Function extracts raster data from input raster file and returns a non-masked array

    Args:
    :param raster_path: string, path for .tif raster file
    :param mask: boolean, which is True when user wants to mask the array and False when you want the original array

    :return: np.array or masked np.array (masking no data values)

    Note: since the input rasters could have different nodata values and different pixel precision, the nodata
    and the raster data are all changed to np.float32 to compare them with the same precision.
    """
    raster = gdal.Open(raster_path)
    band = raster.GetRasterBand(1)
    no_data = np.float32(band.GetNoDataValue())

    array = np.float32(band.ReadAsArray())
    if mask:
        masked_array = create_masked_array(array, no_data)
        return masked_array
    else:
        return array


def clip(clip_path, save_path, original_raster):
    """
    Function clips the raster to the same extents as the snap raster (same no-data cells) using gdal.warp

    Args:
    :param clip_path: string, path where the .shp file, with which to clip input raster
    :param save_path: string, file path (including extension and name) where to save the clipped raster
    :param original_raster: string, path of raster to clip to shape extent (interpolated raster)

    :return: ---
    """
    # Clip the interpolated (resampled) precipitation raster with the bounding raster shapefile from step 3
    os.system(
        "gdalwarp -cutline " + clip_path +
        " -crop_to_cutline -dstnodata -9999 -overwrite --config GDALWARP_IGNORE_BAD_CUTLINE YES "
        + original_raster + " " + save_path)

    # Calculate the info for the clipped raster
    os.system("gdalinfo -stats " + save_path)


def merge(raster_list, merge_name):
    """
    Function merges all rasters in the input 'raster list' into one single .tif raster. At intersecting points, the
    merge function gets the highest value (does not average)

    Args:
    :param raster_list: list or array with the path of every raster to merge
    :param merge_name: path with file name + extension with which to save the resulting merged raster file

    :return: ---
    """
    # Save array with raster paths to a list
    files_to_mosaic = raster_list.tolist()
    # Merge all rasters in raster_list
    g = gdal.Warp(merge_name, files_to_mosaic, format="GTiff", )
    g = None