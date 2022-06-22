
from config import *
from functions import get_file_str

# ----------------Save FUNCTIONS----------------------------------------------------------------------------- #

def save_csv(points, save_name):
    """
    Function receives an array with X, Y, Z point coordinates and converts it to a dataframe, with the corresponding
    column names and then saves the data frame as a .txt file

    :param points: np.array with (X,Y,Z) coordinates of cell centers
    :param save_name: file path name with which to save input point array to .txt format
    :return:
    """
    columns = ["x", "y", "z"]  # Set column names
    df = pd.DataFrame(data=points, index=None, columns=columns)  # Save points array to a pandas data frame
    # print(df)

    # Save table to .txt format
    df.to_csv(save_name, index=False, sep=',', na_rep="", decimal='.')


# ----------------Calculation FUNCTIONS----------------------------------------------------------------------------- #

def get_raster_points(array, gt):
    """
    Function gets the coordinates (X, Y, Z) of the center of all cells that have values and returns an array with the
    coordinate point data

    :param array: npp.array with original raster data
    :param gt: tuple with original raster geotransform data
    :return: np.array where the coordinate and values of the value cell centers are saved
    """

    # 1. Get [y,x] [rows, columns] coordinates of all cells where there are values (non np.nan)
    coord = np.argwhere(~np.isnan(array))
    # print(coord.shape)

    # 2. Initialize an array with the same number of rows as non-zero cell values and 3 columns (X, Y, Z values)
    points = np.zeros((int(coord.shape[0]) - 1, 3))

    # 3. Get upper left corner coordinates from Geotransform (Top left corner X, cell size, 0, Top left corner Y, 0,
    # -cell size)
    upper_left_x = gt[
        0]  # X coordinate of upper left corner. From this point, all cells go towards the right (positive)
    upper_left_y = gt[3]  # Y coordinate of upper left corner. From this point all points go south (negative)
    size = gt[1]  # Cell resolution

    # print("gt: ", gt)
    # print("Upper Left X: ", upper_left_x, "\nUpper Left Y: ", upper_left_y, "\nSize: ", size)

    for i in range(0, int(coord.shape[0]) - 1):  # go through all cells in coord array
        # 1.Fill in x coordinate in row 0
        points[i][0] = upper_left_x + coord[i][1] * size + (size / 2)

        # 2.Fill in x coordinate in row 1
        points[i][1] = upper_left_y - coord[i][0] * size - (size / 2)

        # 3. Fill in the precipitation value in row 2
        points[i][2] = array[int(coord[i][0])][int(coord[i][1])]

        # print("Index in coord: ", i, " - Row in Array: ", points[i][0], " - Column in array: ", points[i][1],
        #       " - Value: ", points[i][2] )

    # print("Points: ", points[0][2])

    # # The name of the .csv file must be "file" and it must be in the program working folder for it to be later read
    # a .vrt file # In the VRT_File function. Does not work otherwise. FIle will be rewritten in each loop and erased
    # at the end. points_path = "file.csv"  # Create the .csv file name as "file.csv" - SaveCSV(points, points_path)
    # Save the XYZ coordinates array to a .csv file

    return points  # Return XYZ.csv file path


def generate_vrt_file(csv_file):
    """
    Function receives a .csv file path, which was created in the "GetRasterPoints" and is then copied to a vrt file.
    The .csv file MUST BE named "file", since that name is automatically called in the vrt file creation.

    :param csv_file: .csv file path with point coordinates (x,y,z) generated in "GetRasterPoints" function
    :return: .vrt file path
    """

    vrt_file = csv_file.replace(".csv",".vrt")

    # Check if VRT file previously exists. If it does, erase it:
    if os.path.exists(vrt_file):
        os.remove(vrt_file)

    # Create VRT file with coordinate information (located in file.csv file) :
    vrt = open(vrt_file, 'w')  # Open .vrt file
    # Create the .vrt file with the following code, which remains constant always
    vrt.write("<OGRVRTDataSource>\n \
        <OGRVRTLayer name=\"file\">\n \
        <SrcDataSource>file.csv</SrcDataSource>\n \
        <SrcLayer>file</SrcLayer> \n \
        <GeometryType>wkbPoint25D</GeometryType>\n \
        <LayerSRS>EPSG:32634</LayerSRS>\n \
        <GeometryField encoding=\"PointFromColumns\" x=\"x\" y=\"y\" z=\"z\"/>\n \
        </OGRVRTLayer>\n \
        </OGRVRTDataSource>")
    vrt.close()

    return vrt_file


def interpolate_points(vrt_file, raster_name, snap_data, cell_size):
    """
    Function receives the path of the .vrt file, which contains the XYZ points and uses these points to interpolate
    values for a new raster resolution (cell size)

    :param vrt_file: .vrt virtual file path which contains the original raster cell center coordinates
    :param folder: folder path in which to temporarily save the interpolated raster file
    :param snap_data: np.array with snap raster extension [Xmin, Ymax, Xmax, Ymin] or [ulX ulY lrX lrY]
    :param cell_size: float with cell size of the resulting raster (same as snap raster's)
    :return: path for the interpolated raster file
    """

    # Check if raster exists, and if it does, erase if:
    if os.path.exists(raster_name):
        os.remove(raster_name)

    # Get the number of columns and rows that the resampled raster must have. Same as the size of the snap raster
    columns = str(int((snap_data[2] - snap_data[0]) / cell_size))  # Get No. of columns in snap raster (as as string)
    rows = str(int((snap_data[1] - snap_data[3]) / cell_size))  # Get No. of rows in snap raster (as a string)

    # Use gdal grid to interpolate:
    # ---- a:interpolation method (Inv distance with nearest neighbor, with smoothing of 0, using a max number of 12
    # ----- points, searching in a 5000 m radius for those max. 12 points)
    # ---- txe: Xmin Xmax,
    # ---- tye: Ymin, Ymax,
    # ---- outsize: columns rows, of: output file format
    # ---- a_srs: coordinate system, ot: out type (float)
    os.system(
        "gdal_grid -a invdistnn:power=2.0:smoothing=0:max_points=12:radius=5000 -txe " + str(snap_data[0]) + " " + str(
            snap_data[2]) +
        " -tye " + str(snap_data[3]) + " " + str(
            snap_data[1]) + " -outsize " + columns + " " + rows + " -of gtiff -a_srs EPSG:32634 " +
        "-ot Float32 " + vrt_file + " " + raster_name)
    return raster_name

