"""
Subak-Soil Streamlit Dashboard.

 Web interface for regional Super Seeder fleet scheduling, soil carbon conservation
diagnostics, and spatial cross-validation reporting across 22 Punjab districts.
"""

from __future__ import annotations

import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from subak_soil_scheduler import (
    ICAR_CONSTANTS,
    ICAR_THRESHOLDS,
    evaluate_ai_models_unbiased,
    load_subak_dataset,
    predict_single_cluster_ai,
    solve_subak_schedule,
)

st.set_page_config(
    page_title="Subak-Soil | Crop Residue & Soil Carbon Dispatch System",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #0f172a;
}
.top-header {
    background: #0f172a;
    color: #f8fafc;
    padding: 22px 26px;
    border-radius: 10px;
    margin-bottom: 18px;
    border-bottom: 3px solid #15803d;
}
.top-meta {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: #86efac;
    margin-bottom: 6px;
}
.top-title {
    font-size: 22px;
    font-weight: 700;
    margin: 0 0 6px 0;
    letter-spacing: -0.01em;
}
.top-desc {
    font-size: 13.5px;
    color: #cbd5e1;
    margin: 0;
    line-height: 1.5;
}
[data-testid="metric-container"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-top: 3px solid #0f172a;
    border-radius: 8px;
    padding: 12px 16px;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}
.callout-card {
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-left: 3px solid #0f172a;
    padding: 12px 16px;
    border-radius: 6px;
    margin-bottom: 12px;
    font-size: 13px;
}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Loading Punjab cluster dataset...")
def get_dataset() -> pd.DataFrame:
    return load_subak_dataset()


@st.cache_data(show_spinner="Running 5-fold spatial cross-validation...")
def get_validation_report() -> dict:
    return evaluate_ai_models_unbiased(get_dataset())


df = get_dataset()
val_report = get_validation_report()

st.markdown(
    """
<div class="top-header">
  <div class="top-meta">Regional Agronomy &amp; Operations Research Decision Support</div>
  <div class="top-title">SUBAK-SOIL — In-Situ Crop Residue &amp; Soil Carbon Dispatch System</div>
  <p class="top-desc">
    Multi-village Custom Hiring Centre (CHC) Super Seeder scheduling across 22 Punjab districts (1,500 clusters).
    Combines CP-SAT integer programming with Soil Health Card stoichiometry to prevent residue burning and preserve Soil Organic Carbon (SOC) and macronutrients.
  </p>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("#### Dispatch Parameters")
    districts = sorted(df["district"].unique())
    default_idx = districts.index("Sangrur") if "Sangrur" in districts else 0
    selected_district = st.selectbox(
        "Target District (Punjab)",
        districts,
        index=default_idx,
    )
    max_per_cluster = st.slider(
        "Max Super Seeders / Cluster / Day",
        min_value=5,
        max_value=25,
        value=15,
        step=1,
    )
    sharing_radius_km = st.slider(
        "Inter-CHC Cooperative Radius (km)",
        min_value=5.0,
        max_value=30.0,
        value=18.0,
        step=1.0,
    )
    soc_filter = st.selectbox(
        "Filter by SOC Status",
        ["ALL CLUSTERS", "CRITICAL (<0.50%)", "DEFICIENT (0.50-0.75%)", "MODERATE (>0.75%)"],
    )

    st.markdown("---")
    st.markdown("#### ICAR Reference Constants")
    st.caption(
        f"Residue Yield: {ICAR_CONSTANTS['straw_tons_per_ha']} t/ha\n\n"
        f"Organic Carbon: {ICAR_CONSTANTS['soc_tons_per_ton_straw']*1000:.0f} kg/t straw\n\n"
        f"Nitrogen (N): {ICAR_CONSTANTS['n_kg_per_ton_straw']} kg/t straw\n\n"
        f"Phosphorus (P2O5): {ICAR_CONSTANTS['p_kg_per_ton_straw']} kg/t straw\n\n"
        f"Potassium (K2O): {ICAR_CONSTANTS['k_kg_per_ton_straw']} kg/t straw\n\n"
        f"Unit Capacity: {ICAR_CONSTANTS['ha_per_machine_day']} ha/machine-day"
    )

schedule_df, summary = solve_subak_schedule(
    df,
    district=selected_district,
    max_machines_per_cluster_day=max_per_cluster,
    sharing_radius_km=sharing_radius_km,
)

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric(
    "Timely Mulched Area",
    f"{summary['subak_coverage_pct']}%",
    f"+{summary['coverage_lift_pct']}% vs uncoordinated ({summary['baseline_coverage_pct']}%)",
)
k2.metric(
    "Stabilized SOC Preserved",
    f"{summary['total_stabilized_carbon_tons']:,.1f} t",
    f"{summary['clusters_fully_served_subak']} / {summary['total_clusters']} clusters complete",
)
k3.metric(
    "Bioavailable NPK Saved",
    f"{summary['total_npk_saved_kg']:,} kg",
    "Adjusted for soil pH & texture",
)
k4.metric(
    "Gini Allocation Index",
    f"{summary['gini_equity_subak']:.3f}",
    f"Baseline {summary['gini_equity_baseline']:.3f} (lower is more equitable)",
    delta_color="inverse",
)
k5.metric(
    "Fertilizer Replacement Value",
    f"INR {summary['total_fertilizer_savings_inr']:,}",
    f"{summary['solver_status']} ({summary['solve_time_sec']}s)",
)


def render_leaflet_map(map_rows: pd.DataFrame, summary_info: dict) -> None:
    records = map_rows[
        [
            "cluster_id",
            "cluster_name",
            "block",
            "latitude",
            "longitude",
            "soc_percent",
            "soc_status",
            "soil_type",
            "soil_ph",
            "paddy_area_ha",
            "subak_ha_mulched",
            "baseline_ha_mulched",
            "harvest_days_left",
            "ai_urgency_score",
            "tier_code",
            "fully_served",
            "stabilized_carbon_tons",
            "npk_saved_kg",
        ]
    ].to_dict(orient="records")

    data_json = json.dumps(records)
    center_lat = summary_info["center_lat"]
    center_lon = summary_info["center_lon"]
    radius_m = int(summary_info["sharing_radius_km"] * 1000)

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8" />
      <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
      <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
      <style>
        body {{ margin: 0; padding: 0; font-family: 'Inter', sans-serif; }}
        #map {{ width: 100%; height: 490px; border-radius: 8px; border: 1px solid #cbd5e1; }}
        .legend {{
          background: rgba(15, 23, 42, 0.92);
          color: #f8fafc;
          padding: 10px 14px;
          border-radius: 6px;
          font-size: 11.5px;
          line-height: 1.6;
        }}
        .swatch {{ display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-right: 6px; }}
      </style>
    </head>
    <body>
      <div id="map"></div>
      <script>
        const clusters = {data_json};
        const centerLat = {center_lat};
        const centerLon = {center_lon};
        const radiusM = {radius_m};

        const streetLayer = L.tileLayer(
          'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{{z}}/{{y}}/{{x}}',
          {{ attribution: 'Tiles &copy; Esri' }}
        );
        const topoLayer = L.tileLayer(
          'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{{z}}/{{y}}/{{x}}',
          {{ attribution: 'Tiles &copy; Esri' }}
        );
        const satLayer = L.tileLayer(
          'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}',
          {{ attribution: 'Tiles &copy; Esri' }}
        );

        const map = L.map('map', {{
          center: [centerLat, centerLon],
          zoom: 10,
          layers: [streetLayer]
        }});

        L.control.layers({{
          "Street Map (Esri)": streetLayer,
          "Topographic Map": topoLayer,
          "Satellite Imagery": satLayer
        }}).addTo(map);

        L.circle([centerLat, centerLon], {{
          radius: radiusM,
          color: '#0f172a',
          weight: 1.5,
          dashArray: '5, 5',
          fillColor: '#0284c7',
          fillOpacity: 0.05
        }}).addTo(map).bindPopup("<b>CHC Cooperative Dispatch Zone</b><br/>Sharing radius: " + (radiusM/1000) + " km");

        clusters.forEach(c => {{
          let fillColor = '#15803d';
          if (!c.fully_served && c.tier_code === 'P1') fillColor = '#be123c';
          else if (!c.fully_served) fillColor = '#d97706';
          else if (c.tier_code === 'P1') fillColor = '#0f766e';

          const marker = L.circleMarker([c.latitude, c.longitude], {{
            radius: Math.max(5.5, Math.min(12.5, Math.sqrt(c.paddy_area_ha) * 0.65)),
            fillColor: fillColor,
            color: '#ffffff',
            weight: 1.5,
            fillOpacity: 0.9
          }}).addTo(map);

          marker.bindPopup(`
            <div style="font-size:12px; line-height:1.45; min-width:210px;">
              <b>${{c.cluster_name}}</b> (${{c.cluster_id}})<br/>
              Block: ${{c.block}} | Soil: ${{c.soil_type}} (pH ${{c.soil_ph}})<br/>
              SOC: ${{c.soc_percent}}% (${{c.soc_status}})<br/>
              Priority Index: ${{c.ai_urgency_score}} (${{c.tier_code}})<br/>
              Mulched: ${{c.subak_ha_mulched}} / ${{c.paddy_area_ha}} ha (Baseline: ${{c.baseline_ha_mulched}} ha)<br/>
              Stabilized SOC: ${{c.stabilized_carbon_tons}} t | NPK: ${{c.npk_saved_kg}} kg<br/>
              Remaining Window: ${{c.harvest_days_left}} days
            </div>
          `);
        }});

        const legend = L.control({{ position: 'bottomright' }});
        legend.onAdd = function() {{
          const div = L.DomUtil.create('div', 'legend');
          div.innerHTML = `
            <b>Cluster Dispatch Status</b><br/>
            <span class="swatch" style="background:#15803d;"></span>100% Mulched Within Window<br/>
            <span class="swatch" style="background:#0f766e;"></span>P1 Critical Cluster Completed<br/>
            <span class="swatch" style="background:#d97706;"></span>Partial Coverage (Deficit)<br/>
            <span class="swatch" style="background:#be123c;"></span>P1 Critical Unfulfilled
          `;
          return div;
        }};
        legend.addTo(map);
      </script>
    </body>
    </html>
    """
    components.html(html_code, height=505)


tab_map, tab_diag, tab_val, tab_soil, tab_doc = st.tabs([
    "Spatial Dispatch & GIS",
    "Soil Diagnostics & Prescription",
    "Model Validation (GroupKFold)",
    "District Soil Inventory & Export",
    "Documentation & Protocol",
])

with tab_map:
    st.markdown(f"#### Spatial Cluster Distribution & Fleet Schedule — {selected_district} District")
    filtered_df = schedule_df.copy()
    if soc_filter != "ALL CLUSTERS":
        filtered_df = filtered_df[filtered_df["soc_status"] == soc_filter]

    render_leaflet_map(filtered_df, summary)

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.progress(
            min(100, int(round(summary["baseline_coverage_pct"]))),
            text=f"Uncoordinated Baseline CHC (Local Fleet Only): {summary['baseline_coverage_pct']}% ({summary['baseline_mulched_ha']:,.1f} ha)",
        )
    with col_p2:
        st.progress(
            min(100, int(round(summary["subak_coverage_pct"]))),
            text=f"Synchronized Subak Dispatch ({sharing_radius_km:.0f} km Sharing Radius): {summary['subak_coverage_pct']}% ({summary['subak_mulched_ha']:,.1f} ha)",
        )

    st.markdown("#### Cluster Allocation Schedule (15-Day Transition Window)")
    core_cols = [
        "cluster_id",
        "cluster_name",
        "block",
        "soil_type",
        "soc_percent",
        "soil_ph",
        "paddy_area_ha",
        "harvest_days_left",
        "ai_urgency_score",
        "tier_code",
        "baseline_ha_mulched",
        "subak_ha_mulched",
        "coverage_pct",
        "fully_served",
        "stabilized_carbon_tons",
        "npk_saved_kg",
    ]
    st.dataframe(schedule_df[core_cols], use_container_width=True, height=360, hide_index=True)

    with st.expander("View Full Daily Allocation Matrix (Day 1 to Day 15)"):
        st.dataframe(schedule_df, use_container_width=True, hide_index=True)

with tab_diag:
    st.markdown("#### Field-Level Soil Urgency & Agronomic Prescription Calculator")
    c_in1, c_in2, c_in3 = st.columns(3)
    with c_in1:
        in_soc = st.slider("Soil Organic Carbon / SOC (%)", 0.25, 1.30, 0.44, 0.01)
        in_ph = st.slider("Soil pH", 5.5, 9.0, 7.85, 0.05)
        in_soil_type = st.selectbox("Soil Texture Class", ["Sandy Loam", "Alluvial", "Loamy", "Clay Loam"])
    with c_in2:
        in_n = st.number_input("Available Nitrogen (kg/ha)", 40.0, 220.0, 82.0, 2.0)
        in_p = st.number_input("Available Phosphorus P2O5 (kg/ha)", 15.0, 110.0, 38.0, 2.0)
        in_k = st.number_input("Available Potassium K2O (kg/ha)", 80.0, 320.0, 145.0, 5.0)
    with c_in3:
        in_area = st.number_input("Cluster Paddy Area (ha)", 20.0, 500.0, 165.0, 5.0)
        in_days = st.slider("Remaining Days Before Wheat Sowing", 1, 15, 4, 1)
        in_chc = st.slider("Local CHC Super Seeders Available", 0, 10, 1, 1)

    pred = predict_single_cluster_ai(
        soc_percent=in_soc,
        nitrogen_kg_ha=in_n,
        phosphorus_kg_ha=in_p,
        potassium_kg_ha=in_k,
        soil_ph=in_ph,
        soil_type=in_soil_type,
        paddy_area_ha=in_area,
        harvest_days_left=in_days,
        chc_machines=in_chc,
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Composite Urgency Score", f"{pred['ai_urgency_score']} / 100", pred["priority_tier"])
    m2.metric("Biophysical Vulnerability", f"{pred['soil_vulnerability_score']} / 100", in_soil_type)
    m3.metric("Required Fleet Rate", f"{pred['required_machines_daily']} units/day", f"Local deficit: {pred['machine_deficit_daily']} units")
    m4.metric("Stabilized Carbon & NPK", f"{pred['agronomic_impact']['stabilized_carbon_tons']} t C", f"{pred['agronomic_impact']['npk_saved_kg']:,.0f} kg NPK")

    st.markdown("#### Field Management Prescriptions")
    for rec in pred["recommendations"]:
        st.markdown(f"<div class='callout-card'>{rec}</div>", unsafe_allow_html=True)

with tab_val:
    st.markdown("#### Spatial Cross-Validation Report (5-Fold Disjoint Across 22 Districts)")
    nb = val_report["naive_biased"]
    su = val_report["spatial_unbiased"]

    st.markdown(
        f"<div class='callout-card'><b>Baseline Split Observation:</b> {nb['notes']}<br/>"
        f"<b>Spatial GroupKFold Protocol:</b> {su['notes']}</div>",
        unsafe_allow_html=True,
    )

    v1, v2 = st.columns(2)
    with v1:
        st.markdown("##### Out-of-Fold Validation Metrics")
        comp_df = pd.DataFrame([
            {"Metric": "Partition Strategy", "Random 5-Fold (With Proxy)": "Random K-Fold", "Spatial Block GroupKFold": "22-District Disjoint Blocks"},
            {"Metric": "Out-of-Fold R2", "Random 5-Fold (With Proxy)": f"{nb['r2']:.4f}", "Spatial Block GroupKFold": f"{su['r2']:.4f}"},
            {"Metric": "RMSE", "Random 5-Fold (With Proxy)": f"{nb['rmse']:.3f}", "Spatial Block GroupKFold": f"{su['rmse']:.3f}"},
            {"Metric": "MAE", "Random 5-Fold (With Proxy)": f"{nb['mae']:.3f}", "Spatial Block GroupKFold": f"{su['mae']:.3f}"},
            {"Metric": "Macro-F1 (3-Tier Classification)", "Random 5-Fold (With Proxy)": "-", "Spatial Block GroupKFold": f"{su['macro_f1']:.4f}"},
            {"Metric": "Balanced Accuracy", "Random 5-Fold (With Proxy)": "-", "Spatial Block GroupKFold": f"{su['balanced_accuracy']:.4f}"},
        ])
        st.dataframe(comp_df, use_container_width=True, hide_index=True)

        st.markdown("##### Out-of-Fold Confusion Matrix (N = 1,500)")
        cm_df = pd.DataFrame(
            su["confusion_matrix"],
            index=[f"Actual: {lbl}" for lbl in su["class_labels"]],
            columns=[f"Predicted: {lbl}" for lbl in su["class_labels"]],
        )
        st.dataframe(cm_df, use_container_width=True)

    with v2:
        st.markdown("##### Permutation Feature Importance")
        imp_df = pd.DataFrame(su["feature_importances"])
        st.dataframe(
            imp_df.rename(columns={"feature": "Predictor Variable", "importance_pct": "Variance Contribution (%)"}),
            use_container_width=True,
            hide_index=True,
        )
        st.bar_chart(imp_df.set_index("feature")["importance_pct"])

with tab_soil:
    st.markdown(f"#### District Soil Parameter Summary — {selected_district}")
    dist_raw = df[df["district"] == selected_district].copy()

    diag_rows = []
    for col_key, meta in ICAR_THRESHOLDS.items():
        mean_val = float(dist_raw[col_key].mean())
        min_val = float(dist_raw[col_key].min())
        max_val = float(dist_raw[col_key].max())
        thresh = float(meta["threshold"])
        if col_key == "soil_ph":
            status_str = "Optimal (Neutral)" if 6.5 <= mean_val <= 7.5 else "Slightly Alkaline (P Fixation Risk)"
        else:
            status_str = "Above Threshold" if mean_val >= thresh else "Below Threshold (Deficit)"
        diag_rows.append({
            "Parameter": meta["label"],
            "District Mean": round(mean_val, 2),
            "Min": round(min_val, 2),
            "Max": round(max_val, 2),
            "ICAR Threshold": thresh,
            "Unit": meta["unit"],
            "Status": status_str,
        })
    st.dataframe(pd.DataFrame(diag_rows), use_container_width=True, hide_index=True)

    dl1, dl2 = st.columns(2)
    with dl1:
        st.download_button(
            label=f"Export Dispatch Schedule — {selected_district} (CSV)",
            data=schedule_df.to_csv(index=False).encode("utf-8"),
            file_name=f"subak_schedule_{selected_district.lower().replace(' ', '_')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with dl2:
        st.download_button(
            label=f"Export Soil Dataset — {selected_district} (CSV)",
            data=dist_raw.to_csv(index=False).encode("utf-8"),
            file_name=f"subak_soil_{selected_district.lower().replace(' ', '_')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

with tab_doc:
    st.markdown("#### System Architecture & Operational Protocol")
    st.markdown(
        """
1. **Spatial Dispatch & GIS:** Select a target district in the sidebar, configure the daily per-cluster machine cap, and set the inter-CHC cooperative sharing radius. The map displays cluster completion status and the cooperative dispatch perimeter.
2. **Soil Diagnostics & Prescription:** Input field-level Soil Health Card measurements (SOC, pH, texture, N, P2O5, K2O) to compute the urgency index, phosphorus bioavailability factor, and residue incorporation recommendations.
3. **Model Validation:** Inspect the 5-fold district-grouped cross-validation metrics, 3x3 confusion matrix, and permutation feature importance rankings.
4. **Unified Codebase:** Both the Streamlit application (`app.py`) and the Vercel serverless API (`api/index.py`) import all scheduling and stoichiometric routines from `subak_soil_scheduler.py`.
        """
    )
