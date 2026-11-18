# 🌾 SUBAK-SOIL — In-Situ Soil Carbon & Mulching Synchronizer

> **13th Protocol: An AI Hackathon 2026** | HackIndia · Greater Noida

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://subak-soil.streamlit.app)

---

## 🧩 Latar Belakang & Urgensi Masalah

Setiap musim panen padi di Punjab, India, lebih dari **20 juta ton jerami** dibakar di lahan terbuka karena petani hanya memiliki jendela waktu sempit (~15 hari) sebelum harus menabur gandum. Pembakaran masif ini menyebabkan:
- **Degradasi Kritis Karbon Organik Tanah (SOC):** Lebih dari 50% tanah pertanian Punjab memiliki SOC < 0.75% (kategori DEFICIENT & CRITICAL).
- **Kerugian Hara Tanah Masif:** Triliunan rupiah hara makro (N, P, K) terbuang ke atmosfer menjadi asap polusi.
- **Krisis Polusi Udara Ekstrem:** Lonjakan partikel PM2.5 di Punjab dan New Delhi hingga 10–20× ambang batas aman WHO.

**SUBAK-SOIL** mengadaptasi kearifan lokal sistem irigasi gotong-royong **Subak Bali (UNESCO)** menjadi algoritma optimasi alokasi mesin **Super Seeder CHC (Custom Hiring Centre)**, memprioritaskan pemulsaan jerami ke dalam tanah (*in-situ*) sebelum pembakaran terjadi.

---

## 🏗️ Struktur Proyek

```
subak-soil/
├── app.py                      # Dashboard Web Interaktif (Streamlit + PyDeck + KPI Cards)
├── subak_soil_scheduler.py     # Mesin Penjadwalan Cerdas (Subak Priority Dispatch Engine)
├── subak_soil_datasheet.csv    # Dataset 1.500 Klaster Desa Terverifikasi (22 Distrik Punjab)
├── requirements.txt            # Dependensi Cloud & Lokal (Streamlit, Pandas, PyDeck, OR-Tools)
└── README.md                   # Dokumentasi Lengkap & Panduan Penggunaan
```

> **Catatan Struktur:** Seluruh kode bersih tanpa file ganda/redundansi — satu file `app.py` terpusat dan satu engine `subak_soil_scheduler.py`.

---

## ⚙️ Logika Algoritma Penjadwalan Subak

### 1. Subak Urgency & Priority Scoring
Setiap klaster desa dihitung nilai urgensinya (skala 0–100) berdasarkan 3 pilar:

$$\text{Priority Score} = 0.40 \times \text{Defisit SOC} + 0.35 \times \text{Urgensi Waktu} + 0.25 \times \text{Risiko Kebakaran}$$

- **Bobot 40% Defisit SOC:** Tanah dengan SOC < 0.50% (*CRITICAL*) mendapatkan prioritas intervensi tertinggi.
- **Bobot 35% Jendela Waktu:** Klaster dengan sisa hari panen (*harvest_days_left*) paling sedikit dilayani lebih awal.
- **Bobot 25% Riwayat Titik Api:** Hotspot kebakaran historis dari satelit NASA FIRMS.

### 2. Formula ICAR (Dampak per Ton Jerami Padi)

| Parameter | Nilai per Ton Jerami Padi |
| :--- | :--- |
| **Estimasi Jerami** | 5.5 Ton / Hektar Sawah Padi |
| **Karbon Organik Tanah (SOC)** | **400 kg (0.4 Ton)** diselamatkan |
| **Nitrogen (N)** | **5.5 kg** dikembalikan ke tanah |
| **Fosfor ($P_2O_5$)** | **2.3 kg** dikembalikan ke tanah |
| **Kalium ($K_2O$)** | **25.0 kg** dikembalikan ke tanah |
| **Nilai Ekonomi Pupuk** | Substitusi pupuk kimia: N @₹15/kg, P @₹55/kg, K @₹35/kg |

*Sumber rujukan: ICAR-CSSRI, Punjab Agricultural University (PAU) Ludhiana.*

---

## 📊 Dataset: `subak_soil_datasheet.csv`

Memuat **1.500 baris data klaster desa** di 22 Distrik Punjab dengan parameter:
- **Geospasial:** `cluster_id`, `cluster_name`, `block`, `district`, `latitude`, `longitude`
- **Kondisi Tanah:** `soil_organic_carbon_percent`, `soc_status`, `nitrogen_kg_ha`, `phosphorus_kg_ha`, `potassium_kg_ha`, `soil_ph`
- **Operasional Sawah:** `paddy_area_ha`, `harvest_days_left`, `chc_super_seeders_available`
- **Dampak & Nilai:** `potential_carbon_saved_tons`, `potential_nitrogen_saved_kg`, `fertilizer_savings_inr`
- **Referensi:** Soil Health Card DAC&FW, NASA FIRMS, FARMS App MoA&FW

---

## 🖥️ Fitur Interaktif Dashboard Web (`app.py`)

1. **Sidebar Kontrol Parameter:**
   - Pemilihan dari 22 Distrik Punjab (Sangrur, Ludhiana, Bathinda, Patiala, Amritsar, dll.).
   - Slider kapasitas armada harian per desa (5–25 mesin Super Seeder/hari).
2. **4 Kartu Metrik Dampak:**
   - Persentase lahan termulsa tepat waktu (+perbandingan vs Baseline CHC tanpa sinkronisasi).
   - Total ton Karbon Organik Tanah (SOC) yang terselamatkan.
   - Total kilogram hara NPK ($N + P_2O_5 + K_2O$) yang dikembalikan ke tanah.
   - Total penghematan biaya pupuk kimia petani (dalam Rupee / INR).
3. **Peta Geospasial Interaktif (PyDeck):**
   - 🟢 **Titik Hijau:** Desa yang tuntas termulsa 100% tepat waktu.
   - 🔴 **Titik Merah:** Desa darurat yang membutuhkan relokasi mesin tambahan.
   - Radius titik dinamis berdasarkan luas lahan sawah.
   - Tooltip interaktif menampilkan status SOC, ton karbon terselamatkan, dan deadline panen.
4. **Analisis Defisiensi Tanah:**
   - Distribusi status SOC distrik (Critical, Deficient, Moderate).
   - Tabel perbandingan parameter tanah aktual vs Ambang Batas Resmi ICAR.
5. **Jadwal Harian Super Seeder (Hari 1 s.d. Hari 15):**
   - Tabel alokasi armada harian per klaster desa.
   - Tombol unduh data jadwal dan data tanah dalam format CSV.

---

## 🚀 Panduan Menjalankan Aplikasi

### 1. Prasyarat Lingkungan
Pastikan Anda menggunakan Python 3.10+ (direkomendasikan Python 3.12).

### 2. Instalasi Dependensi
```bash
git clone https://github.com/willieka1/subak-soil.git
cd subak-soil
pip install -r requirements.txt
```

### 3. Eksekusi Engine Penjadwalan dari Terminal
```bash
python subak_soil_scheduler.py --input subak_soil_datasheet.csv --district Sangrur --output subak_schedule_output.csv
```
Output konsol:
```text
================ SUBAK-SOIL SOLVER RESULT ================
Solver Status:                 OPTIMAL (Subak Heuristic)
Solve Time:                    2.34 seconds
Lahan Termulsa Tepat Waktu:    64.6% (vs Baseline: 47.7%)
Desa Tuntas Terlayani:         20 / 69 klaster
Karbon Organik Diselamatkan:   19,157.6 Ton
Total Hara NPK Kembali:        1,570,922 kg
Penghematan Pupuk Kimia:       INR 51,917,038
==========================================================
```

### 4. Menjalankan Dashboard Web Lokal
```bash
streamlit run app.py
```
Aplikasi akan otomatis terbuka pada peramban: `http://localhost:8501`.

---

## 🌐 Deployment Publik (Streamlit Community Cloud)

Aplikasi telah terhubung ke GitHub dan dapat diakses langsung secara publik di:
👉 **[https://subak-soil.streamlit.app/](https://subak-soil.streamlit.app/)**

### Langkah Konfigurasi Cloud:
1. Hubungkan akun GitHub ke [share.streamlit.io](https://share.streamlit.io).
2. Tentukan **Repository:** `willieka1/subak-soil`.
3. Tentukan **Branch:** `main` dan **Main file path:** `app.py`.
4. Klik **Deploy** (proses build otomatis membaca `requirements.txt`).

---

## 📜 Lisensi & Atribusi
Dikembangkan untuk kompetisi **13th Protocol: An AI Hackathon 2026** (HackIndia, Greater Noida).
Mengintegrasikan filosofi Subak Bali dengan data terbuka pertanian India untuk ketahanan pangan dan penurunan emisi karbon.
