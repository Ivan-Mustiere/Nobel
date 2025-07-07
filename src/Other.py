import os
import pandas as pd

# Chargement
caract = pd.read_csv("data/caract-2023.csv", sep=';', dtype={'com': str})
vehicules = pd.read_csv("data/vehicules-2023.csv", sep=';', dtype={'Num_Acc': str})
usagers = pd.read_csv("data/usagers-2023.csv", sep=';', dtype={'Num_Acc': str})

# Nettoyage
caract = caract[~caract['com'].isna()]
caract['Num_Acc'] = caract['Num_Acc'].astype(str)
vehicules['Num_Acc'] = vehicules['Num_Acc'].astype(str)
usagers['Num_Acc'] = usagers['Num_Acc'].astype(str)

# Regroupement Paris, Lyon, Marseille
def regroupe_communes(code):
    code = code.zfill(5)
    if code.startswith('75'):
        return '75056'  # Paris
    elif code.startswith('69') and code not in ['69000']:
        return '69123'  # Lyon
    elif code.startswith('13') and code not in ['13000']:
        return '13055'  # Marseille
    return code

caract['com_insee'] = caract['com'].apply(regroupe_communes)

# Préparation sortie
output_dir = "output/mois"
os.makedirs(output_dir, exist_ok=True)

for mois in range(1, 13):
    mois_str = str(mois).zfill(2)
    subset = caract[caract["mois"] == mois]

    # Filtrer véhicules et usagers du mois
    acc_ids = subset["Num_Acc"].unique()
    v_sub = vehicules[vehicules["Num_Acc"].isin(acc_ids)]
    u_sub = usagers[usagers["Num_Acc"].isin(acc_ids)]

    # Agrégation véhicules : nombre de véhicules par accident
    veh_counts = v_sub.groupby("Num_Acc").size().reset_index(name="veh_count")

    # Agrégation usagers : nombre par sexe (sera ignoré côté app)
    sex_counts = u_sub.pivot_table(index="Num_Acc", columns="sexe", aggfunc='size', fill_value=0).reset_index()
    sex_counts.columns.name = None

    # Fusion avec données principales
    enriched = subset.merge(veh_counts, on="Num_Acc", how="left").merge(sex_counts, on="Num_Acc", how="left")
    enriched["veh_count"] = enriched["veh_count"].fillna(0)
    enriched["1"] = enriched.get("1", 0)  # hommes
    enriched["2"] = enriched.get("2", 0)  # femmes

    # Agrégation finale par commune
    df_month = enriched.groupby("com_insee").agg(
        nbr_accidents=("Num_Acc", "count"),
        nbr_vehicules=("veh_count", "sum"),
        nb_hommes=("1", "sum"),
        nb_femmes=("2", "sum")
    ).reset_index()

    mois_folder = os.path.join(output_dir, mois_str)
    os.makedirs(mois_folder, exist_ok=True)

    csv_path = os.path.join(mois_folder, f"accidents_{mois_str}.csv")
    df_month.to_csv(csv_path, index=False)

    print(f"✅ Fichier enrichi créé : {csv_path}")
