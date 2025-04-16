import rasterio
from rasterio.warp import calculate_default_transform, reproject
from rasterio.enums import Resampling
from rasterio.io import MemoryFile

def reproject_raster_obj(raster, dst_crs='EPSG:4269', resampling=Resampling.nearest):
    """
    Reproject a rasterio DatasetReader object to a target CRS (default NAD83).
    
    Returns a new rasterio DatasetReader object in memory.
    """
    transform, width, height = calculate_default_transform(
        raster.crs, dst_crs, raster.width, raster.height, *raster.bounds)

    kwargs = raster.meta.copy()
    kwargs.update({
        'crs': dst_crs,
        'transform': transform,
        'width': width,
        'height': height
    })

    memfile = MemoryFile()
    with memfile.open(**kwargs) as dst:
        for i in range(1, raster.count + 1):
            reproject(
                source=rasterio.band(raster, i),
                destination=rasterio.band(dst, i),
                src_transform=raster.transform,
                src_crs=raster.crs,
                dst_transform=transform,
                dst_crs=dst_crs,
                resampling=resampling
            )
    return memfile.open()


def resample_raster_obj(src_raster, reference_raster, resampling='bilinear'):
    """
    Resample one raster (src_raster) to match the resolution and transform of another (reference_raster).
    
    Parameters:
    - src_raster: rasterio DatasetReader object (the one to resample)
    - reference_raster: rasterio DatasetReader object (defines target resolution/transform)
    - resampling: str or Resampling enum (default 'bilinear')

    Returns:
    - rasterio DatasetReader object (in memory, resampled)
    """
    # allow string or enum
    resampling_methods = {
        'nearest': Resampling.nearest,
        'bilinear': Resampling.bilinear,
        'cubic': Resampling.cubic,
        'average': Resampling.average,
        'lanczos': Resampling.lanczos,
        'mode': Resampling.mode
    }
    if isinstance(resampling, str):
        resampling = resampling_methods.get(resampling.lower(), Resampling.bilinear)

    out_shape = (src_raster.count, reference_raster.height, reference_raster.width)
    transform = reference_raster.transform

    data = src_raster.read(out_shape=out_shape, resampling=resampling)

    kwargs = src_raster.meta.copy()
    kwargs.update({
        'height': reference_raster.height,
        'width': reference_raster.width,
        'transform': transform
    })

    memfile = MemoryFile()
    with memfile.open(**kwargs) as dst:
        dst.write(data)
    return memfile.open()
