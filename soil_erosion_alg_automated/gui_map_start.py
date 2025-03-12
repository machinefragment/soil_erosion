from flask import Flask, render_template, request, jsonify
import folium
from folium.plugins import Draw
import geopandas as gpd
import os
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, Resampling, transform_bounds
from PIL import Image
import io
import zipfile
import base64
import logging

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_map():
    folium_map = folium.Map(location=[20, 0], zoom_start=2, control_scale=True, tiles="openstreetmap", name="Street Map")
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Satellite Imagery",
        overlay=False
    ).add_to(folium_map)
    Draw(export=True).add_to(folium_map)
    folium.LayerControl(collapsed=False).add_to(folium_map)
    return folium_map

@app.route('/')
def index():
    folium_map = create_map()
    map_data = folium_map._repr_html_()
    logger.debug(f"Generated map HTML: {map_data[:500]}")
    return render_template("base_map.html", map_data=map_data)

@app.route('/upload_raster', methods=['POST'])
def upload_raster():
    file = request.files.get('file')
    if not file:
        return jsonify(status="error", message="No file uploaded"), 400
    logger.debug(f"Received raster file: {file.filename}")
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ['.tif', '.tiff']:
        return jsonify(status="error", message="Please upload a raster file (.tif, .tiff)"), 400

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    try:
        logger.debug(f"Processing raster: {file_path}")
        with rasterio.open(file_path) as src:
            transform, width, height = calculate_default_transform(src.crs, 'EPSG:3857', src.width, src.height, *src.bounds)
            kwargs = src.meta.copy()
            kwargs.update({'crs': 'EPSG:3857', 'transform': transform, 'width': width, 'height': height})
            img = src.read(out_shape=(src.count, height, width), resampling=Resampling.bilinear)
            img = np.moveaxis(img, 0, -1)
            if img.dtype != np.uint8:
                img = (img * 255).astype(np.uint8)
            png_image = Image.fromarray(img[:, :, :3] if img.shape[2] >= 3 else img[:, :, 0])
            png_buffer = io.BytesIO()
            png_image.save(png_buffer, format="PNG")
            png_data = base64.b64encode(png_buffer.getvalue()).decode('utf-8')
            bounds = transform_bounds(src.crs, 'EPSG:4326', *src.bounds)
            img_bounds = [[bounds[1], bounds[0]], [bounds[3], bounds[2]]]
            logger.debug(f"Raster bounds: {img_bounds}")
        return jsonify(status="success", type="raster", image_data=png_data, bounds=img_bounds, name=file.filename)
    except Exception as e:
        logger.error(f"Raster processing error: {str(e)}")
        return jsonify(status="error", message=f"Error processing raster: {str(e)}"), 500

@app.route('/upload_shapefile', methods=['POST'])
def upload_shapefile():
    files = request.files.getlist('file')
    if not files:
        return jsonify(status="error", message="No files uploaded"), 400
    logger.debug(f"Received shapefile(s): {[f.filename for f in files]}")
    
    file_paths = []
    for f in files:
        file_path = os.path.join(UPLOAD_FOLDER, f.filename)
        f.save(file_path)
        file_paths.append(file_path)

    try:
        shp_file = next((f for f in files if f.filename.lower().endswith('.shp')), None)
        if not shp_file:
            return jsonify(status="error", message="No .shp file found. Please upload a .shp file with .shx and .dbf, or a .zip."), 400
        
        file_extension = os.path.splitext(shp_file.filename)[1].lower()
        if file_extension == '.zip':
            with zipfile.ZipFile(os.path.join(UPLOAD_FOLDER, shp_file.filename), 'r') as zip_ref:
                zip_ref.extractall(UPLOAD_FOLDER)
            shp_file_path = os.path.join(UPLOAD_FOLDER, os.path.splitext(shp_file.filename)[0] + '.shp')
            if not os.path.exists(shp_file_path):
                return jsonify(status="error", message="No .shp file found in the zip archive"), 400
            gdf = gpd.read_file(shp_file_path)
        elif file_extension == '.shp':
            base_name = os.path.splitext(shp_file.filename)[0]
            required_extensions = ['.shx', '.dbf']
            missing_files = [ext for ext in required_extensions if not any(f.filename == base_name + ext for f in files)]
            if missing_files:
                return jsonify(status="error", message=f"Missing required files: {', '.join(base_name + ext for ext in missing_files)}. Please upload .shp, .shx, and .dbf together or use a .zip."), 400
            gdf = gpd.read_file(os.path.join(UPLOAD_FOLDER, shp_file.filename))
        else:
            return jsonify(status="error", message="Please upload a shapefile (.shp with .shx and .dbf, or .zip containing them)"), 400
        geo_json = json.loads(gdf.to_json())
        bounds = gdf.total_bounds
        logger.debug(f"Shapefile bounds: {bounds}")
        return jsonify(status="success", type="shapefile", geojson=geo_json, bounds=[[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
    except Exception as e:
        logger.error(f"Shapefile processing error: {str(e)}")
        return jsonify(status="error", message=f"Error processing shapefile: {str(e)}"), 500

if __name__ == '__main__':
    app.run(debug=True)