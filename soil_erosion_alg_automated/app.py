from flask import Flask, render_template, request, jsonify
import folium
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route("/")
def index():
    # Create folium map centered at default location
    folium_map = folium.Map(location=[20.0, 0.0], zoom_start=2)
    map_path = os.path.join("templates", "map.html")
    folium_map.save(map_path)

    return render_template("map.html")

@app.route("/add_marker", methods=["POST"])
def add_marker():
    data = request.form
    lat = data.get("lat")
    lon = data.get("lon")
    address = data.get("address")

    # Handle file upload
    if "file" in request.files:
        file = request.files["file"]
        if file.filename != "":
            file.save(os.path.join(UPLOAD_FOLDER, file.filename))

    # Return JSON response
    return jsonify({"lat": lat, "lon": lon, "address": address, "message": "Marker added successfully!"})

if __name__ == "__main__":
    app.run(debug=True)
