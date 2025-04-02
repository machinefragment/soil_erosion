import os
import openeo
import rasterio
from rasterio.enums import Resampling

# First, set up file storage
def ensure_dir(directory):
    """ Ensure that a directory exists on the filesystem. If the directory does not exist, it is created.

    Parameters:
    directory (str): The path of the directory to check or create. 
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")
    else:
        print(f"Directory already exists: {directory}")

# Also, set up deletion handling
def delete_file(file_path):
    """Deletes a file from the filesystem if it exists.

    Parameters:
    file_path (str): The path to the file that should be deleted.
    """
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Deleted file: {file_path}")
    else:
        print(f"No file found at: {file_path}, nothing to delete.")

# Base directory for storage
storage_base = "C:/RUSLE_Application/File_Storage"

# Specific directories for NDVI and C_Factor
ndvi_dir = os.path.join(storage_base, "NDVI")
c_factor_dir = os.path.join(storage_base, "C_Factor")

# Ensure directories exist
ensure_dir(ndvi_dir)
ensure_dir(c_factor_dir)



# establish connection to EO
def fetch_SENTINEL(bbox, datetime):
    """Fetches Sentinel-2 satellite data as a datacube using the openEO API.

    Parameters:
    bbox (dict): A dictionary specifying the bounding box with keys 'west', 'south', 'east', 'north'.
    datetime (list): A list containing the start and end date strings.

    Returns:
    openeo.ImageCollection: An image collection of Sentinel-2 data.
    """
    connection = openeo.connect("openeofed.dataspace.copernicus.eu")
    connection.authenticate_oidc()
    sentinelCube = connection.load_collection(
        "SENTINEL2_L2A",
        spatial_extent=bbox,
        temporal_extent=datetime,
        bands=["B02", "B04", "B08", "SCL"],
        max_cloud_cover=85
    )
    
    return sentinelCube


# Example usage:
bounding = {"west": 5.14, "south": 51.17, "east": 5.17, "north": 51.19}
dates = ["2021-02-01", "2021-04-30"]
fetchcube = fetch_SENTINEL(bounding, dates)

# A function to calculate NDVI, based on the cube

def ndvi_generation(datacube, output_path):
    """ Generates an NDVI composite image from a given datacube and saves it as a GeoTIFF.

    Parameters:
    datacube (openeo.ImageCollection): The datacube obtained from Sentinel-2 data.
    output_path (str): The file path where the NDVI GeoTIFF will be saved.
    """
    # Rescale digital number values to physical reflectances
    red = datacube.band("B04") * 0.0001
    nir = datacube.band("B08") * 0.0001

    # compute ndvi

    ndvi_cube = (nir - red) / (nir + red)

    # Reduce the temporal dimension by taking the maximum value for each pixel
   
    ndvi_composite = ndvi_cube.max_time()

    # Download the result as a GeoTIFF file
    ndvi_composite.download(output_path)
    print(f"NDVI data saved to {output_path}")


def c_factor(tiff_path, output_path):
    """
    Calculates the cover factor (C-Factor) from an NDVI TIFF and saves it as a new TIFF.

    Parameters:
    tiff_path (str): The path to the NDVI TIFF file.
    output_path (str): The path where the C-Factor TIFF file will be saved.

    See Van der Knijff, J.M., Jones, R.J.A. and Montanarella, L. (2000) 
    Soil Erosion Risk Assessment in Europe. 
    EUR 19044 EN, Office for Official Publications of the European Communities, Luxembourg, 34.
    
    For more information on the specifications of the C-factor.


    """
    # Open the NDVI TIFF file
    with rasterio.open(tiff_path) as src:
        ndvi = src.read(1)  # Read the first band

        # Normalize NDVI to scale from 0 to 1
        ndvi_min, ndvi_max = ndvi.min(), ndvi.max()
        normalized_ndvi = (ndvi - ndvi_min) / (ndvi_max - ndvi_min)

        # Invert the normalized NDVI to get the Cover Factor
        cover_factor = 1 - normalized_ndvi

        # Define new metadata for the output file
        out_meta = src.meta.copy()
        out_meta.update({
            "dtype": 'float32',
            "compress": "lzw"
        })

        # Save the Cover Factor as a new TIFF file
        with rasterio.open(output_path, 'w', **out_meta) as dest:
            dest.write(cover_factor, 1)  # Write the Cover Factor to the first band
    print(f"C_Factor saved to {output_path}")

# Function which calls the C_factor function, but then also deletes the NDVI, to save on storage
def c_factor_and_cleanup(ndvi_path, c_factor_path):
    # Generate the C_Factor
    c_factor(ndvi_path, c_factor_path)
    
    # Delete the NDVI file after C_Factor has been created
    delete_file(ndvi_path)
    print("NDVI file has been deleted after processing C_Factor.")

ndvi_path = os.path.join(ndvi_dir, "ndvi.tiff")
c_factor_path = os.path.join(c_factor_dir, "cover_factor.tiff")

# Example usage
ndvi_generation(fetchcube, ndvi_path)
c_factor_and_cleanup(ndvi_path, c_factor_path)