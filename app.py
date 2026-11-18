"""
SUBAK-SOIL — In-Situ Soil Carbon & Mulching Synchronizer
Web Dashboard  |  13th Protocol: An AI Hackathon 2026

Stack: Streamlit · PyDeck · Pandas
Solver: subak_soil_scheduler.py  (Greedy Priority Heuristic)
Data:   subak_soil_datasheet.csv (1 500 village clusters, 22 Punjab districts)
"""

import os
import pandas as pd
import pydeck as pdk
import streamlit as st

from subak_soil_scheduler import solve_subak_schedule

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SUBAK-SOIL | Soil Carbon Synchronizer",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Minimal custom CSS (no external fonts needed) ─────────────────────────────
st.markdown("""
<style>
/* Metric card background */
[data-testid="metric-container"] {
    background: #f0faf3;
    border: 1px solid #c3e6cb;
    border-radius: 10px;
    padding: 14px 18px;
}
/* Green header accent */
h1 { color: #1a6b3c; }
h2, h3 { color: #2d5a3d; }
/* Sidebar accent */
[data-testid="stSidebar"] { background: #f7fcf8; }
/* Badge pills */
.badge-critical { background:#dc3545; color:white; padding:2px 8px; border-radius:12px; font-size:12px; }
.badge-deficient { background:#fd7e14; color:white; padding:2px 8px; border-radius:12px; font-size:12px; }
.badge-moderate { background:#198754; color:white; padding:2px 8px; border-radius:12px; font-size:12px; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
# 🌾 SUBAK-SOIL
### In-Situ Soil Carbon & Mulching Synchronizer
""")
st.markdown(
    "Platform penjadwalan **Super Seeder CHC** berbasis algoritma Subak Bali "
    "untuk menyelamatkan **Karbon Organik Tanah (SOC)** dan **hara NPK** dari "
    "pembakaran jerami padi di Punjab, India — dalam jendela kritis 15 hari."
)
st.divider()

# ── Load data (cached) ────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Memuat dataset 1 500 klaster desa Punjab…")
def load_dataset() -> pd.DataFrame:
    for path in [
        "subak_soil_datasheet.csv",
        os.path.join(os.path.dirname(__file__), "subak_soil_datasheet.csv"),
    ]:
        if os.path.exists(path):
            return pd.read_csv(path)
    raise FileNotFoundError("subak_soil_datasheet.csv tidak ditemukan.")

df = load_dataset()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/Flag_of_India.svg/320px-Flag_of_India.svg.png",
        width=90,
    )
    st.markdown("## ⚙️ Parameter Simulasi")
    st.markdown("---")

    districts = sorted(df["district"].unique())
    default_idx = districts.index("Sangrur") if "Sangrur" in districts else 0
    selected_district = st.selectbox(
        "🏘️ Distrik Target",
        districts,
        index=default_idx,
        help="Pilih salah satu dari 22 distrik Punjab.",
    )

    max_per_cluster = st.slider(
        "🚜 Maks. Super Seeder per Desa/Hari",
        min_value=5, max_value=25, value=15, step=1,
        help="Batas atas armada mesin yang dikirim ke satu klaster desa per hari.",
    )

    st.markdown("---")
    st.markdown("### 📖 Cara Penggunaan")
    st.markdown("""
1. **Pilih Distrik** — tentukan wilayah prioritas Punjab.
2. **Atur kapasitas mesin** — sesuaikan armada CHC yang tersedia.
3. **Lihat peta** — 🟢 desa tuntas, 🔴 perlu tambahan mesin.
4. **Baca kartu metrik** — SOC diselamatkan, NPK, & penghematan pupuk.
5. **Unduh jadwal** — ekspor CSV harian untuk operasional lapangan.
    """)

    st.markdown("---")
    st.markdown("### 🧮 Formula ICAR")
    st.markdown("""
| Parameter | Nilai per Ton Jerami |
|-----------|---------------------|
| Straw yield | 5.5 ton/ha paddy |
| SOC saved | 400 kg (0.4 ton) |
| N saved | 5.5 kg |
| P saved | 2.3 kg |
| K saved | 25.0 kg |
""")
    st.caption("Sumber: ICAR-CSSRI, PAU Ludhiana")

# ── Run solver ────────────────────────────────────────────────────────────────
with st.spinner(f"🧠 Menghitung jadwal optimal untuk Distrik **{selected_district}**…"):
    schedule_df, summary = solve_subak_schedule(
        df,
        district=selected_district,
        max_machines_per_cluster_day=max_per_cluster,
    )

# ── Section 1: KPI Cards ──────────────────────────────────────────────────────
st.markdown("## 📊 Dampak Intervensi Subak")
delta_pct = round(summary["subak_coverage_pct"] - summary["baseline_coverage_pct"], 1)

c1, c2, c3, c4 = st.columns(4)
c1.metric(
    "🌱 Lahan Termulsa Tepat Waktu",
    f"{summary['subak_coverage_pct']}%",
    f"+{delta_pct}% vs Baseline CHC",
    help="Persentase lahan paddy yang berhasil dimulsa sebelum deadline pembakaran."
)
c2.metric(
    "🪨 Karbon Organik Tanah (SOC)",
    f"{summary['total_carbon_saved_tons']:,.0f} Ton",
    f"{summary['clusters_fully_served_subak']} / {summary['total_clusters']} desa tuntas",
    help="Total SOC yang diselamatkan dari pembakaran (formula ICAR: 400 kg SOC per ton jerami)."
)
c3.metric(
    "🌿 NPK Kembali ke Tanah",
    f"{summary['total_npk_saved_kg']:,.0f} kg",
    "N + P₂O₅ + K₂O in-situ",
    help="Total hara N, P, K yang kembali ke tanah secara alami."
)
c4.metric(
    "💰 Hemat Pupuk Kimia",
    f"INR {summary['total_fertilizer_savings_inr']:,}",
    f"⏱ {summary['solve_time_sec']} dtk",
    help="Nilai ekonomi penggantian pupuk kimia (Urea, DAP, MOP)."
)

# Baseline comparison bar
st.markdown("#### Perbandingan Cakupan: Subak vs Baseline CHC")
bar_col1, bar_col2 = st.columns(2)
with bar_col1:
    baseline = summary["baseline_coverage_pct"]
    st.progress(int(baseline), text=f"Baseline CHC (tanpa sinkronisasi): **{baseline}%**")
with bar_col2:
    subak = summary["subak_coverage_pct"]
    st.progress(min(int(subak), 100), text=f"SUBAK-SOIL (tersinkronisasi): **{subak}%**")

st.divider()

# ── Section 2: Map ────────────────────────────────────────────────────────────
st.markdown(f"## 🗺️ Peta Distribusi Klaster Desa — {selected_district}")
st.caption("🟢 Desa Tuntas (mulsa 100%)    🔴 Desa Perlu Tambahan Mesin")

coords_df = df[df["district"] == selected_district][["cluster_id", "latitude", "longitude"]]
map_df = schedule_df.merge(coords_df, on="cluster_id", how="left")

# Color: green = fully served, red = not
map_df["color_r"] = map_df["fully_served"].apply(lambda v: 34  if v else 220)
map_df["color_g"] = map_df["fully_served"].apply(lambda v: 170 if v else 50)
map_df["color_b"] = map_df["fully_served"].apply(lambda v: 85  if v else 20)
map_df["radius"]  = map_df["paddy_area_ha"].apply(lambda h: max(600, min(h * 5, 2000)))

layer = pdk.Layer(
    "ScatterplotLayer",
    data=map_df,
    get_position="[longitude, latitude]",
    get_fill_color="[color_r, color_g, color_b, 210]",
    get_radius="radius",
    pickable=True,
    auto_highlight=True,
)
view = pdk.ViewState(
    latitude=float(map_df["latitude"].mean()),
    longitude=float(map_df["longitude"].mean()),
    zoom=9.2,
    pitch=0,
)
st.pydeck_chart(pdk.Deck(
    layers=[layer],
    initial_view_state=view,
    map_style="mapbox://styles/mapbox/light-v10",
    tooltip={
        "html": """
        <b>{cluster_name}</b><br/>
        🧪 SOC: {soc_percent}% — {soc_status}<br/>
        🌾 Lahan: {subak_ha_mulched} / {paddy_area_ha} ha termulsa<br/>
        🪨 Karbon diselamatkan: {carbon_saved_tons} ton<br/>
        🌿 NPK: {npk_saved_kg} kg<br/>
        ⏰ Deadline: {harvest_days_left} hari
        """,
        "style": {
            "backgroundColor": "#1a6b3c",
            "color": "white",
            "fontSize": "13px",
            "borderRadius": "8px",
            "padding": "10px",
        },
    },
))

st.divider()

# ── Section 3: Soil Deficiency Breakdown ──────────────────────────────────────
st.markdown("## 🧪 Analisis Defisiensi Tanah")

dist_data = df[df["district"] == selected_district].copy()
soc_counts = dist_data["soc_status"].value_counts()

col_a, col_b = st.columns([1, 2])
with col_a:
    st.markdown("**Status SOC per Distrik**")
    for status, count in soc_counts.items():
        pct = round(count / len(dist_data) * 100, 1)
        if "CRITICAL" in status:
            color = "🔴"
        elif "DEFICIENT" in status:
            color = "🟠"
        else:
            color = "🟢"
        st.markdown(f"{color} **{status}**: {count} desa ({pct}%)")

with col_b:
    st.markdown("**Rata-Rata Parameter Tanah**")
    avg_cols = ["soil_organic_carbon_percent", "nitrogen_kg_ha", "phosphorus_kg_ha", "potassium_kg_ha", "soil_ph"]
    rename_map = {
        "soil_organic_carbon_percent": "SOC (%)",
        "nitrogen_kg_ha": "N (kg/ha)",
        "phosphorus_kg_ha": "P (kg/ha)",
        "potassium_kg_ha": "K (kg/ha)",
        "soil_ph": "pH"
    }
    avg_df = dist_data[avg_cols].mean().round(2).rename(rename_map).reset_index()
    avg_df.columns = ["Parameter", "Rata-rata Distrik"]
    # Add ICAR threshold
    thresholds = {"SOC (%)": 0.75, "N (kg/ha)": 100, "P (kg/ha)": 50, "K (kg/ha)": 150, "pH": 7.0}
    avg_df["Ambang Batas ICAR"] = avg_df["Parameter"].map(thresholds)
    avg_df["Status"] = avg_df.apply(
        lambda r: "✅ OK" if r["Parameter"] in ["pH"] or r["Rata-rata Distrik"] >= r["Ambang Batas ICAR"] else "⚠️ Defisit",
        axis=1
    )
    st.dataframe(avg_df, use_container_width=True, hide_index=True)

st.divider()

# ── Section 4: Schedule Table ─────────────────────────────────────────────────
st.markdown("## 📅 Jadwal Harian Mesin Super Seeder")
st.caption("Jadwal alokasi armada CHC per klaster desa selama 15 hari jendela kritis.")

display_cols = [c for c in schedule_df.columns if not c.startswith("day_")]
st.dataframe(
    schedule_df[display_cols].style.map(
        lambda v: "background-color: #d4edda; color: #155724;" if v is True else
                  ("background-color: #f8d7da; color: #721c24;" if v is False else ""),
        subset=["fully_served"]
    ),
    use_container_width=True,
    height=380,
)

with st.expander("📋 Lihat Jadwal Harian Lengkap per Desa (Hari 1–15)"):
    st.dataframe(schedule_df, use_container_width=True)

st.markdown("---")

# ── Section 5: Download ───────────────────────────────────────────────────────
st.markdown("## ⬇️ Ekspor Data")
dl1, dl2 = st.columns(2)

with dl1:
    csv_schedule = schedule_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=f"📥 Unduh Jadwal {selected_district} (CSV)",
        data=csv_schedule,
        file_name=f"subak_schedule_{selected_district.lower().replace(' ', '_')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

with dl2:
    dist_raw = df[df["district"] == selected_district]
    csv_soil = dist_raw.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=f"🧪 Unduh Data Tanah {selected_district} (CSV)",
        data=csv_soil,
        file_name=f"subak_soil_{selected_district.lower().replace(' ', '_')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style='text-align:center; color:#6c757d; font-size:13px; padding-top:8px;'>
🌾 <b>SUBAK-SOIL</b> &nbsp;|&nbsp; 13th Protocol: An AI Hackathon 2026 &nbsp;|&nbsp;
Algoritma Subak Bali × Soil Health Card India × Formula ICAR-PAU<br/>
Dataset: 1 500 klaster desa, 22 Distrik Punjab · Solver: Greedy Priority Heuristic (sub-detik)
</div>
""", unsafe_allow_html=True)
