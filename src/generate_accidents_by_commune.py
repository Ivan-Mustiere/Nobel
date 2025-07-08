from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, sum as _sum, avg, when, max as spark_max
import os

# -----------------------------
# 1. Initialisation
# -----------------------------
spark = SparkSession.builder.appName("AccidentsParCommune").getOrCreate()

# -----------------------------
# 2. Chargement des fichiers
# -----------------------------
caract = spark.read.csv("data/caract-2023.csv", sep=";", header=True)
vehicules = spark.read.csv("data/vehicules-2023.csv", sep=";", header=True)
usagers = spark.read.csv("data/usagers-2023.csv", sep=";", header=True)

# -----------------------------
# 3. Nettoyage & normalisation
# -----------------------------
caract = caract.filter(col("com").isNotNull())
caract = caract.withColumn("com", col("com").substr(1, 5).alias("com"))
caract = caract.withColumn("Num_Acc", col("Num_Acc").cast("string"))

# Regrouper Paris/Lyon/Marseille
def regroupe_communes_udf(code):
    if code.startswith("75"):
        return "75056"
    elif code.startswith("69") and code != "69000":
        return "69123"
    elif code.startswith("13") and code != "13000":
        return "13055"
    return code.zfill(5)

from pyspark.sql.functions import udf
from pyspark.sql.types import StringType
regroupe_udf = udf(regroupe_communes_udf, StringType())

caract = caract.withColumn("com_insee", regroupe_udf(col("com")))

vehicules = vehicules.withColumn("Num_Acc", col("Num_Acc").cast("string"))
usagers = usagers.withColumn("Num_Acc", col("Num_Acc").cast("string"))

# -----------------------------
# 4. Boucle sur les mois
# -----------------------------
output_base = "output/mois"
os.makedirs(output_base, exist_ok=True)

for mois in range(1, 13):
    mois_str = str(mois).zfill(2)

    subset = caract.filter(col("mois") == mois)

    acc_ids = subset.select("Num_Acc").distinct()

    v_sub = vehicules.join(acc_ids, on="Num_Acc", how="inner")
    u_sub = usagers.join(acc_ids, on="Num_Acc", how="inner")

    # Véhicules par accident
    veh_counts = v_sub.groupBy("Num_Acc").count().withColumnRenamed("count", "veh_count")

    # Usagers par sexe
    sex_counts = u_sub.groupBy("Num_Acc", "sexe").count().groupBy("Num_Acc").pivot("sexe").sum("count")

    # Gravité max par accident
    grav_max = u_sub.groupBy("Num_Acc").agg(spark_max("grav").alias("grav_max"))

    # Fusion
    enriched = subset.join(veh_counts, on="Num_Acc", how="left") \
                     .join(sex_counts, on="Num_Acc", how="left") \
                     .join(grav_max, on="Num_Acc", how="left")

    enriched = enriched.fillna(0, subset=["veh_count", "1", "2"])

    # Agrégation par commune
    df_month = enriched.groupBy("com_insee").agg(
        count("Num_Acc").alias("nbr_accidents"),
        _sum("veh_count").alias("nbr_vehicules"),
        _sum("1").alias("nb_hommes"),
        _sum("2").alias("nb_femmes"),
        avg("grav_max").alias("grav_moyenne")
    )

    df_month = df_month.withColumn("grav_moyenne", col("grav_moyenne").cast("double"))

    # Export CSV
    mois_folder = os.path.join(output_base, mois_str)
    os.makedirs(mois_folder, exist_ok=True)
    df_month.toPandas().round(2).to_csv(os.path.join(mois_folder, f"accidents_{mois_str}.csv"), index=False)

    print(f"✅ Spark : Fichier {mois_str} exporté")

spark.stop()
