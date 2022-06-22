"""
The module extracts a set of .nc files and cuts them to the given shapefile. The raster files have to contain bands with
a percentual share for the land use class (PFT0 - PFT32). The land use bands are projected to the C-Factor according to
the given csv file (c_fac_file) and are merged to one band which contains the sum of C-Factors based on their share.
The Raster is saved to a latitude-longitude-projection and later transfered to the target CRS (EPSG:32634). Based on the
snap file (snapraster_file) the area is interpolated (gdal_grid; invdistnn) and clipped along the given shape file. The
final file is exported in the export folder.

Needed information:
- See config.py file
"""
# Import files
from functions import *
from config import *
import raster_calculations as rc
import resample_snap as rs

start_time = time.time()

if not (os.path.exists(lu_path)):
    raise Exception("The folder '" + lu_path + "' does not exist")

if not (os.path.exists(export_folder)):
    os.makedirs(export_folder)
if not (os.path.exists(tmp_folder)):
    os.makedirs(tmp_folder)

# Get C-factor values correlating to land use
c_factor = pd.read_csv(c_fac_file, header=0, delimiter=',', usecols=[1, 2, 3], )

# Get projection and geotransform from the snap raster:
gt, proj, snap_data, cell_resolution = rc.get_snap_raster_data(snapraster_file)


# Iterate over all available NC-files
filenames = glob.glob(lu_path + "/*.nc")
for i, nc_file in enumerate(filenames):
    print("File: " + nc_file)

    # Extract current file name
    nc_alias = get_file_str(nc_file)

    # Extract NC-data
    print("Importing NC file ...")
    ds, ds_lon, ds_lat = extract_nc_data_to_array(nc_file)

    # Apply the C-factors based on the pixels share and season
    print("Applying C Factors ...")
    summer_array, winter_array = apply_cfac_to_array(ds, ds_lon, ds_lat, c_factor)

    for season_array, season_alias in zip([summer_array, winter_array], ["summer", "winter"]):

        # Define files
        interpolation_file = tmp_folder + '/' + nc_alias + "_" + season_alias + '_interpolation.tif'
        season_file_epsg4326 = tmp_folder + '/' + nc_alias + "_" + season_alias + "_epsg4326.tif"
        season_file_epsg32634 = tmp_folder + '/' + nc_alias + "_" + season_alias + "_epsg32634.tif"

        season_file_finalized = export_folder + '/' + nc_alias + "_" + season_alias + "_clip.tif"

        # Export the finalized tif
        print(season_alias + ", Exporting epsg:4326 ...")
        export_to_tif(ds_lon, ds_lat, season_array, season_file_epsg4326)

        # Change to the target CRS 32634 (18°E - 24°E)
        print(season_alias + ", Exporting epsg:32634 ...")
        transform_to_target_crs(season_file_epsg4326, season_file_epsg32634, "EPSG:32634")

        # Save raster data to an array
        print(season_alias + ", Importng Raster ...")
        original_array = rc.raster_to_array(season_file_epsg32634, mask=False)

        # Convert all -9999 No data cells into numpy nan values
        original_array = np.where(original_array == 9.96921e+36, np.nan, original_array)

        # Get the gt (geotransform) information from the original raster file
        gt_original, proj_original = rc.get_raster_data(season_file_epsg32634)  # Get gt information from the ASCII file

        # Get the coordinates of the center of all the cells WITH VALUES and save data the XYZ coordinates for each point to an array
        print(season_alias + ", Preparing CSV ...")
        xyz_array = rs.get_raster_points(original_array, gt_original)  # Path with the .csv file with coordinates

        # Save the XYZ coordinate data to a .csv file
        print(season_alias + ", Exporting CSV ...")
        rs.save_csv(xyz_array, xyz_csv_file)  # Save array to .csv file

        # Create a .vrt file from the .csv in order to be read by the gdal grid command
        print(season_alias + ", Generating VRT ...")
        xyz_vrt_file = rs.generate_vrt_file(xyz_csv_file)

        # Interpolate and resample points using GDAL_Grid - for interpolation a brush is used to merge the pixels
        print(season_alias + ", Interpolating target area...")
        rs.interpolate_points(xyz_vrt_file, interpolation_file, snap_data, cell_resolution)

        # Clip the resampled raster to the extent of the shape file
        print(season_alias + ", Clipping target area...")
        rc.clip(shape_file, season_file_finalized, interpolation_file)

        print(season_alias + ", Erasing tmp ...")
        # Erase .csv file with points
        if os.path.exists(xyz_csv_file):
            os.remove(xyz_csv_file)

        # Erase the vrt file
        if os.path.exists(xyz_vrt_file):
            os.remove(xyz_vrt_file)

        if not (USELOG):
            # Erase the interpolation file
            if os.path.exists(interpolation_file):
                os.remove(interpolation_file)

            # Erase the epsg:4326 tif
            if os.path.exists(season_file_epsg4326):
                os.remove(season_file_epsg4326)

            # Erase the epsg:32634 tif
            if os.path.exists(season_file_epsg32634):
                os.remove(season_file_epsg32634)

print('Total time: ', time.time() - start_time)
