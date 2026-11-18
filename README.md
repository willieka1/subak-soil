# Subak-Soil: Regional Crop Residue & Soil Carbon Dispatch System

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://subak-soil.streamlit.app/)

**Subak-Soil** is a geospatial decision-support and operations-research system designed to coordinate Custom Hiring Centre (CHC) *Super Seeder* fleets across 22 districts in Punjab, India (1,500 village clusters). By adapting the cooperative rotational scheduling principles of Bali's *Subak* irrigation networks into a constraint-programming solver (**Google OR-Tools CP-SAT**), the platform maximizes timely *in-situ* paddy straw mulching within the critical 15-day *Kharif*-to-*Rabi* transition window—preserving Soil Organic Carbon (SOC) and soil macronutrients (N, $\text{P}_2\text{O}_5$, $\text{K}_2\text{O}$).

## Problem Context & Agronomic Basis

During the November harvest transition in the Indo-Gangetic Plains, farmers face a strict 10–15 day window between paddy harvest and wheat sowing. Delays in wheat sowing beyond mid-November incur yield penalties of **200–500 kg/ha per week** ([MDPI Agronomy, 2026](https://www.mdpi.com/2073-445x/15/8/1453)). Although over 43,500 Custom Hiring Centres operate CRM machinery ([Earth5R, 2025](https://earth5r.org/stubble-burning-india/)), uncoordinated local dispatching leaves machines idle in low-urgency blocks while neighbouring villages resort to open-field burning.

According to **ICAR-IARI** and **Soil Health Card (SHC)** assessments ([ICRIER Policy Brief #63](https://icrier.org/pdf/pb63_Improving-Soil-Health-Better-Crop-Health-and-Human-Nutrition.pdf); [PMC6427124](https://pmc.ncbi.nlm.nih.gov/articles/PMC6427124/)), burning 1 metric ton of paddy residue results in the direct loss of:
- **400 kg** of Soil Organic Carbon (SOC)
- **5.5 kg** of Nitrogen (N), **2.3 kg** of Phosphorus ($\text{P}_2\text{O}_5$), **25.0 kg** of Potassium ($\text{K}_2\text{O}$), and **1.2 kg** of Sulphur (S)
- Acute topsoil heating (**33.8–42.2 °C** at 10 mm depth), reducing microbial biomass in the rhizosphere.

## Repository Structure

The repository uses a unified core module (`subak_soil_scheduler.py`) shared by both the **Streamlit** application and the **Vercel** serverless backend + web client, eliminating duplicate code and redundant files:

```text
subak-soil/
├── subak_soil_scheduler.py     # Core engine: CSV loader, ICAR stoichiometry, GroupKFold validation, CP-SAT solver
├── app.py                      # Streamlit web application (imports subak_soil_scheduler.py)
├── api/
│   └── index.py                # FastAPI serverless entrypoint for Vercel (imports subak_soil_scheduler.py)
├── public/
│   └── index.html              # Standalone web dashboard with Leaflet ArcGIS StreetMap & Chart.js
├── vercel.json                 # Vercel routing configuration (/api/* -> api/index.py, /* -> public/index.html)
├── subak_soil_datasheet.csv    # Calibrated dataset covering 1,500 village clusters across 22 Punjab districts
├── requirements.txt            # Python dependencies
├── push_to_github.sh           # Automated Git commit & push script (macOS / Linux / Git Bash)
├── push_to_github.bat          # Automated Git commit & push script (Windows CMD / PowerShell)
└── README.md                   # Project documentation
```

## Methodology & Model Validation

1. **Spatial Cross-Validation (`GroupKFold` across 22 Districts):**
   - To prevent spatial autocorrelation and target formula leakage from district-level fire proxy variables (`fire_risk_index`), model validation partitions the 1,500 clusters into 5 spatially disjoint district folds using 9 biophysical and operational features (`SOC`, `N`, `P2O5`, `K2O`, `soil_ph`, `soil_type`, `paddy_area_ha`, `harvest_days_left`, `chc_super_seeders_available`).
   - Out-of-fold validation achieves **$R^2 = 0.9549$**, **RMSE $= 2.213$**, **MAE $= 1.755$**, **Macro-F1 $= 0.9053$**, and **Balanced Accuracy $= 0.9046$**.
2. **pH- and Texture-Adjusted Nutrient Recovery:**
   - Adjusts phosphorus ($\text{P}_2\text{O}_5$) bioavailability for calcium-phosphate fixation in alkaline soils ($\text{pH} > 7.5$) and scales humified carbon stabilization across soil texture classes (*Clay Loam*, *Loamy*, *Alluvial*, *Sandy Loam*).
3. **CP-SAT Cooperative Fleet Scheduling & Spatial Equity:**
   - Formulates daily machine allocation as a constrained integer program solved via `ortools.sat.python.cp_model`, comparing synchronized cooperative pooling against uncoordinated local CHC baselines and reporting the **Gini Coefficient** of spatial coverage.

## Local Development & Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Run CLI scheduler and spatial cross-validation report for Sangrur district
python subak_soil_scheduler.py --district Sangrur --validate --output subak_schedule_output.csv

# Launch Streamlit application locally
streamlit run app.py
```

## Deployment (Streamlit & Vercel)

### Updating `github.com/willieka1/subak-soil`
Extract the release archive into your local project folder and run:
- **Windows:** `push_to_github.bat`
- **macOS / Linux / Git Bash:** `bash push_to_github.sh`

Once pushed to `https://github.com/willieka1/subak-soil`:
1. **Streamlit Community Cloud:** Connected automatically via `app.py` at [subak-soil.streamlit.app](https://subak-soil.streamlit.app/).
2. **Vercel:** Import `willieka1/subak-soil` at [vercel.com/new](https://vercel.com/new). Vercel automatically reads `vercel.json`, builds `api/index.py` as a Python Serverless Function, and serves `public/index.html`.
