import streamlit as st
import pandas as pd
import altair as alt

# =========================
# CONFIGURATION DE LA PAGE
# =========================
st.set_page_config(
    page_title="Base de données des matériaux de construction",
    page_icon="🧱",
    layout="wide"
)

# =========================
# CSS PERSONNALISÉ (thème sombre + cartes)
# =========================
st.markdown(
    """
    <style>
    .main {
        background-color: #020617;  /* fond global très sombre */
        color: #e5e7eb;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1.5rem;
    }

    .metric-card {
        background: #020617;
        padding: 0.8rem 1rem;
        border-radius: 12px;
        border: 1px solid rgba(148, 163, 184, 0.4);
    }

    /* Cartes matériaux : fond un peu plus clair que la page */
    .material-card {
        background: #0b1120;  /* différent du fond de la page */
        border-radius: 18px;
        border: 1px solid rgba(148, 163, 184, 0.35);
        box-shadow: 0 20px 25px -5px rgba(15,23,42,0.65),
                    0 10px 10px -5px rgba(15,23,42,0.7);
        margin-bottom: 1.4rem;
        padding: 0;
        overflow: hidden;
    }

    /* Bandeau de couleur quand il n'y a pas d'image */
    .material-banner {
        height: 140px;
        width: 100%;
        background: linear-gradient(135deg, #22c55e, #16a34a, #14532d);
    }

    /* Wrapper pour toutes les images => hauteur uniforme */
    .material-img-wrapper {
        height: 140px;               /* hauteur fixe */
        width: 100%;
        background: linear-gradient(135deg, #22c55e, #16a34a, #14532d);
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
    }

    .material-img {
        width: 100%;
        height: 100%;
        object-fit: cover;           /* recadre pour remplir sans déformer */
    }

    .material-content {
        padding: 0.9rem 1.1rem 1.1rem 1.1rem;
    }

    .material-title {
        font-size: 1.05rem;
        font-weight: 600;
        margin-bottom: 0.1rem;
    }

    .material-subtitle {
        font-size: 0.85rem;
        color: #9ca3af;
        margin-bottom: 0.5rem;
    }

    .section-title {
        font-size: 0.75rem;
        letter-spacing: .08em;
        text-transform: uppercase;
        color: #22c55e;
        border-bottom: 1px solid #22c55e;
        padding-bottom: 0.15rem;
        margin-bottom: 0.25rem;
        margin-top: 0.4rem;
    }

    .metric-label {
        font-size: 0.8rem;
        color: #9ca3af;
        margin-bottom: 0.1rem;
    }

    .metric-value {
        font-size: 0.9rem;
        font-weight: 500;
        margin-bottom: 0.25rem;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #020617;
        border-radius: 999px;
        padding: 0.5rem 1rem;
        color: #e5e7eb;
        border: 1px solid rgba(148, 163, 184, 0.4);
    }

    .stTabs [aria-selected="true"] {
        border-color: #22c55e !important;
        background: rgba(34,197,94,0.09) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
# CHARGEMENT DES DONNÉES
# =========================

CSV_FILE = "materiaux_clean.csv"  # ton CSV nettoyé

@st.cache_data
def load_data(csv_file: str) -> pd.DataFrame:
    df = pd.read_csv(csv_file, sep=";", encoding="utf-8-sig")

    # Supprimer les colonnes parasites Unnamed
    unnamed = [c for c in df.columns if c.startswith("Unnamed")]
    if unnamed:
        df = df.drop(columns=unnamed)

    # Nettoyage minimal texte
    for col in df.select_dtypes(include="object").columns:
        df[col] = (
            df[col]
            .astype(str)
            .str.strip()
            .str.replace(r"\s+", " ", regex=True)
            .replace({"nan": ""})
        )

    return df

def add_eco_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ajoute une colonne 'eco_score' (0-100) basée sur :
    - cout_eur_m2 (plus c'est bas, mieux c'est)
    - empreinte_carbone_kgco2e_kg (plus c'est bas, mieux c'est)
    - conductivite_w_mk (plus c'est bas, mieux c'est)
    - contenu_recycle_pct (plus c'est haut, mieux c'est)
    """
    df = df.copy()

    for col in ["cout_eur_m2", "empreinte_carbone_kgco2e_kg",
                "contenu_recycle_pct", "conductivite_w_mk"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    scores = []
    # Coût (bas = bien)
    if "cout_eur_m2" in df.columns and df["cout_eur_m2"].notna().sum() > 0:
        col = df["cout_eur_m2"]
        mn, mx = col.min(), col.max()
        if mx > mn:
            scores.append((mx - col) / (mx - mn))

    # CO2 (bas = bien)
    if "empreinte_carbone_kgco2e_kg" in df.columns and df["empreinte_carbone_kgco2e_kg"].notna().sum() > 0:
        col = df["empreinte_carbone_kgco2e_kg"]
        mn, mx = col.min(), col.max()
        if mx > mn:
            scores.append((mx - col) / (mx - mn))

    # Lambda (bas = bien)
    if "conductivite_w_mk" in df.columns and df["conductivite_w_mk"].notna().sum() > 0:
        col = df["conductivite_w_mk"]
        mn, mx = col.min(), col.max()
        if mx > mn:
            scores.append((mx - col) / (mx - mn))

    # Contenu recyclé (haut = bien)
    if "contenu_recycle_pct" in df.columns and df["contenu_recycle_pct"].notna().sum() > 0:
        col = df["contenu_recycle_pct"]
        mn, mx = col.min(), col.max()
        if mx > mn:
            scores.append((col - mn) / (mx - mn))

    if scores:
        eco_raw = sum(scores) / len(scores)
        df["eco_score"] = (eco_raw * 100).round(1)
    else:
        df["eco_score"] = None

    return df

df = load_data(CSV_FILE)
df = add_eco_score(df)

# =========================
# PETITES FONCTIONS UTILES
# =========================
def get_range(df, column, fallback_min=0.0, fallback_max=1.0):
    """Retourne (min, max) réels d'une colonne numérique."""
    if column in df.columns and df[column].notna().any():
        real_min = float(df[column].min())
        real_max = float(df[column].max())
        if real_min == real_max:
            real_min = real_min * 0.9
            real_max = real_max * 1.1
        return real_min, real_max
    return fallback_min, fallback_max


def fmt(val, suffix=""):
    """Formatage nombre + suffixe, ou tiret si NaN."""
    try:
        if pd.isna(val):
            return "—"
        val = float(val)
        return f"{val:.2f}{suffix}"
    except Exception:
        return "—"


def get_valid_image_url(row) -> str:
    """Retourne une URL d'image propre ou '' si rien de valide."""
    url = str(row.get("image_url", "")).strip()
    if url.lower().startswith("http://") or url.lower().startswith("https://"):
        return url
    return ""


# =========================
# SIDEBAR : FILTRES
# =========================
st.sidebar.title("🧹 Filtres matériaux")

# Recherche texte
search_text = st.sidebar.text_input(
    "Recherche par nom ou description",
    placeholder="ex : béton, bois, isolant..."
)

st.sidebar.markdown("### Classification")

# Type (multi-sélection)
type_options = sorted(df["type"].dropna().unique().tolist()) if "type" in df.columns else []
selected_types = st.sidebar.multiselect(
    "Type principal",
    options=type_options,
    help="Sélectionne un ou plusieurs types de matériaux."
)

# Sous-type dépendant des types choisis
if selected_types and "type" in df.columns:
    df_for_subtypes = df[df["type"].isin(selected_types)]
else:
    df_for_subtypes = df

if "sous_type" in df_for_subtypes.columns:
    subtype_options = sorted(df_for_subtypes["sous_type"].dropna().unique().tolist())
else:
    subtype_options = []

selected_subtypes = st.sidebar.multiselect(
    "Sous-type",
    options=subtype_options,
    help="Liste filtrée selon les types sélectionnés."
)

st.sidebar.markdown("### Propriétés physiques")

dens_min, dens_max = get_range(df, "masse_volumique_kg_m3", 0.0, 8000.0)
density_range = st.sidebar.slider(
    "Densité (kg/m³)",
    min_value=float(dens_min),
    max_value=float(dens_max),
    value=(float(dens_min), float(dens_max)),
    step=0.1,
    key="density_slider",
)

lambda_min, lambda_max = get_range(df, "conductivite_w_mk", 0.0, 10.0)
lambda_range = st.sidebar.slider(
    "Conductivité thermique λ (W/m·K)",
    min_value=float(lambda_min),
    max_value=float(lambda_max),
    value=(float(lambda_min), float(lambda_max)),
    step=0.01,
    key="lambda_slider",
)

st.sidebar.markdown("### Origine")

if "pays_origine" in df.columns:
    country_options = sorted(df["pays_origine"].dropna().unique().tolist())
else:
    country_options = []
selected_countries = st.sidebar.multiselect("Pays", country_options)

if "fabricant" in df.columns:
    manufacturer_options = sorted(df["fabricant"].dropna().unique().tolist())
else:
    manufacturer_options = []
selected_manufacturers = st.sidebar.multiselect("Fabricant", manufacturer_options)

if st.sidebar.button("🔄 Réinitialiser tous les filtres"):
    st.experimental_rerun()

# =========================
# APPLICATION DES FILTRES
# =========================
filtered = df.copy()

if search_text:
    mask_name = filtered["nom"].astype(str).str.contains(search_text, case=False, na=False) if "nom" in filtered.columns else False
    mask_desc = filtered["description"].astype(str).str.contains(search_text, case=False, na=False) if "description" in filtered.columns else False
    filtered = filtered[mask_name | mask_desc]

if selected_types and "type" in filtered.columns:
    filtered = filtered[filtered["type"].isin(selected_types)]

if selected_subtypes and "sous_type" in filtered.columns:
    filtered = filtered[filtered["sous_type"].isin(selected_subtypes)]

# On garde aussi les NaN
if "masse_volumique_kg_m3" in filtered.columns:
    mask_density = (
        filtered["masse_volumique_kg_m3"].between(density_range[0], density_range[1])
        | filtered["masse_volumique_kg_m3"].isna()
    )
    filtered = filtered[mask_density]

if "conductivite_w_mk" in filtered.columns:
    mask_lambda = (
        filtered["conductivite_w_mk"].between(lambda_range[0], lambda_range[1])
        | filtered["conductivite_w_mk"].isna()
    )
    filtered = filtered[mask_lambda]

if selected_countries and "pays_origine" in filtered.columns:
    filtered = filtered[filtered["pays_origine"].isin(selected_countries)]

if selected_manufacturers and "fabricant" in filtered.columns:
    filtered = filtered[filtered["fabricant"].isin(selected_manufacturers)]

# =========================
# EN-TÊTE + MÉTRIQUES
# =========================
header_col1, header_col2 = st.columns([3, 2])

with header_col1:
    st.markdown("### 🧱 Base de données des matériaux de construction")
    st.markdown(
        "<h1 style='margin-top:-8px; color:#bbf7d0;'>Explorer & comparer les matériaux</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color:#9ca3af; max-width:650px;'>Interface interactive pour comparer les propriétés physiques, thermiques, mécaniques et environnementales des matériaux de construction.</p>",
        unsafe_allow_html=True,
    )

with header_col2:
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.caption("Matériaux")
        st.subheader(len(df))
        st.markdown("</div>", unsafe_allow_html=True)
    with m2:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.caption("Filtrés")
        st.subheader(len(filtered))
        st.markdown("</div>", unsafe_allow_html=True)
    with m3:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.caption("Types")
        if "type" in df.columns:
            st.subheader(df["type"].nunique())
        else:
            st.subheader("—")
        st.markdown("</div>", unsafe_allow_html=True)
    with m4:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.caption("Pays")
        if "pays_origine" in df.columns:
            st.subheader(df["pays_origine"].nunique())
        else:
            st.subheader("—")
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# Petit résumé stats sur les matériaux filtrés
if not filtered.empty:
    stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
    with stats_col1:
        st.caption("Densité moyenne (filtré)")
        if "masse_volumique_kg_m3" in filtered.columns:
            st.write(f"{filtered['masse_volumique_kg_m3'].mean():.1f} kg/m³")
        else:
            st.write("—")
    with stats_col2:
        st.caption("λ moyenne (filtré)")
        if "conductivite_w_mk" in filtered.columns:
            st.write(f"{filtered['conductivite_w_mk'].mean():.3f} W/m·K")
        else:
            st.write("—")
    with stats_col3:
        st.caption("Empreinte CO₂ moyenne (filtré)")
        if "empreinte_carbone_kgco2e_kg" in filtered.columns:
            st.write(f"{filtered['empreinte_carbone_kgco2e_kg'].mean():.2f} kgCO₂e/kg")
        else:
            st.write("—")
    with stats_col4:
        st.caption("Éco-score moyen")
        if "eco_score" in filtered.columns and filtered["eco_score"].notna().any():
            st.write(f"{filtered['eco_score'].mean():.1f} / 100")
        else:
            st.write("—")

# =========================
# ONGLETS
# =========================
tab1, tab2, tab3, tab4 = st.tabs(
    ["📂 Parcours des matériaux", "📊 Comparaison", "📈 Statistiques", "🗂 Gestion"]
)

# =========================
# ONGLET 1 : PARCOURS
# =========================
with tab1:
    st.markdown(f"### {len(filtered)} matériau(x) affiché(s)")

    sort_option = st.selectbox(
        "Trier par",
        ["Nom (A→Z)", "Densité (croissante)", "Densité (décroissante)",
         "λ (croissante)", "λ (décroissante)", "Éco-score (meilleur en premier)"],
        key="sort_explorer",
    )

    filtered_sorted = filtered.copy()
    if sort_option == "Nom (A→Z)" and "nom" in filtered.columns:
        filtered_sorted = filtered.sort_values("nom", ascending=True)
    elif sort_option == "Densité (croissante)" and "masse_volumique_kg_m3" in filtered.columns:
        filtered_sorted = filtered.sort_values("masse_volumique_kg_m3", ascending=True)
    elif sort_option == "Densité (décroissante)" and "masse_volumique_kg_m3" in filtered.columns:
        filtered_sorted = filtered.sort_values("masse_volumique_kg_m3", ascending=False)
    elif sort_option == "λ (croissante)" and "conductivite_w_mk" in filtered.columns:
        filtered_sorted = filtered.sort_values("conductivite_w_mk", ascending=True)
    elif sort_option == "λ (décroissante)" and "conductivite_w_mk" in filtered.columns:
        filtered_sorted = filtered.sort_values("conductivite_w_mk", ascending=False)
    elif sort_option == "Éco-score (meilleur en premier)" and "eco_score" in filtered.columns:
        filtered_sorted = filtered.sort_values("eco_score", ascending=False)

    # bouton export CSV
    csv_bytes = filtered_sorted.to_csv(index=False, sep=";").encode("utf-8")
    st.download_button(
        "📥 Exporter les données filtrées en CSV",
        data=csv_bytes,
        file_name="materiaux_filtres.csv",
        mime="text/csv",
    )

    st.write("")

    # Affichage en grille : 2 cartes par ligne
    records = filtered_sorted.to_dict("records")
    for i in range(0, len(records), 2):
        ligne = records[i:i+2]
        cols = st.columns(2)
        for col, row in zip(cols, ligne):
            with col:
                st.markdown("<div class='material-card'>", unsafe_allow_html=True)

                # Image avec hauteur uniforme ou bandeau par défaut
                img_url = get_valid_image_url(row)
                if img_url:
                    st.markdown(
                        f"""
                        <div class="material-img-wrapper">
                            <img src="{img_url}" class="material-img" alt="{row.get('nom', 'Matériau')}">
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown("<div class='material-banner'></div>", unsafe_allow_html=True)

                st.markdown("<div class='material-content'>", unsafe_allow_html=True)

                # Titre + sous-titre
                st.markdown(
                    f"<div class='material-title'>{row.get('nom', 'Matériau')}</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<div class='material-subtitle'>{row.get('type', '—')} → {row.get('sous_type', '—')}</div>",
                    unsafe_allow_html=True,
                )

                # Description courte
                desc = row.get("description")
                if isinstance(desc, str) and desc.strip():
                    if len(desc) > 160:
                        short = desc[:160].rstrip() + "..."
                    else:
                        short = desc
                    st.markdown(f"**Résumé :** {short}")

                # Résumé de 4 propriétés clés en frontal
                col_key1, col_key2, col_key3, col_key4 = st.columns(4)
                with col_key1:
                    st.markdown("<div class='metric-label'>Densité</div>", unsafe_allow_html=True)
                    st.markdown(
                        f"<div class='metric-value'>{fmt(row.get('masse_volumique_kg_m3'), ' kg/m³')}</div>",
                        unsafe_allow_html=True,
                    )
                with col_key2:
                    st.markdown("<div class='metric-label'>λ</div>", unsafe_allow_html=True)
                    st.markdown(
                        f"<div class='metric-value'>{fmt(row.get('conductivite_w_mk'), ' W/m·K')}</div>",
                        unsafe_allow_html=True,
                    )
                with col_key3:
                    st.markdown("<div class='metric-label'>CO₂</div>", unsafe_allow_html=True)
                    st.markdown(
                        f"<div class='metric-value'>{fmt(row.get('empreinte_carbone_kgco2e_kg'), ' kgCO₂e/kg')}</div>",
                        unsafe_allow_html=True,
                    )
                with col_key4:
                    st.markdown("<div class='metric-label'>Éco-score</div>", unsafe_allow_html=True)
                    eco = row.get("eco_score")
                    eco_txt = "—" if pd.isna(eco) else f"{eco:.1f}/100"
                    st.markdown(
                        f"<div class='metric-value'>{eco_txt}</div>",
                        unsafe_allow_html=True,
                    )

                # DÉTAILS DANS UN EXPANDER
                with st.expander("🔍 Afficher plus de détails"):
                    st.markdown("<div class='section-title'>Propriétés physiques</div>", unsafe_allow_html=True)
                    col_p1, col_p2 = st.columns(2)
                    with col_p1:
                        st.markdown("<div class='metric-label'>Densité</div>", unsafe_allow_html=True)
                        st.markdown(
                            f"<div class='metric-value'>{fmt(row.get('masse_volumique_kg_m3'), ' kg/m³')}</div>",
                            unsafe_allow_html=True,
                        )
                    with col_p2:
                        st.markdown("<div class='metric-label'>Conductivité thermique λ</div>", unsafe_allow_html=True)
                        st.markdown(
                            f"<div class='metric-value'>{fmt(row.get('conductivite_w_mk'), ' W/m·K')}</div>",
                            unsafe_allow_html=True,
                        )

                    st.markdown("<div class='section-title'>Thermique & mécanique</div>", unsafe_allow_html=True)
                    col_tm1, col_tm2 = st.columns(2)
                    with col_tm1:
                        st.markdown("<div class='metric-label'>Résistance en compression</div>", unsafe_allow_html=True)
                        st.markdown(
                            f"<div class='metric-value'>{fmt(row.get('resistance_compression_mpa'), ' MPa')}</div>",
                            unsafe_allow_html=True,
                        )
                    with col_tm2:
                        st.markdown("<div class='metric-label'>Capacité thermique massique</div>", unsafe_allow_html=True)
                        st.markdown(
                            f"<div class='metric-value'>{fmt(row.get('capacite_thermique_j_kgk'), ' J/kg·K')}</div>",
                            unsafe_allow_html=True,
                        )

                    st.markdown("<div class='section-title'>Environnement & durabilité</div>", unsafe_allow_html=True)
                    col_s1, col_s2 = st.columns(2)
                    with col_s1:
                        st.markdown("<div class='metric-label'>Contenu recyclé</div>", unsafe_allow_html=True)
                        st.markdown(
                            f"<div class='metric-value'>{fmt(row.get('contenu_recycle_pct'), ' %')}</div>",
                            unsafe_allow_html=True,
                        )
                    with col_s2:
                        st.markdown("<div class='metric-label'>Empreinte carbone</div>", unsafe_allow_html=True)
                        st.markdown(
                            f"<div class='metric-value'>{fmt(row.get('empreinte_carbone_kgco2e_kg'), ' kgCO₂e/kg')}</div>",
                            unsafe_allow_html=True,
                        )
                    st.markdown("<div class='metric-label'>Éco-score global</div>", unsafe_allow_html=True)
                    st.markdown(
                        f"<div class='metric-value'>{eco_txt}</div>",
                        unsafe_allow_html=True,
                    )

                    st.markdown("<div class='section-title'>Origine</div>", unsafe_allow_html=True)
                    src_parts = []
                    if isinstance(row.get("fabricant"), str) and row["fabricant"].strip():
                        src_parts.append(f"Fabricant : {row['fabricant']}")
                    if isinstance(row.get("pays_origine"), str) and row["pays_origine"].strip():
                        src_parts.append(f"Pays : {row['pays_origine']}")
                    if isinstance(row.get("origine"), str) and row["origine"].strip():
                        src_parts.append(f"Origine : {row['origine']}")
                    if src_parts:
                        st.markdown(" | ".join(src_parts))

                st.markdown("</div></div>", unsafe_allow_html=True)

# =========================
# ONGLET 2 : COMPARAISON
# =========================
with tab2:
    st.markdown("### 📊 Comparer plusieurs matériaux")

    if "nom" in df.columns:
        options = df["nom"].tolist()
    else:
        options = []

    selected_for_compare = st.multiselect(
        "Sélectionne les matériaux à comparer (max 6)",
        options=options,
        max_selections=6,
    )

    if not selected_for_compare:
        st.info("Sélectionne au moins un matériau dans la liste ci-dessus pour lancer la comparaison.")
    else:
        comp_df = df[df["nom"].isin(selected_for_compare)].copy()

        cols_to_show = [
            "nom", "type", "sous_type",
            "masse_volumique_kg_m3",
            "conductivite_w_mk",
            "resistance_compression_mpa",
            "capacite_thermique_j_kgk",
            "contenu_recycle_pct",
            "empreinte_carbone_kgco2e_kg",
            "cout_eur_m2",
            "eco_score",
            "pays_origine",
        ]
        cols_to_show = [c for c in cols_to_show if c in comp_df.columns]

        st.markdown("#### Vue tableau")
        st.dataframe(comp_df[cols_to_show].set_index("nom"), use_container_width=True)

        st.markdown("---")
        st.markdown("#### Profils graphiques")

        # Barres horizontales densité
        if "masse_volumique_kg_m3" in comp_df.columns:
            chart_density = (
                alt.Chart(comp_df)
                .mark_bar()
                .encode(
                    x=alt.X("masse_volumique_kg_m3:Q", title="Densité (kg/m³)"),
                    y=alt.Y("nom:N", sort="-x", title="Matériau"),
                    color=alt.Color("nom:N", legend=None),
                    tooltip=["nom", "masse_volumique_kg_m3"],
                )
                .properties(height=250, title="Densité des matériaux (barres horizontales)")
            )
        else:
            chart_density = None

        # Barres λ
        if "conductivite_w_mk" in comp_df.columns:
            chart_lambda = (
                alt.Chart(comp_df)
                .mark_bar()
                .encode(
                    x=alt.X("nom:N", sort="-y", title="Matériau"),
                    y=alt.Y("conductivite_w_mk:Q", title="λ (W/m·K)"),
                    color=alt.Color("nom:N", legend=None),
                    tooltip=["nom", "conductivite_w_mk"],
                )
                .properties(height=250, title="Comparaison des conductivités λ")
                .interactive()
            )
        else:
            chart_lambda = None

        # Nuage densité vs λ pour les matériaux sélectionnés
        if "masse_volumique_kg_m3" in comp_df.columns and "conductivite_w_mk" in comp_df.columns:
            scatter_sel = (
                alt.Chart(comp_df)
                .mark_circle(size=180)
                .encode(
                    x=alt.X("masse_volumique_kg_m3:Q", title="Densité (kg/m³)"),
                    y=alt.Y("conductivite_w_mk:Q", title="λ (W/m·K)"),
                    color=alt.Color("nom:N", title="Matériau"),
                    tooltip=["nom", "type", "masse_volumique_kg_m3", "conductivite_w_mk"],
                )
                .properties(height=280, title="Positionnement λ / densité des matériaux sélectionnés")
                .interactive()
            )
        else:
            scatter_sel = None

        c1, c2 = st.columns(2)
        with c1:
            if chart_density is not None:
                st.altair_chart(chart_density, use_container_width=True)
            else:
                st.write("Données densité manquantes.")
        with c2:
            if chart_lambda is not None:
                st.altair_chart(chart_lambda, use_container_width=True)
            else:
                st.write("Données λ manquantes.")

        st.markdown("#### Nuage de points détaillé")
        if scatter_sel is not None:
            st.altair_chart(scatter_sel, use_container_width=True)
        else:
            st.write("Données insuffisantes pour le nuage de points.")

        # Éco-score comparatif
        if "eco_score" in comp_df.columns and comp_df["eco_score"].notna().any():
            st.markdown("#### Éco-score des matériaux sélectionnés")
            chart_eco = (
                alt.Chart(comp_df)
                .mark_bar()
                .encode(
                    x=alt.X("nom:N", sort="-y", title="Matériau"),
                    y=alt.Y("eco_score:Q", title="Éco-score (0–100)"),
                    color=alt.Color("nom:N", legend=None),
                    tooltip=["nom", "eco_score"],
                )
                .properties(height=250)
            )
            st.altair_chart(chart_eco, use_container_width=True)

        st.markdown("---")
        st.markdown("### 🧱 Scénario de paroi (R thermique & éco-score)")

        st.write(
            "Compose une paroi en choisissant plusieurs couches de matériaux et leurs épaisseurs. "
            "L’application calcule la **résistance thermique totale R** et un **éco-score moyen de la paroi**."
        )

        nb_couches = st.number_input(
            "Nombre de couches",
            min_value=1,
            max_value=6,
            value=3,
            step=1,
            key="nb_couches_paroi",
        )

        couches = []
        for i in range(int(nb_couches)):
            cmat, cep = st.columns([2, 1])
            with cmat:
                mat = st.selectbox(
                    f"Couche {i+1} – matériau",
                    options=options,
                    key=f"paroi_mat_{i}",
                )
            with cep:
                ep_cm = st.number_input(
                    f"Épaisseur {i+1} (cm)",
                    min_value=0.0,
                    max_value=200.0,
                    value=10.0,
                    step=0.5,
                    key=f"paroi_ep_{i}",
                )

            if mat:
                row_mat = df[df["nom"] == mat].iloc[0]
                lam = pd.to_numeric(row_mat.get("conductivite_w_mk"), errors="coerce")
                eco = pd.to_numeric(row_mat.get("eco_score"), errors="coerce")
                if pd.notna(lam) and lam > 0:
                    R_i = (ep_cm / 100.0) / lam
                else:
                    R_i = None
                couches.append(
                    {
                        "Couche": i + 1,
                        "Matériau": mat,
                        "Épaisseur (cm)": ep_cm,
                        "λ (W/m·K)": lam,
                        "R (m²K/W)": R_i,
                        "Éco-score": eco,
                    }
                )

        if couches:
            df_paroi = pd.DataFrame(couches)

            R_total = df_paroi["R (m²K/W)"].dropna().sum()
            # Éco-score moyen pondéré par l'épaisseur
            if df_paroi["Épaisseur (cm)"].sum() > 0 and df_paroi["Éco-score"].notna().any():
                eco_paroi = (
                    (df_paroi["Épaisseur (cm)"] * df_paroi["Éco-score"])
                    .sum()
                    / df_paroi["Épaisseur (cm)"].sum()
                )
            else:
                eco_paroi = None

            st.markdown("#### Résultats du scénario")
            colR, colE = st.columns(2)
            with colR:
                st.markdown("**Résistance thermique totale R :**")
                if R_total > 0:
                    st.markdown(f"👉 **R = {R_total:.3f} m²K/W**")
                else:
                    st.markdown("Données λ insuffisantes pour calculer R.")
            with colE:
                st.markdown("**Éco-score moyen de la paroi :**")
                if eco_paroi is not None:
                    st.markdown(f"👉 **{eco_paroi:.1f} / 100**")
                else:
                    st.markdown("Données éco-score insuffisantes.")

            st.markdown("#### Détail des couches")
            st.dataframe(df_paroi, use_container_width=True)

# =========================
# ONGLET 3 : STATISTIQUES
# =========================
with tab3:
    st.markdown("### 🌱 Statistiques globales (focus biosourcé)")

    def is_biosourced(df_):
        mask = pd.Series(False, index=df_.index)
        for col in ["sous_type", "type", "origine"]:
            if col in df_.columns:
                mask = mask | df_[col].astype(str).str.contains("biosour", case=False, na=False)
        return mask

    if not df.empty:
        bio_mask = is_biosourced(df)
        df_bio = df[bio_mask].copy()
        df_other = df[~bio_mask].copy()
    else:
        df_bio = df_other = df

    total = len(df)
    nb_bio = len(df_bio)
    share_bio = (nb_bio / total * 100) if total > 0 else 0

    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        st.metric("Matériaux totaux", total)
    with mc2:
        st.metric("Matériaux biosourcés", nb_bio)
    with mc3:
        st.metric("Part de biosourcé", f"{share_bio:.1f} %")

    st.markdown("---")

    st.markdown("#### Propriétés moyennes : biosourcé vs autres")

    def avg_or_none(df_, col):
        if col in df_.columns and df_[col].notna().any():
            return df_[col].mean()
        return None

    dens_bio = avg_or_none(df_bio, "masse_volumique_kg_m3")
    dens_other = avg_or_none(df_other, "masse_volumique_kg_m3")
    lambda_bio = avg_or_none(df_bio, "conductivite_w_mk")
    lambda_other = avg_or_none(df_other, "conductivite_w_mk")
    co2_bio = avg_or_none(df_bio, "empreinte_carbone_kgco2e_kg")
    co2_other = avg_or_none(df_other, "empreinte_carbone_kgco2e_kg")
    eco_bio = avg_or_none(df_bio, "eco_score")
    eco_other = avg_or_none(df_other, "eco_score")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.caption("Densité moyenne (kg/m³)")
        if dens_bio is not None and dens_other is not None:
            st.write(f"🌱 Biosourcé : **{dens_bio:.0f}**")
            st.write(f"🏗️ Autres   : **{dens_other:.0f}**")
        else:
            st.write("Données insuffisantes")
    with c2:
        st.caption("λ moyenne (W/m·K)")
        if lambda_bio is not None and lambda_other is not None:
            st.write(f"🌱 Biosourcé : **{lambda_bio:.3f}**")
            st.write(f"🏗️ Autres   : **{lambda_other:.3f}**")
        else:
            st.write("Données insuffisantes")
    with c3:
        st.caption("Empreinte CO₂ moyenne (kgCO₂e/kg)")
        if co2_bio is not None and co2_other is not None:
            st.write(f"🌱 Biosourcé : **{co2_bio:.2f}**")
            st.write(f"🏗️ Autres   : **{co2_other:.2f}**")
        else:
            st.write("Données insuffisantes")
    with c4:
        st.caption("Éco-score moyen")
        if eco_bio is not None and eco_other is not None:
            st.write(f"🌱 Biosourcé : **{eco_bio:.1f} / 100**")
            st.write(f"🏗️ Autres   : **{eco_other:.1f} / 100**")
        else:
            st.write("Données insuffisantes")

    st.markdown("---")
    st.markdown("#### Répartition & graphiques")

    col_a, col_b = st.columns(2)

    with col_a:
        st.caption("Nombre de matériaux par type")
        if "type" in df.columns:
            counts_type = (
                df.groupby("type")
                .size()
                .reset_index(name="nb_materiaux")
            )

            chart_type = (
                alt.Chart(counts_type)
                .mark_bar()
                .encode(
                    x=alt.X("type:N", sort="-y", title="Type"),
                    y=alt.Y("nb_materiaux:Q", title="Nombre de matériaux"),
                    color=alt.Color("type:N", legend=None),
                    tooltip=["type", "nb_materiaux"],
                )
                .properties(height=300)
            )

            st.altair_chart(chart_type, use_container_width=True)
        else:
            st.write("Colonne 'type' absente des données.")

    with col_b:
        st.caption("λ en fonction de la densité (coloré par type)")
        if "masse_volumique_kg_m3" in df.columns and "conductivite_w_mk" in df.columns:
            scatter = (
                alt.Chart(df)
                .mark_circle(size=80)
                .encode(
                    x=alt.X("masse_volumique_kg_m3:Q", title="Densité (kg/m³)"),
                    y=alt.Y("conductivite_w_mk:Q", title="λ (W/m·K)"),
                    color="type:N" if "type" in df.columns else alt.value("steelblue"),
                    tooltip=["nom", "type", "masse_volumique_kg_m3", "conductivite_w_mk"],
                )
                .properties(height=300)
            )
            st.altair_chart(scatter, use_container_width=True)
        else:
            st.write("Données insuffisantes pour le nuage de points.")

    st.markdown("#### λ biosourcé par type")
    if not df_bio.empty and "type" in df_bio.columns and "conductivite_w_mk" in df_bio.columns:
        lambda_by_type_bio = (
            df_bio.groupby("type")["conductivite_w_mk"]
            .mean()
            .reset_index(name="lambda_mean")
        )
        chart_bio = (
            alt.Chart(lambda_by_type_bio)
            .mark_bar()
            .encode(
                x=alt.X("type:N", title="Type"),
                y=alt.Y("lambda_mean:Q", title="λ moyen (W/m·K)"),
                color="type:N",
                tooltip=["type", "lambda_mean"],
            )
            .properties(height=300)
        )
        st.altair_chart(chart_bio, use_container_width=True)
    else:
        st.write("Aucun matériau biosourcé permettant de tracer λ par type.")

    st.markdown("#### Distribution des éco-scores")
    if "eco_score" in df.columns and df["eco_score"].notna().any():
        eco_hist = (
            alt.Chart(df.dropna(subset=["eco_score"]))
            .mark_bar()
            .encode(
                x=alt.X("eco_score:Q", bin=alt.Bin(maxbins=15), title="Éco-score (0–100)"),
                y=alt.Y("count():Q", title="Nombre de matériaux"),
            )
            .properties(height=250)
        )
        st.altair_chart(eco_hist, use_container_width=True)
    else:
        st.write("Pas encore assez de données éco-score pour tracer une distribution.")

# =========================
# ONGLET 4 : GESTION (explorateur)
# =========================
with tab4:
    st.markdown("### 🗂 Gestion / exploration de la base")

    st.write(
        "Cet onglet permet de jeter un coup d’œil **brut** à la base de données : "
        "recherche rapide, filtrage par type et export."
    )

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        search_raw = st.text_input("🔎 Recherche texte (toutes colonnes)", "")
    with col_f2:
        type_raw = st.multiselect(
            "Filtrer par type",
            options=sorted(df["type"].dropna().unique()) if "type" in df.columns else [],
        )

    df_manage = df.copy()

    if search_raw:
        mask_any = pd.Series(False, index=df_manage.index)
        for col in df_manage.columns:
            mask_any = mask_any | df_manage[col].astype(str).str.contains(search_raw, case=False, na=False)
        df_manage = df_manage[mask_any]

    if type_raw and "type" in df_manage.columns:
        df_manage = df_manage[df_manage["type"].isin(type_raw)]

    st.markdown(f"**{len(df_manage)} ligne(s)** après filtrage.")
    st.dataframe(df_manage, use_container_width=True, height=400)

    csv_manage = df_manage.to_csv(index=False, sep=";").encode("utf-8")
    st.download_button(
        "📤 Exporter la vue filtrée (CSV brut)",
        data=csv_manage,
        file_name="materiaux_gestion.csv",
        mime="text/csv",
    )

    st.markdown(
        "> Pour un vrai module d’édition (ajout / modification avec sauvegarde dans le CSV), "
        "> il faudrait ajouter une couche de gestion de fichiers côté serveur. "
        "Ici, on reste sur une exploration sécurisée de la base."
    )
