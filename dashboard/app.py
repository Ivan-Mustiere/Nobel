import os
import numpy as np
import pandas as pd
import geopandas as gpd
import folium
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(layout="wide")
st.title("📍 Carte dynamique des accidents par commune – par mois")

# -----------------------------
# 1. Lister les mois disponibles
# -----------------------------
base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "output", "mois"))
if not os.path.exists(base_path):
    st.error(f"❌ Le dossier {base_path} n'existe pas.")
    st.stop()

mois_folders = sorted([
    d for d in os.listdir(base_path)
    if os.path.isdir(os.path.join(base_path, d)) and d.isdigit()
])
if not mois_folders:
    st.error(f"❌ Aucun mois trouvé dans {base_path}")
    st.stop()

mois_select = st.selectbox(
    "🗓️ Choisir un mois",
    mois_folders,
    format_func=lambda x: f"Mois {x}"
)

# -----------------------------
# 2. Charger les données du mois
# -----------------------------
csv_path = os.path.join(base_path, mois_select, f"accidents_{mois_select}.csv")
if not os.path.exists(csv_path):
    st.error(f"❌ Fichier CSV manquant : {csv_path}")
    st.stop()

df = pd.read_csv(csv_path, usecols=["com_insee", "nbr_accidents"])
df["com_insee"] = df["com_insee"].astype(str).str.zfill(5)

# -----------------------------
# 3. Charger les géométries des communes
# -----------------------------
geo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "communes.geojson"))
if not os.path.exists(geo_path):
    st.error(f"❌ Fichier GeoJSON manquant : {geo_path}")
    st.stop()

geo = gpd.read_file(geo_path)[['code', 'nom', 'geometry']]
geo.columns = ['com_insee', 'nom_commune', 'geometry']
geo["com_insee"] = geo["com_insee"].astype(str).str.zfill(5)

# -----------------------------
# 4. Fusion et filtrage
# -----------------------------
merged = geo.merge(df, on='com_insee', how='left')
merged['nbr_accidents'] = merged['nbr_accidents'].fillna(0)
filtered = merged[merged['nbr_accidents'] >= 1].sort_values(by='nbr_accidents', ascending=False)

if filtered.empty:
    st.warning("⚠️ Aucune commune avec au moins 1 accident pour ce mois.")
    st.stop()

# -----------------------------
# 5. Créer la carte Folium
# -----------------------------
m = folium.Map(location=[46.5, 2.5], zoom_start=6, tiles='CartoDB Dark_Matter')
max_val = filtered['nbr_accidents'].max()

import numpy as np

# Calcul des seuils dynamiques sûrs
max_val = int(filtered['nbr_accidents'].max())

if max_val <= 10:
    thresholds = list(range(1, max_val + 2))  # ex : [1, 2, ..., max+1]
else:
    # 6 bins linéaires + une borne max + 1
    thresholds = list(np.linspace(1, max_val, 6, dtype=int))
    thresholds = sorted(set(thresholds + [max_val + 1]))


folium.Choropleth(
    geo_data=filtered.__geo_interface__,
    data=filtered,
    columns=["com_insee", "nbr_accidents"],
    key_on="feature.properties.com_insee",
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=0.1,
    legend_name=f"Accidents – Mois {mois_select}",
    threshold_scale=thresholds,
    bins=thresholds,  # Ajout essentiel
    nan_fill_color='white',
    nan_fill_opacity=0.4
).add_to(m)

for _, row in filtered.iterrows():
    nom = row.get("nom_commune", "Inconnu")
    accidents = int(row.get("nbr_accidents", 0))
    geom = row.get("geometry", None)

    if geom is not None:
        folium.GeoJson(
            geom,
            style_function=lambda x: {"fillOpacity": 0, "color": "transparent"},
            tooltip=folium.Tooltip(f"{nom} : {accidents} accident(s)")
        ).add_to(m)

# -----------------------------
# 6. Affichage dans Streamlit
# -----------------------------
st.subheader(f"🗺️ Carte interactive – Mois {mois_select}")
st_folium(m, width=1000, height=700, returned_objects=[])

# -----------------------------
# 7. Tableau des données
# -----------------------------
st.subheader(f"📊 Top 20 des communes avec le plus d'accidents – Mois {mois_select}")
df_display = filtered[['com_insee', 'nom_commune', 'nbr_accidents']]
st.dataframe(df_display.head(20))
