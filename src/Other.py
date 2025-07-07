import pandas as pd
import geopandas as gpd
import os

# --------------------------
# Chargement des données
# --------------------------
caract = pd.read_csv("data/caract-2023.csv", sep=';', dtype={'com': str})
caract = caract[~caract['com'].isna()]

geo = gpd.read_file("data/communes.geojson")[['code', 'nom', 'geometry']]
geo.columns = ['com_insee', 'nom_commune', 'geometry']

# --------------------------
# Regroupement des communes spéciales
# --------------------------
# Dictionnaire : codes à fusionner → nouveau code INSEE
fusion_map = {
    '75': '75056',   # Paris
    '69': '69123',   # Lyon (69XXX)
    '13': '13055'    # Marseille
}

def regroupe_communes(code_insee):
    if code_insee.startswith('75'):
        return '75056'
    elif code_insee.startswith('69') and code_insee != '69000':
        return '69123'
    elif code_insee.startswith('13') and code_insee != '13000':
        return '13055'
    return code_insee

caract['com_insee'] = caract['com'].apply(lambda x: regroupe_communes(x.zfill(5)))

# --------------------------
# Préparer sortie
# --------------------------
output_dir = "output/mois"
os.makedirs(output_dir, exist_ok=True)

# --------------------------
# Boucle mensuelle
# --------------------------
for mois in range(1, 13):
    mois_str = str(mois).zfill(2)

    subset = caract[caract["mois"] == mois]

    df_month = (
        subset.groupby("com_insee")
        .size()
        .reset_index(name="nbr_accidents")
    )

    mois_folder = os.path.join(output_dir, mois_str)
    os.makedirs(mois_folder, exist_ok=True)

    csv_path = os.path.join(mois_folder, f"accidents_{mois_str}.csv")
    df_month.to_csv(csv_path, index=False)

    print(f"✅ Fichier créé : {csv_path}")
