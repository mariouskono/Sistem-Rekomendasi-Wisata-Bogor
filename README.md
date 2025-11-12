# 🌳 Sistem Rekomendasi Wisata Bogor (BogorTravel)

Repositori ini berisi kode untuk **BogorTravel**, sebuah aplikasi web sistem rekomendasi tempat wisata cerdas di **Bogor, Indonesia**.  

Aplikasi ini menggunakan pendekatan **hybrid** yang menggabungkan:
- **Deep Learning (Autoencoder)** untuk kesamaan konten,  
- **Filter geospasial** untuk kedekatan lokasi,  
- **Filter kualitas** berdasarkan ulasan pengguna.  
---

## 🎯 Konsep Inti & Fokus Deep Learning  

Sistem ini bukan sekadar filter *if-else* sederhana. Inti proyek ini adalah penggunaan **Deep Learning (Autoencoder)** untuk *representation learning* — pembelajaran representasi fitur dari tempat wisata.  

### 🧩 Masalah  
Bagaimana mendefinisikan tempat wisata yang “mirip”?  
Jika pengguna menyukai *Curug Cilember* (Alam), apakah cukup merekomendasikan “tempat Alam” lainnya?  
Tentu tidak. *Kebun Raya Bogor* dan *Goa Garunggang* sama-sama “Alam”, tetapi memiliki esensi yang berbeda.  

---

## 💡 Solusi: Autoencoder untuk "DNA" Wisata  

Autoencoder digunakan untuk mempelajari “DNA” dari setiap tempat wisata, yaitu representasi vektor padat (*embedding*) yang memuat pola dan ciri khasnya.  

### 🏗️ Arsitektur Model
- **Input:** Vektor fitur gabungan untuk satu tempat wisata  
  Contoh: `[rating, jumlah_rating, kategori_alam, kategori_budaya, kecamatan_cisarua, ...]`
- **Encoder:** Lapisan Dense berturut-turut (contoh: 64 → 32)
- **Bottleneck:** Lapisan Dense berukuran kecil (contoh: 8) → inilah “DNA” wisata  
- **Decoder:** Lapisan cermin dari Encoder (contoh: 32 → 64)  

Setelah model dilatih (`autoencoder.fit()`), hanya bagian **Encoder** yang disimpan.  
Semua tempat wisata dilewatkan melalui Encoder untuk mendapatkan *embedding* (“DNA”) mereka.  

### 📊 Hasil
Dengan “DNA” ini, sistem menghitung **Cosine Similarity** antar tempat wisata.  
Hasilnya adalah matriks kesamaan (`similarity_matrix.npy`) yang menggambarkan seberapa mirip dua tempat wisata secara semantik, bukan hanya kategorinya.

Contohnya:  
*Taman Budaya Sentul City* bisa dianggap mirip dengan *Museum Zoologi Bogor* karena pola pengunjung, jenis kegiatan, dan rating — bukan semata karena label “Budaya”.

---

## 🚀 Alur Kerja Rekomendasi Hybrid  

Aplikasi **Streamlit** menggabungkan tiga lapisan filter secara *real-time*:  

1. **Input Pengguna**  
   Pengguna memilih tempat yang disukai, misal: “ECOART PARK Sentul City”.  
2. **Filter Deep Learning**  
   Aplikasi mencari “DNA” tempat tersebut dan mengambil daftar tempat paling mirip berdasarkan skor Cosine Similarity.  
3. **Filter Geospasial**  
   Hasil mirip tersebut difilter berdasarkan jarak (radius_km) menggunakan rumus Haversine.  
4. **Filter Kualitas**  
   Hasil akhir diurutkan berdasarkan rating tertinggi dan jumlah ulasan terbanyak.  
5. **Output**  
   Pengguna menerima daftar rekomendasi terbaik yang relevan secara konten, lokasi, dan kualitas.  

---

## 🛠️ Tumpukan Teknologi (Tech Stack)  

| Lapisan | Teknologi |
|----------|------------|
| Analisis & Model DL | Python, Pandas, NumPy, Scikit-learn, TensorFlow (Keras) |
| Aplikasi Web | Streamlit |
| Visualisasi Peta | Folium + streamlit-folium |
| Deployment | Streamlit Cloud |

---

## 📂 Struktur Repositori  

```

Sistem-Rekomendasi-Wisata-Bogor/
│
├── app.py                  # File utama aplikasi Streamlit
├── df_lookup_wisata.csv    # Data wisata bersih yang digunakan oleh app.py
├── similarity_matrix.npy   # "Otak" model DL, hasil pelatihan Autoencoder
├── requirements.txt        # Daftar library Python
├── Deep_Learning_Recommendation_System_Bogor.ipynb  # Notebook Colab untuk training model
└── README.md               # Dokumentasi proyek

````

---

## 🔑 Poin Penting  

- `app.py` **tidak melatih model**.  
- `app.py` hanya **memuat** `similarity_matrix.npy` dan `df_lookup_wisata.csv` agar aplikasi ringan dan cepat.  
- Model Deep Learning (Autoencoder) dilatih sekali di Colab, lalu hasil embedding digunakan oleh aplikasi.  

---

## ⚙️ Menjalankan Secara Lokal  

### 1. Clone repositori  
```bash
git clone https://github.com/mariouskono/Sistem-Rekomendasi-Wisata-Bogor.git
cd Sistem-Rekomendasi-Wisata-Bogor
````

### 2. Buat virtual environment (disarankan)

```bash
python -m venv venv
source venv/bin/activate  # (Mac/Linux)
.\venv\Scripts\activate   # (Windows)
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Jalankan aplikasi Streamlit

```bash
streamlit run app.py
```

Aplikasi akan terbuka otomatis di browser lokal Anda (biasanya di `http://localhost:8501`).

---

## ✨ Kontributor

**Bertnardo Mario Uskono** — Data Science, Deep Learning & Web Deployment

---

## 📸 Cuplikan Aplikasi

Tambahkan screenshot atau GIF interaktif dari tampilan Streamlit-mu di sini.

---

## 🧠 Lisensi

Proyek ini menggunakan lisensi MIT. Bebas digunakan untuk keperluan akademik dan penelitian.
