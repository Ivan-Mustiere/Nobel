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

df = pd.read_csv(csv_path, dtype={"com_insee": str})
df["com_insee"] = df["com_insee"].str.zfill(5)

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
filtered = merged.dropna(subset=['nbr_accidents'])
filtered = filtered[filtered['nbr_accidents'] >= 1].sort_values(by='nbr_accidents', ascending=False)

if filtered.empty:
    st.warning("⚠️ Aucune commune avec au moins 1 accident pour ce mois.")
    st.stop()

# Total accidents
total = int(filtered['nbr_accidents'].sum())
st.markdown(f"### 🚧 Total d'accidents ce mois : **{total:,}**")

# -----------------------------
# 5. Choix du fond de carte
# -----------------------------
tile_option = st.selectbox(
    "🗺️ Choix du fond de carte",
    ['CartoDB positron', 'CartoDB Dark_Matter']
)

# -----------------------------
# 6. Filtre interactif par nombre d'accidents
# -----------------------------
min_acc = st.slider("🔢 Filtrer les communes avec au moins X accidents", 1, int(filtered['nbr_accidents'].max()), 1)
filtered = filtered[filtered['nbr_accidents'] >= min_acc]

# -----------------------------
# 7. Créer la carte Folium
# -----------------------------
m = folium.Map(location=[46.5, 2.5], zoom_start=6, tiles=tile_option)

max_val = int(filtered['nbr_accidents'].max())
if max_val <= 10:
    thresholds = list(range(1, max_val + 2))
else:
    thresholds = list(np.linspace(1, max_val, 6, dtype=int))
    thresholds = sorted(set(thresholds + [max_val + 1]))
if max_val >= thresholds[-1]:
    thresholds.append(max_val + 1)

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
    bins=thresholds,
).add_to(m)

# Infobulles simplifiées
for _, row in filtered.iterrows():
    nom = row["nom_commune"]
    acc = int(row["nbr_accidents"])
    veh = int(row.get("nbr_vehicules", 0))
    geom = row["geometry"]
    if geom and geom.centroid:
        lat, lon = geom.centroid.y, geom.centroid.x
        tooltip = f"{nom} : {acc} accident(s), {veh} véhicule(s)"
        folium.CircleMarker(
            location=[lat, lon],
            radius=3 + (acc ** 0.5),
            color="red",
            fill=True,
            fill_opacity=0.6,
            tooltip=tooltip
        ).add_to(m)

# -----------------------------
# 8. Affichage dans Streamlit
# -----------------------------
st.subheader(f"🗺️ Carte interactive – Mois {mois_select}")
st_folium(m, width=1000, height=700, returned_objects=[])

# -----------------------------
# 9. Tableau des données
# -----------------------------
st.subheader(f"📊 Top 20 des communes avec le plus d'accidents – Mois {mois_select}")
df_display = filtered[['com_insee', 'nom_commune', 'nbr_accidents', 'nbr_vehicules']]
st.dataframe(df_display.head(20))

# -----------------------------
# 10. Téléchargement CSV
# -----------------------------
st.download_button(
    label="📥 Télécharger les données du mois (CSV)",
    data=df_display.to_csv(index=False),
    file_name=f"accidents_mois_{mois_select}.csv",
    mime="text/csv"
)

# -----------------------------
# 11. Histogramme des classes
# -----------------------------
st.subheader("📈 Répartition des communes par classe d'accidents")
bins = pd.cut(filtered['nbr_accidents'], bins=thresholds)
hist = bins.value_counts().sort_index()
hist_df = pd.DataFrame({'Classe': hist.index.astype(str), 'Nombre de communes': hist.values})
st.bar_chart(hist_df.set_index('Classe'))
