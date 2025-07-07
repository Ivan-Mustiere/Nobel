import psycopg2
import pandas as pd

conn = psycopg2.connect(
    dbname="dap_db",
    user="dap_user",
    password="dap_pass",
    host="postgres"
)
cur = conn.cursor()

# Définition des tables
tables = {
    "vehicules": {
        "csv": "/data/vehicules-2023.csv",
        "schema": """
            CREATE TABLE IF NOT EXISTS vehicules (
                Num_Acc TEXT,
                id_vehicule TEXT,
                num_veh TEXT,
                senc TEXT,
                catv TEXT,
                obs TEXT,
                obsm TEXT,
                choc TEXT,
                manv TEXT,
                motor TEXT,
                occutc TEXT
            )
        """
    },
    "usagers": {
        "csv": "/data/usagers-2023.csv",
        "schema": """
            CREATE TABLE IF NOT EXISTS usagers (
                Num_Acc TEXT,
                id_usager TEXT,
                id_vehicule TEXT,
                num_veh TEXT,
                place TEXT,
                catu TEXT,
                grav TEXT,
                sexe TEXT,
                an_nais TEXT,
                trajet TEXT,
                secu1 TEXT,
                secu2 TEXT,
                secu3 TEXT,
                locp TEXT,
                actp TEXT,
                etatp TEXT
            )
        """
    },
    "lieux": {
        "csv": "/data/lieux-2023.csv",
        "schema": """
            CREATE TABLE IF NOT EXISTS lieux (
                Num_Acc TEXT,
                catr TEXT,
                voie TEXT,
                v1 TEXT,
                v2 TEXT,
                circ TEXT,
                nbv TEXT,
                vosp TEXT,
                prof TEXT,
                pr TEXT,
                pr1 TEXT,
                plan TEXT,
                lartpc TEXT,
                larrout TEXT,
                surf TEXT,
                infra TEXT,
                situ TEXT,
                vma TEXT
            )
        """
    },
    "caract": {
        "csv": "/data/caract-2023.csv",
        "schema": """
            CREATE TABLE IF NOT EXISTS caract (
                Num_Acc TEXT,
                jour TEXT,
                mois TEXT,
                an TEXT,
                hrmn TEXT,
                lum TEXT,
                dep TEXT,
                com TEXT,
                agg TEXT,
                int TEXT,
                atm TEXT,
                col TEXT,
                adr TEXT,
                lat TEXT,
                long TEXT
            )
        """
    }
}

# Créer les tables et insérer les données
for name, info in tables.items():
    cur.execute(info["schema"])
    conn.commit()
    df = pd.read_csv(info["csv"], sep=";", dtype=str)
    df.columns = [col.strip() for col in df.columns]
    for _, row in df.iterrows():
        cols = ','.join(df.columns)
        vals = ','.join(['%s'] * len(df.columns))
        cur.execute(f"INSERT INTO {name} ({cols}) VALUES ({vals})", tuple(row))
    conn.commit()

cur.close()
conn.close()
