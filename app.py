import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import folium_static

# =============================================================================
# KONFIGURASI HALAMAN
# =============================================================================
st.set_page_config(
    page_title="Rekomendasi Wisata Bogor",
    page_icon="🌳",
    layout="wide"
)

# =============================================================================
# FUNGSI HELPER (Salin dari notebook)
# =============================================================================
def haversine(lat1, lon1, lat2, lon2):
    """
    Menghitung jarak antara dua titik koordinat (dalam km)
    """
    R = 6371  # Radius bumi dalam km
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

# =============================================================================
# MEMUAT DATA (MENGGUNAKAN CACHE)
# =============================================================================
# st.cache_data memastikan data hanya dimuat sekali
@st.cache_data
def load_data():
    """
    Memuat data lookup (bersih) dan matriks kesamaan (otak model)
    """
    try:
        # Ganti dengan path file Anda jika perlu
        df_lookup = pd.read_csv("df_lookup_wisata.csv")
    except FileNotFoundError:
        st.error("File 'df_lookup_wisata.csv' tidak ditemukan. Pastikan file ada di folder yang sama.")
        return None, None

    try:
        similarity_matrix = np.load("similarity_matrix.npy")
    except FileNotFoundError:
        st.error("File 'similarity_matrix.npy' tidak ditemukan. Pastikan file ada di folder yang sama.")
        return None, None
        
    return df_lookup, similarity_matrix

df_lookup, similarity_matrix = load_data()

# =============================================================================
# FUNGSI REKOMENDASI (Salin dari notebook)
# =============================================================================
def get_recommendations_hybrid(input_place_name, user_lat, user_lon, radius_km, top_n, df_lookup, similarity_matrix):
    """
    Memberikan rekomendasi hybrid (3 Lapis)
    """
    try:
        place_index = df_lookup[df_lookup['nama_tempat_wisata'] == input_place_name].index[0]
    except IndexError:
        st.error(f"Error: Tempat '{input_place_name}' tidak ditemukan.")
        return pd.DataFrame()

    similarity_scores = list(enumerate(similarity_matrix[place_index]))
    df_similar = pd.DataFrame(similarity_scores, columns=['index', 'similarity'])
    df_similar = df_similar.join(df_lookup)
    
    df_similar['distance_km'] = df_similar.apply(
        lambda row: haversine(user_lat, user_lon, row['latitude'], row['longitude']),
        axis=1
    )
    
    df_final_recs = df_similar[df_similar['nama_tempat_wisata'] != input_place_name]
    df_final_recs = df_final_recs[df_final_recs['distance_km'] <= radius_km]
    
    df_final_recs = df_final_recs.sort_values(
        by=['similarity', 'rating', 'jumlah_rating'],
        ascending=[False, False, False]
    )
    
    return df_final_recs.head(top_n)

# =============================================================================
# ANTARMUKA PENGGUNA (USER INTERFACE)
# =============================================================================

st.title("Sistem Rekomendasi Wisata Cerdas 🌳")
st.markdown("Temukan tempat wisata di Bogor berdasarkan kemiripan, kualitas, dan kedekatan lokasi.")

# Hanya lanjutkan jika data berhasil dimuat
if df_lookup is not None and similarity_matrix is not None:
    
    # --- Input Pengguna (di Sidebar) ---
    st.sidebar.header("Pencarian Anda")
    
    # 1. Pilih tempat wisata yang disukai
    # Ambil daftar nama tempat dari 'nama_tempat_wisata' di df_lookup
    place_list = df_lookup['nama_tempat_wisata'].unique()
    selected_place = st.sidebar.selectbox(
        "Pilih tempat wisata yang Anda sukai:",
        options=place_list,
        index=0 # Tampilkan item pertama sebagai default
    )
    
    # 2. Ambil lokasi pengguna (secara proxy dari tempat yang dipilih)
    # Ini adalah asumsi cerdas: lokasi pengguna adalah lokasi tempat yang ia pilih
    selected_place_data = df_lookup[df_lookup['nama_tempat_wisata'] == selected_place].iloc[0]
    user_lat = selected_place_data['latitude']
    user_lon = selected_place_data['longitude']
    
    st.sidebar.markdown(f"**Lokasi Anda (Asumsi):**")
    st.sidebar.markdown(f"`{selected_place}`")
    
    # 3. Pilih radius pencarian
    radius_km = st.sidebar.slider(
        "Cari dalam radius (km):",
        min_value=1,
        max_value=30,
        value=10, # Default 10km
        step=1
    )
    
    # 4. Pilih jumlah rekomendasi
    top_n = st.sidebar.number_input(
        "Jumlah rekomendasi:",
        min_value=3,
        max_value=10,
        value=5 # Default 5
    )

    # --- Tombol "Run" ---
    if st.sidebar.button("Dapatkan Rekomendasi"):
        
        st.header(f"Rekomendasi Teratas untuk Anda")
        st.markdown(f"Berdasarkan kemiripan dengan **{selected_place}**, dalam radius **{radius_km} km**.")
        
        # Panggil fungsi rekomendasi
        recs = get_recommendations_hybrid(
            selected_place, 
            user_lat, 
            user_lon, 
            radius_km, 
            top_n,
            df_lookup,
            similarity_matrix
        )
        
        if recs.empty:
            st.warning("Maaf, tidak ditemukan rekomendasi yang sesuai dengan kriteria Anda. Coba perbesar radius pencarian.")
        else:
            # --- Tampilkan Hasil ---
            st.success(f"Menampilkan {len(recs)} rekomendasi terbaik:")
            
            # Buat peta
            # Tentukan lokasi tengah peta
            map_center = [user_lat, user_lon]
            m = folium.Map(location=map_center, zoom_start=12)
            
            # Tambahkan marker untuk lokasi pengguna (tempat yang dipilih)
            folium.Marker(
                [user_lat, user_lon],
                tooltip=f"Lokasi Anda (Asumsi): {selected_place}",
                popup=f"Lokasi Anda: {selected_place}",
                icon=folium.Icon(color="blue", icon="user")
            ).add_to(m)

            # Tampilkan rekomendasi dalam kolom
            cols = st.columns(len(recs))
            
            for i, (col, idx) in enumerate(zip(cols, recs.index)):
                row = recs.loc[idx]
                
                with col:
                    st.subheader(f"{i+1}. {row['nama_tempat_wisata']}")
                    st.markdown(f"**Kategori:** `{row['kategori']}`")
                    st.markdown(f"**Rating:** {row['rating']} ⭐ ({row['jumlah_rating']} ulasan)")
                    st.markdown(f"**Jarak:** {row['distance_km']:.2f} km")
                    st.markdown(f"**Kesamaan:** {row['similarity']:.2%}")
                    st.link_button("Lihat di Google Maps", row['link'])

                # Tambahkan marker untuk setiap rekomendasi
                folium.Marker(
                    [row['latitude'], row['longitude']],
                    tooltip=f"{row['nama_tempat_wisata']} (Rating: {row['rating']})",
                    popup=f"{row['nama_tempat_wisata']}",
                    icon=folium.Icon(color="green", icon="tree-conifer")
                ).add_to(m)

            # Tampilkan peta di bawah hasil
            st.header("Peta Rekomendasi")
            folium_static(m, width=900, height=500)
            
else:
    st.error("Gagal memuat data. Aplikasi tidak dapat dijalankan.")
