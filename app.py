import streamlit as st
import pandas as pd
import altair as alt

# =========================
# CONFIG PAGE
# =========================
st.set_page_config(
    page_title="Construction Materials Database",
    page_icon="🧱",
    layout="wide"
)

# =========================
# CUSTOM CSS (dark UI)
# =========================
st.markdown(
    """
    <style>
    .main {
        background-color: #020617;
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

    .material-card {
        background: #020617;
        border-radius: 18px;
        border: 1px solid rgba(148, 163, 184, 0.35);
        box-shadow: 0 20px 25px -5px rgba(15,23,42,0.65),
                    0 10px 10px -5px rgba(15,23,42,0.7);
        margin-bottom: 1.4rem;
        padding: 0;
        overflow: hidden;
    }

    .material-banner {
        height: 140px;
        background: linear-gradient(120deg, #4f46e5, #ec4899, #f97316);
    }

    .material-content {
        padding: 1.1rem 1.4rem 1.3rem 1.4rem;
    }

    .material-title {
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: 0.1rem;
    }

    .material-subtitle {
        font-size: 0.9rem;
        color: #9ca3af;
        margin-bottom: 0.9rem;
    }

    .section-title {
        font-size: 0.8rem;
        letter-spacing: .08em;
        text-transform: uppercase;
        color: #60a5fa;
        border-bottom: 1px solid #1d4ed8;
        padding-bottom: 0.25rem;
        margin-bottom: 0.4rem;
        margin-top: 0.4rem;
    }

    .metric-label {
        font-size: 0.8rem;
        color: #9ca3af;
        margin-bottom: 0.15rem;
    }

    .metric-value {
        font-size: 0.95rem;
        font-weight: 500;
        margin-bottom: 0.35rem;
    }

    .chip {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 0.7rem;
        margin-right: 4px;
        margin-bottom: 4px;
        background: rgba(148, 163, 184, 0.16);
        color: #e5e7eb;
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
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
# LOAD DATA FROM CSV
# =========================

# 👉 Mets ici le NOM EXACT de ton CSV arrondi (celui que tu utilises)
CSV_FILE = "materiaux_clean.csv"   # par ex: materiaux_filled_rounded.csv renommé

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

df = load_data(CSV_FILE)

# =========================
# SMALL UTILS
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
    # On considère valide si ça commence par http ou https
    if url.lower().startswith("http://") or url.lower().startswith("https://"):
        return url
    return ""


# =========================
# SIDEBAR FILTERS
# =========================
st.sidebar.title("🧹 Filter Materials")

# Search by name or description
search_text = st.sidebar.text_input(
    "Search by name or description",
    placeholder="e.g., concrete, wood, insulation..."
)

st.sidebar.markdown("### Material Type")

# Type (multi-select)
type_options = sorted(df["type"].dropna().unique().tolist()) if "type" in df.columns else []
selected_types = st.sidebar.multiselect(
    "Type",
    options=type_options,
    help="Select one or more main material types."
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
    "Sub-Type",
    options=subtype_options,
    help="Filtered based on selected types."
)

st.sidebar.markdown("### Physical Properties")

dens_min, dens_max = get_range(df, "masse_volumique_kg_m3", 0.0, 8000.0)
density_range = st.sidebar.slider(
    "Density (kg/m³)",
    min_value=float(dens_min),
    max_value=float(dens_max),
    value=(float(dens_min), float(dens_max)),
    step=0.1,
    key="density_slider",
)

lambda_min, lambda_max = get_range(df, "conductivite_w_mk", 0.0, 10.0)
lambda_range = st.sidebar.slider(
    "Thermal Conductivity λ (W/m·K)",
    min_value=float(lambda_min),
    max_value=float(lambda_max),
    value=(float(lambda_min), float(lambda_max)),
    step=0.01,
    key="lambda_slider",
)

st.sidebar.markdown("### Source")

if "pays_origine" in df.columns:
    country_options = sorted(df["pays_origine"].dropna().unique().tolist())
else:
    country_options = []
selected_countries = st.sidebar.multiselect("Country", country_options)

if "fabricant" in df.columns:
    manufacturer_options = sorted(df["fabricant"].dropna().unique().tolist())
else:
    manufacturer_options = []
selected_manufacturers = st.sidebar.multiselect("Manufacturer", manufacturer_options)

if st.sidebar.button("Reset All Filters"):
    st.experimental_rerun()

# =========================
# APPLY FILTERS
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

# On garde les matériaux avec NaN dans les colonnes numériques
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
# HEADER + METRICS
# =========================
header_col1, header_col2 = st.columns([3, 2])

with header_col1:
    st.markdown("### 🧱 Construction Materials Database")
    st.markdown(
        "<h1 style='margin-top:-8px; color:#f9fafb;'>Explore & Compare Materials</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color:#9ca3af; max-width:650px;'>Explore and compare construction materials based on their physical, thermal and environmental properties.</p>",
        unsafe_allow_html=True,
    )

with header_col2:
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.caption("Total Materials")
        st.subheader(len(df))
        st.markdown("</div>", unsafe_allow_html=True)
    with m2:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.caption("Filtered Results")
        st.subheader(len(filtered))
        st.markdown("</div>", unsafe_allow_html=True)
    with m3:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.caption("Material Types")
        if "type" in df.columns:
            st.subheader(df["type"].nunique())
        else:
            st.subheader("—")
        st.markdown("</div>", unsafe_allow_html=True)
    with m4:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.caption("Countries")
        if "pays_origine" in df.columns:
            st.subheader(df["pays_origine"].nunique())
        else:
            st.subheader("—")
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# Petit résumé stats sur les matériaux filtrés
if not filtered.empty:
    stats_col1, stats_col2, stats_col3 = st.columns(3)
    with stats_col1:
        st.caption("Average Density (filtered)")
        if "masse_volumique_kg_m3" in filtered.columns:
            st.write(f"{filtered['masse_volumique_kg_m3'].mean():.1f} kg/m³")
        else:
            st.write("—")
    with stats_col2:
        st.caption("Average λ (filtered)")
        if "conductivite_w_mk" in filtered.columns:
            st.write(f"{filtered['conductivite_w_mk'].mean():.3f} W/m·K")
        else:
            st.write("—")
    with stats_col3:
        st.caption("Average CO₂ footprint (filtered)")
        if "empreinte_carbone_kgco2e_kg" in filtered.columns:
            st.write(f"{filtered['empreinte_carbone_kgco2e_kg'].mean():.2f} kgCO₂e/kg")
        else:
            st.write("—")

# =========================
# TABS
# =========================
tab1, tab2, tab3, tab4 = st.tabs(
    ["📂 Materials Explorer", "📊 Compare Materials", "📈 Database Statistics", "✏️ Manage Materials"]
)

# =========================
# TAB 1: MATERIALS EXPLORER
# =========================
with tab1:
    st.markdown(f"### Showing {len(filtered)} material(s)")

    sort_option = st.selectbox(
        "Sort by",
        ["Name (A→Z)", "Density (low→high)", "Density (high→low)",
         "λ (low→high)", "λ (high→low)"],
        key="sort_explorer",
    )

    filtered_sorted = filtered.copy()
    if sort_option == "Name (A→Z)" and "nom" in filtered.columns:
        filtered_sorted = filtered.sort_values("nom", ascending=True)
    elif sort_option == "Density (low→high)" and "masse_volumique_kg_m3" in filtered.columns:
        filtered_sorted = filtered.sort_values("masse_volumique_kg_m3", ascending=True)
    elif sort_option == "Density (high→low)" and "masse_volumique_kg_m3" in filtered.columns:
        filtered_sorted = filtered.sort_values("masse_volumique_kg_m3", ascending=False)
    elif sort_option == "λ (low→high)" and "conductivite_w_mk" in filtered.columns:
        filtered_sorted = filtered.sort_values("conductivite_w_mk", ascending=True)
    elif sort_option == "λ (high→low)" and "conductivite_w_mk" in filtered.columns:
        filtered_sorted = filtered.sort_values("conductivite_w_mk", ascending=False)

    # bouton export CSV
    csv_bytes = filtered_sorted.to_csv(index=False, sep=";").encode("utf-8")
    st.download_button(
        "📥 Export filtered data to CSV",
        data=csv_bytes,
        file_name="materials_filtered.csv",
        mime="text/csv",
    )

    st.write("")
    for _, row in filtered_sorted.iterrows():
        st.markdown("<div class='material-card'>", unsafe_allow_html=True)

        # Image si image_url valide, sinon bandeau
        img_url = get_valid_image_url(row)
        if img_url:
            st.image(img_url)
        else:
            st.markdown("<div class='material-banner'></div>", unsafe_allow_html=True)

        st.markdown("<div class='material-content'>", unsafe_allow_html=True)

        st.markdown(
            f"<div class='material-title'>{row.get('nom', 'Material')}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div class='material-subtitle'>{row.get('type', '—')} → {row.get('sous_type', '—')}</div>",
            unsafe_allow_html=True,
        )

        desc = row.get("description")
        if isinstance(desc, str) and desc.strip():
            st.markdown(f"**Description:** {desc}")

        st.markdown("<div class='section-title'>PHYSICAL PROPERTIES</div>", unsafe_allow_html=True)
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("<div class='metric-label'>Density</div>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='metric-value'>{fmt(row.get('masse_volumique_kg_m3'), ' kg/m³')}</div>",
                unsafe_allow_html=True,
            )
        with col_p2:
            st.markdown("<div class='metric-label'>Thermal Conductivity λ</div>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='metric-value'>{fmt(row.get('conductivite_w_mk'), ' W/m·K')}</div>",
                unsafe_allow_html=True,
            )

        st.markdown("<div class='section-title'>THERMAL & MECHANICAL</div>", unsafe_allow_html=True)
        col_tm1, col_tm2 = st.columns(2)
        with col_tm1:
            st.markdown("<div class='metric-label'>Compressive Strength</div>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='metric-value'>{fmt(row.get('resistance_compression_mpa'), ' MPa')}</div>",
                unsafe_allow_html=True,
            )
        with col_tm2:
            st.markdown("<div class='metric-label'>Thermal Capacity</div>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='metric-value'>{fmt(row.get('capacite_thermique_j_kgk'), ' J/kg·K')}</div>",
                unsafe_allow_html=True,
            )

        st.markdown("<div class='section-title'>SUSTAINABILITY</div>", unsafe_allow_html=True)
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.markdown("<div class='metric-label'>Recycled Content</div>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='metric-value'>{fmt(row.get('contenu_recycle_pct'), ' %')}</div>",
                unsafe_allow_html=True,
            )
        with col_s2:
            st.markdown("<div class='metric-label'>CO₂ Footprint</div>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='metric-value'>{fmt(row.get('empreinte_carbone_kgco2e_kg'), ' kgCO₂e/kg')}</div>",
                unsafe_allow_html=True,
            )

        st.markdown("<div class='section-title'>SOURCE INFORMATION</div>", unsafe_allow_html=True)
        src_parts = []
        if isinstance(row.get("fabricant"), str) and row["fabricant"].strip():
            src_parts.append(f"Manufacturer: {row['fabricant']}")
        if isinstance(row.get("pays_origine"), str) and row["pays_origine"].strip():
            src_parts.append(f"Country: {row['pays_origine']}")
        if isinstance(row.get("origine"), str) and row["origine"].strip():
            src_parts.append(f"Origin: {row['origine']}")
        if src_parts:
            st.markdown(" | ".join(src_parts))

        st.markdown("</div></div>", unsafe_allow_html=True)

# =========================
# TAB 2: COMPARE MATERIALS (graphique)
# =========================
with tab2:
    st.markdown("### 📊 Compare Materials")

    if "nom" in df.columns:
        options = df["nom"].tolist()
    else:
        options = []

    selected_for_compare = st.multiselect(
        "Select materials to compare (up to 6)",
        options=options,
        max_selections=6,
    )

    if not selected_for_compare:
        st.info("Select at least one material in the dropdown above to compare.")
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
            "pays_origine",
        ]
        cols_to_show = [c for c in cols_to_show if c in comp_df.columns]

        st.dataframe(comp_df[cols_to_show].set_index("nom"), use_container_width=True)

        st.markdown("---")
        st.markdown("#### Graphical comparison")

        def metric_bar_chart(df_, col, title, y_label):
            if col not in df_.columns or df_[col].isna().all():
                st.write(f"No data for **{title}**")
                return
            chart = (
                alt.Chart(df_)
                .mark_bar()
                .encode(
                    x=alt.X("nom:N", sort="-y", title="Material"),
                    y=alt.Y(f"{col}:Q", title=y_label),
                    color=alt.Color("nom:N", legend=None),
                    tooltip=["nom", col],
                )
                .properties(height=250, title=title)
            )
            st.altair_chart(chart, use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            metric_bar_chart(comp_df, "masse_volumique_kg_m3",
                             "Density comparison", "Density (kg/m³)")
        with c2:
            metric_bar_chart(comp_df, "conductivite_w_mk",
                             "Thermal conductivity λ comparison", "λ (W/m·K)")

        c3, c4 = st.columns(2)
        with c3:
            metric_bar_chart(comp_df, "resistance_compression_mpa",
                             "Compressive strength comparison", "Strength (MPa)")
        with c4:
            metric_bar_chart(comp_df, "cout_eur_m2",
                             "Cost comparison", "Cost (€/m²)")

# =========================
# TAB 3: DATABASE STATISTICS (graphique + biosourcé)
# =========================
with tab3:
    st.markdown("### 🌱 Database statistics (with biosourced focus)")

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
        st.metric("Total materials", total)
    with mc2:
        st.metric("Biosourced materials", nb_bio)
    with mc3:
        st.metric("Share of biosourced", f"{share_bio:.1f} %")

    st.markdown("---")

    st.markdown("#### Average properties: biosourced vs other")

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

    c1, c2, c3 = st.columns(3)
    with c1:
        st.caption("Average density (kg/m³)")
        if dens_bio is not None and dens_other is not None:
            st.write(f"🌱 Biosourced : **{dens_bio:.0f}**")
            st.write(f"🏗️ Other     : **{dens_other:.0f}**")
        else:
            st.write("Not enough data")
    with c2:
        st.caption("Average λ (W/m·K)")
        if lambda_bio is not None and lambda_other is not None:
            st.write(f"🌱 Biosourced : **{lambda_bio:.3f}**")
            st.write(f"🏗️ Other     : **{lambda_other:.3f}**")
        else:
            st.write("Not enough data")
    with c3:
        st.caption("Average CO₂ footprint (kgCO₂e/kg)")
        if co2_bio is not None and co2_other is not None:
            st.write(f"🌱 Biosourced : **{co2_bio:.2f}**")
            st.write(f"🏗️ Other     : **{co2_other:.2f}**")
        else:
            st.write("Not enough data")

    st.markdown("---")
    st.markdown("#### Distribution & charts")

    col_a, col_b = st.columns(2)

    with col_a:
        st.caption("Number of materials per type")
        if "type" in df.columns:
            counts_type = df.groupby("type").size().reset_index(name="count")
            chart_type = (
                alt.Chart(counts_type)
                .mark_bar()
                .encode(
                    x=alt.X("type:N", title="Type"),
                    y=alt.Y("count:Q", title="Number of materials"),
                    color="type:N",
                    tooltip=["type", "count"],
                )
                .properties(height=300)
            )
            st.altair_chart(chart_type, use_container_width=True)
        else:
            st.write("No 'type' column in data.")

    with col_b:
        st.caption("λ vs density (colored by type)")
        if "masse_volumique_kg_m3" in df.columns and "conductivite_w_mk" in df.columns:
            scatter = (
                alt.Chart(df)
                .mark_circle(size=80)
                .encode(
                    x=alt.X("masse_volumique_kg_m3:Q", title="Density (kg/m³)"),
                    y=alt.Y("conductivite_w_mk:Q", title="λ (W/m·K)"),
                    color="type:N" if "type" in df.columns else alt.value("steelblue"),
                    tooltip=["nom", "type", "masse_volumique_kg_m3", "conductivite_w_mk"],
                )
                .properties(height=300)
            )
            st.altair_chart(scatter, use_container_width=True)
        else:
            st.write("Not enough data for λ vs density scatter plot.")

    st.markdown("#### Biosourced λ by type")
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
                y=alt.Y("lambda_mean:Q", title="Average λ (W/m·K)"),
                color="type:N",
                tooltip=["type", "lambda_mean"],
            )
            .properties(height=300)
        )
        st.altair_chart(chart_bio, use_container_width=True)
    else:
        st.write("No biosourced materials to plot λ by type.")

# =========================
# TAB 4: MANAGE MATERIALS
# =========================
with tab4:
    st.markdown("### Manage materials (coming later)")
    st.write("Here you could later add forms to add/edit materials directly from the app.")
