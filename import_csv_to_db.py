import pandas as pd
from sqlalchemy import create_engine

# Nom du fichier CSV (il doit être dans le même dossier que ce script)
CSV_FILE = "Modèle_base_materiaux_complet(tableau) (1).csv"


# Nom du fichier SQLite à créer
DB_FILE = "materiaux.db"

print("📥 Étape 1 : lecture du fichier CSV...")

# On lit le CSV. Le séparateur est ";" (typique des fichiers Excel français).
df = pd.read_csv(CSV_FILE, sep=";", encoding="utf-8-sig")

print("Colonnes trouvées dans le fichier :")
print(df.columns.tolist())

# Liste des colonnes qui contiennent des nombres (mais écrits avec des virgules)
numeric_cols = [
    "masse_volumique_kg_m3",
    "conductivite_w_mk",
    "capacite_thermique_j_kgk",
    "resistance_compression_mpa",
    "module_young_gpa",
    "resistance_traction_mpa",
    "permeabilite_vapeur_mu",
    "porosite_pct",
    "contenu_recycle_pct",
    "energie_grise_mj_kg",
    "empreinte_carbone_kgco2e_kg",
    "cout_eur_m2",
    "durabilite_ans",
]

print("🧹 Étape 2 : nettoyage des nombres (virgules → points)...")

for col in numeric_cols:
    if col in df.columns:
        # On convertit en texte, remplace la virgule par un point, enlève les espaces
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .str.replace(" ", "", regex=False)
            .replace({"nan": None, "": None})
        )
        # Puis on convertit en nombres (float). Les valeurs invalides deviennent NaN.
        df[col] = pd.to_numeric(df[col], errors="coerce")

print("✅ Nombres nettoyés.")

print("🗄️ Étape 3 : création de la base SQLite...")

# Création de la connexion vers un fichier SQLite
engine = create_engine(f"sqlite:///{DB_FILE}", echo=False)

# On écrit tout le DataFrame dans une table appelée "materiaux"
df.to_sql("materiaux", con=engine, if_exists="replace", index=False)

print(f"✅ Base de données créée : {DB_FILE}")
print("✅ Table créée : materiaux")
print("👍 Tu peux maintenant l'utiliser dans l'application Streamlit.")
