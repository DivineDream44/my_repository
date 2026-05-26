import streamlit as st
from PIL import Image, ImageOps
import piexif
import io
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Editeur EXIF", layout="wide")

def decimal_to_dms(value):
    value = abs(value)
    degrees = int(value)
    minutes_float = (value - degrees) * 60
    minutes = int(minutes_float)
    seconds = round((minutes_float - minutes) * 60 * 10000)
    return ((degrees, 1), (minutes, 1), (seconds, 10000))

def gps_ifd(lat, lon):
    gps = {}
    gps[piexif.GPSIFD.GPSVersionID] = (2, 0, 0, 0)
    gps[piexif.GPSIFD.GPSLatitudeRef] = "N" if lat >= 0 else "S"
    gps[piexif.GPSIFD.GPSLatitude] = decimal_to_dms(lat)
    gps[piexif.GPSIFD.GPSLongitudeRef] = "E" if lon >= 0 else "W"
    gps[piexif.GPSIFD.GPSLongitude] = decimal_to_dms(lon)
    return gps

def load_exif(image_bytes):
    try:
        return piexif.load(image_bytes)
    except Exception:
        return {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

def encode_utf8(text):
    return text.encode("utf-8") if text else b""

st.title("Editeur Streamlit avec EXIF, GPS et POI")

with open("mnemosyne.jpg", "rb") as f:
    image_bytes = f.read()

image_name = "mnemosyne.jpg"
img = Image.open(io.BytesIO(image_bytes))
img = ImageOps.exif_transpose(img)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Photo")
    st.image(img, width="stretch")

exif_dict = load_exif(image_bytes)

lat = 43.073926
lon = -89.385244

with col2:
    st.subheader("Formulaire EXIF")
    with st.form("exif_form"):
        file_name = st.text_input("Nom", "Mnemosyne")
        file_author = st.text_input("Auteur", "Jonah Brown")
        file_description = st.text_input("Description", "femme en lunettes de soleil marron et chemise marron.")
        file_comment = st.text_area("Commentaire", "Photo libre de droits. Trouvée sur le site Unsplash.")
        file_published_date = st.text_input("Date de publication", "2021:03:22 00:00:00")
        file_camera = st.text_input("Camera utilisée", "SONY")
        file_model = st.text_input("Model de la caméra", "ILCE-7M3")
        file_copyright = st.text_input("Licence", "Unsplash")
        file_width = st.number_input("Largeur px", value=3636, step=1)
        file_height = st.number_input("Hauteur px", value=5454, step=1)
        lat = st.number_input("Latitude", value=lat, format="%.6f", key="lat_input")
        lon = st.number_input("Longitude", value=lon, format="%.6f", key="lon_input")
        submit = st.form_submit_button("Mettre à jour")

    if submit:
        exif_dict["0th"][piexif.ImageIFD.XPTitle] = file_name.encode("utf-16le")
        exif_dict["0th"][piexif.ImageIFD.Artist] = encode_utf8(file_author)
        exif_dict["0th"][piexif.ImageIFD.ImageDescription] = encode_utf8(file_description)
        exif_dict["0th"][piexif.ImageIFD.XPComment] = file_comment.encode("utf-16le")
        exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = encode_utf8(file_published_date)
        exif_dict["0th"][piexif.ImageIFD.Make] = encode_utf8(file_camera)
        exif_dict["0th"][piexif.ImageIFD.Model] = encode_utf8(file_model)
        exif_dict["0th"][piexif.ImageIFD.Copyright] = encode_utf8(file_copyright)
        exif_dict["0th"][piexif.ImageIFD.ImageWidth] = int(file_width)
        exif_dict["0th"][piexif.ImageIFD.ImageLength] = int(file_height)
        exif_dict["GPS"] = gps_ifd(lat, lon)

        exif_bytes = piexif.dump(exif_dict)
        output = io.BytesIO()
        img.save(output, format="JPEG", exif=exif_bytes)
        output.seek(0)

        st.success("Image mise à jour.")
        st.download_button(
            "Télécharger l'image modifiée",
            data=output.getvalue(),
            file_name=f"modified_{image_name}",
            mime="image/jpeg"
        )

st.divider()

st.subheader("Carte des coordonnées de la photo")
map1 = folium.Map(location=[lat, lon], zoom_start=13)
folium.Marker([lat, lon], popup="Position GPS de l'image").add_to(map1)
st_folium(map1, width=750, height=450, key="gps_map")
            
st.divider()

st.subheader("Carte POI")
poi_list = [
    ("Vaison-la-Romaine", 44.2407641, 5.075737),
    ("Paris", 48.8588897, 2.320041),
    ("Saint-Jean-de-Monts", 46.7936111, -2.0588889),
    ("Soulac-sur-Mer", 45.513149, -1.1228789),
    ("Argelès-sur-Mer", 42.5476734, 3.0253613),
    ("Quiberon", 47.4874, -3.12152),
    ("Biscaros", 43.2626963, -0.6130566),
    ("La Roque-sur-Cèze", 44.193857, 4.5194678),
    ("Chenonceau", 47.34701, 1.1691652),
    ("Brissac", 43.8783291, 3.7027359),
    ("Chambord", 48.8899454, 0.6095948),
    ("Amboise", 47.4110351, 0.983698),
    ("Fontainebleau", 48.4049375, 2.7015872),
    ("Salou", 41.0768193, 1.1440411),
    ("Barcelone", 41.3825802, 2.177073),
    ("Bournemouth", 50.7201514, -1.8799118)
]

poi_gps = [(p[1], p[2]) for p in poi_list]
map2 = folium.Map(location=poi_gps[0], zoom_start=6)

for name, la, lo in poi_list:
    folium.Marker([la, lo], popup=name, tooltip=name).add_to(map2)

folium.PolyLine(poi_gps, color="pink", weight=3).add_to(map2)
st_folium(map2, width=750, height=450)
