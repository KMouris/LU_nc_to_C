"""File contains all needed modules and libraries, as well as the user input. """

# import all needed basic python libraries
try:
    import glob
    import os
    import sys
    import time
    import datetime
except ModuleNotFoundError as b:
    print('ModuleNotFoundError: Missing basic libraries (required: glob, os, sys, time, datetime, re, shutil, calendar')
    print(b)

# import additional python libraries
try:
    import numpy as np
    import pandas as pd
    import rasterio as rio
    from rasterio import warp as wrp
    from rasterio.enums import Resampling

    import matplotlib as math
    from osgeo import gdal
    from osgeo import ogr
    import netCDF4 as nc
except ModuleNotFoundError as b:
    print('ModuleNotFoundError: Missing fundamental packages (required: gdal, numpy, pandas, rasterio, netCDF4, mathplot')
    print(b)

"""Input variable description: 
* Decision variables 
- USELOG: boolean, which determine whether the temporary files are erased after the clipped file is finalized

* Input files:
- c_fac_file: string, path for the land cover factor correlation (.csv format)
- xyz_csv_file: string, path for the temporary csv file (.csv format)
- shape_file: string, path for the shape file (.tif format)
- snapraster_file: string, path for a sample snap file with the geoinformation (.tif format)
- lu_path: string, folder where the land use projection raster files in .nc format are
- export_folder: string, path where the export files are stored
- tmp_folder: string, path where the temporary files are stored (These will be erased if USELOG=False)
"""

USELOG = True

c_fac_file = r'C:\Users\Mouris\Desktop\glob_LU_to_C\Data\land_cover.csv'
xyz_csv_file = r'C:\Users\Mouris\Desktop\glob_LU_to_C\file.csv'
shape_file = r'C:\Users\Mouris\Desktop\glob_LU_to_C\Data\totalboundary.shp'

snapraster_file = r'C:\Users\Mouris\Desktop\glob_LU_to_C\Data\Cp_Mean_snap.tif'

lu_path = r'C:\Users\Mouris\Desktop\glob_LU_to_C\Data\nc_files'
export_folder = r'export'
tmp_folder = r'tmp'