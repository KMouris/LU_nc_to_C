
from config import *

def extract_nc_data_to_array(nc_path):
    """
    Extracts the dataset from an nc file

    :param nc_path: string, with the path to the nc file
    :return: nc.Dataset, with the nc bands; int, with the width in longitude degree; int, with the heigh in latitude degree
    """
    ds = nc.Dataset(nc_path)
    ds_lon = ds.variables['longitude'].shape[0]
    ds_lat = ds.variables['latitude'].shape[0]

    return ds, ds_lon, ds_lat

def apply_cfac_to_array(ds, ds_lon, ds_lat, c_fac_arr):
    """
    Applys a c factor value for summer and winter based on a nc dataset that contains 32 PFT bands. Each band contains
    percent share of the land cover for each pixel. Based on the share the percentual C-factor is applied.

    :param ds: nc.Dataset, that contains land use classes (32 PFT bands)
    :param ds_lon: int, with the width in longitude degrees
    :param ds_lat: int, with the height in latitude degrees
    :param c_fac_arr: np.array, with 32 rows and 3 columns. The rows have to align to the 32 PFT bands. The columns have to have [Name/index, C-factor summer value, C-factor winter value, ...]
    :return: np.array, with c-factors (summer) accroding to lat and lon; np.array, with c-factors (winter) accroding to lat and lon
    """
    merged_raster_summer = np.zeros([ds_lat, ds_lon], dtype=float, order='C')
    merged_raster_winter = np.zeros([ds_lat, ds_lon], dtype=float, order='C')

    for pft_nr in range(len(ds.variables) - 2):
        # Apply each C-Factors share to every pixel
        r_fac_summer = ds.variables["PFT" + str(pft_nr)][:]/100 * c_fac_arr.loc[pft_nr][1]
        r_fac_winter = ds.variables["PFT" + str(pft_nr)][:]/100 * c_fac_arr.loc[pft_nr][2]

        # Data is fipped by 90° therefore rotate it
        merged_raster_summer += np.transpose(r_fac_summer)
        merged_raster_winter += np.transpose(r_fac_winter)

    return merged_raster_summer, merged_raster_winter


def export_to_tif(ds_lon, ds_lat, merged_raster, export_file):
    """
    Converts a raster array to a GEOTIFF file and exports it to the given location. The export is safed as proj=latlong
    in the cordinate system epsg:4326

    :param ds_lon: int, with the width in longitude degrees
    :param ds_lat: int, with the height in latitude degrees
    :param merged_raster: np.array, with the C-factors for each pixel
    :param export_file: str, with the new path to the GEOTIFF
    """
    # create the transform for the base matrix in lat/long projection
    transform = rio.transform.Affine.translation(-180, 90) * Affine.scale(0.05000000120000000492, -0.05000000119999999798)

    src_crs = '+proj=latlong'
    dst_crs = "EPSG:32634"
    profile = {
        'driver': 'GTiff',
        'height': ds_lat,
        'width': ds_lon,
        'count': 1,
        'dtype': str(merged_raster.dtype),
        'transform': transform
    }

    with rasterio.open(export_file, 'w', crs=dst_crs, **profile) as dst:
        dst.write(merged_raster, 1)

def transform_to_target_crs(src_file, dst_file, dst_crs):
    """
    Transformes a GEOTIFF file to the target crs system.

    :param src_file: str, with the path to the original GEOTIFF
    :param dst_file: str, with the path to the new GEOTIFF
    :param dst_crs: str, with the new crs system
    """
    with rasterio.open(src_file) as src:
        # transform for input raster
        src_transform = src.transform

        # calculate the transform matrix for the output
        dst_transform, width, height = rio.warp.calculate_default_transform(
            src.crs,  # source CRS
            dst_crs,  # destination CRS
            src.width,  # column count
            src.height,  # row count
            *src.bounds,  # unpacks outer boundaries (left, bottom, right, top)
        )

        if USELOG:
            print("Source Transform:\n", src_transform, '\n')
            print("Destination Transform:\n", dst_transform)


        # set properties for output
        dst_kwargs = src.meta.copy()
        dst_kwargs.update(
            {
                "crs": dst_crs,
                "transform": dst_transform,
                "width": width,
                "height": height,
                "nodata": -9999,  # replace 0 with np.nan
            }
        )

        with rasterio.open(dst_file, "w", **dst_kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=dst_transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.nearest,
                )

def get_file_str(file_path):
    """
    Returns the file name of an entire file path.

    :param file_path: str, with the file path
    :return: str, with the file name
    """
    alias = os.path.splitext(os.path.split(file_path)[1])[0]
    return alias
