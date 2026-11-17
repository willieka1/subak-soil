import os
import pandas as pd
import pydeck as pdk
import streamlit as st
from subak_soil_scheduler import solve_subak_schedule

st.set_page_config(page_title="SUBAK-SOIL | Soil Nutrient Synchronizer", layout="wide")
st.title("SUBAK-SOIL: In-Situ Soil Carbon & Mulching Synchronizer")
st.caption("Sinkronisasi giliran mesin Super Seeder berbasis algoritma Subak Bali & Google OR-Tools untuk penyelamatan Karbon Organik Tanah (SOC) dan NPK di India.")

@st.cache_data
def load_dataset():
    paths = [
        "subak_soil_datasheet.csv",
        os.path.join(os.path.dirname(__file__), "subak_soil_datasheet.csv"),
        "subak-soil-app/subak_soil_datasheet.csv",
        "../subak_soil_datasheet.csv"
    ]
    for p in paths:
        if os.path.exists(p):
            return pd.read_csv(p)
    return pd.read_csv("subak_soil_datasheet.csv")

df = load_dataset()

# Sidebar Kontrol Simulasi
st.sidebar.header("Parameter Penjadwalan Subak")
districts = sorted(df["district"].unique())
default_index = districts.index("Sangrur") if "Sangrur" in districts else 0
selected_district = st.sidebar.selectbox("Pilih Distrik Target:", districts, index=default_index)
max_per_cluster = st.sidebar.slider("Maksimum Mesin per Desa/Hari:", min_value=5, max_value=25, value=15)

# Jalankan Solver OR-Tools secara Real-Time
schedule_df, summary = solve_subak_schedule(
    df,
    district=selected_district,
    max_machines_per_cluster_day=max_per_cluster,
)

# Baris 1: 4 Kartu Metrik Utama (Fokus Tanah)
col1, col2, col3, col4 = st.columns(4)
col1.metric(
    "Lahan Termulsa Tepat Waktu",
    f"{summary['subak_coverage_pct']}%",
    f"+{round(summary['subak_coverage_pct'] - summary['baseline_coverage_pct'], 1)}% vs Baseline CHC",
)
col2.metric(
    "Karbon Organik Tanah (SOC) Diselamatkan",
    f"{summary['total_carbon_saved_tons']:,.1f} Ton",
    f"{summary['clusters_fully_served_subak']} dari {summary['total_clusters']} Desa Tuntas",
)
col3.metric(
    "Total Hara NPK Kembali ke Tanah",
    f"{summary['total_npk_saved_kg']:,.0f} kg",
    "N + P2O5 + K2O In-Situ",
)
col4.metric(
    "Penghematan Pupuk Kimia Petani",
    f"INR {summary['total_fertilizer_savings_inr']:,}",
    f"Solver: {summary['solver_status']} ({summary['solve_time_sec']} dtk)",
)

# Gabungkan koordinat untuk peta PyDeck
coords = df[df["district"] == selected_district][["cluster_id", "latitude", "longitude"]]
map_df = schedule_df.merge(coords, on="cluster_id", how="left")
map_df["color_r"] = map_df["fully_served"].apply(lambda v: 22 if v else 180)
map_df["color_g"] = map_df["fully_served"].apply(lambda v: 101 if v else 52)
map_df["color_b"] = map_df["fully_served"].apply(lambda v: 52 if v else 18)

st.subheader(f"Peta Sinkronisasi Tanah & Mesin Mulsa — Distrik {selected_district}")
layer = pdk.Layer(
    "ScatterplotLayer",
    data=map_df,
    get_position="[longitude, latitude]",
    get_fill_color="[color_r, color_g, color_b, 200]",
    get_radius=1200,
    pickable=True,
)
view_state = pdk.ViewState(
    latitude=float(map_df["latitude"].mean()),
    longitude=float(map_df["longitude"].mean()),
    zoom=9.2,
)
st.pydeck_chart(pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip={"text": "{cluster_name}\nSOC: {soc_percent}% ({soc_status})\nLahan Termulsa: {subak_ha_mulched} / {paddy_area_ha} ha\nKarbon Diselamatkan: {carbon_saved_tons} ton"},
))

st.subheader("Jadwal Harian Mesin Super Seeder (Hari 1 s.d. Hari 15) & Kalkulator Hara")
st.dataframe(schedule_df, use_container_width=True)
csv_bytes = schedule_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label=f"Unduh Jadwal Subak Distrik {selected_district} (CSV)",
    data=csv_bytes,
    file_name=f"subak_schedule_{selected_district.lower()}.csv",
    mime="text/csv",
)
