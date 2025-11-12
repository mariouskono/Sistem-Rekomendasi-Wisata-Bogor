import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import folium_static

# =============================================================================
# KONFIGURASI HALAMAN
# =============================================================================
st.set_page_config(
    page_title="BogorTravel",  # NAMA BARU
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
@st.cache_data
def load_data():
    """
    Memuat data lookup (bersih) dan matriks kesamaan (otak model)
    """
    try:
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

# --- CSS KUSTOM UNTUK CARD SIMETRIS ---
# Ini adalah "sihir"-nya.
# Kita target `st.container(border=True)` (yaitu `[data-testid="stBlock"]`)
# dan memaksanya memiliki tinggi minimal dan layout flexbox
st.markdown("""
    <style>
    [data-testid="stBlock"] {
        /* Ini adalah elemen st.container(border=True) */
        padding: 1rem;
        border-radius: 0.5rem;
        min-height: 280px; /* Paksa tinggi minimal untuk semua card */
        display: flex;
        flex-direction: column;
        justify-content: space-between; /* Dorong tombol ke bawah */
    }
    [data-testid="stBlock"] h4 { /* Atur ukuran judul card */
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.25rem;
    }
    [data-testid="stBlock"] .stMarkdown {
        margin-bottom: 0.25rem; /* Kurangi jarak antar teks */
    }
    </style>
    """, unsafe_allow_html=True)

st.title("BogorTravel 🌳") # NAMA BARU
st.markdown("Temukan tempat wisata di Bogor berdasarkan kemiripan, kualitas, dan kedekatan lokasi.")

if df_lookup is not None and similarity_matrix is not None:
    
    st.sidebar.header("Pencarian Anda")
    
    place_list = df_lookup['nama_tempat_wisata'].unique()
    selected_place = st.sidebar.selectbox(
        "Pilih tempat wisata yang Anda sukai:",
        options=place_list,
        index=0
    )
    
    selected_place_data = df_lookup[df_lookup['nama_tempat_wisata'] == selected_place].iloc[0]
    user_lat = selected_place_data['latitude']
    user_lon = selected_place_data['longitude']
    
    st.sidebar.markdown(f"**Lokasi Anda (Asumsi):**")
    st.sidebar.markdown(f"`{selected_place}`")
    
    radius_km = st.sidebar.slider(
        "Cari dalam radius (km):", 1, 30, 10, 1
    )
    
    top_n = st.sidebar.number_input(
        "Jumlah rekomendasi:", 3, 10, 5 # Ubah max_value ke 10
    )

    if st.sidebar.button("Dapatkan Rekomendasi"):
        
        st.header(f"Rekomendasi Teratas untuk Anda")
        st.markdown(f"Berdasarkan kemiripan dengan **{selected_place}**, dalam radius **{radius_km} km**.")
        
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
            st.success(f"Menampilkan {len(recs)} rekomendasi terbaik:")
            
            # --- PERUBAHAN TATA LETAK CARD ---
            # Buat 5 kolom untuk grid
            cols = st.columns(5)
            
            for i, idx in enumerate(recs.index):
                row = recs.loc[idx]
                
                # Gunakan 'i % 5' untuk menempatkan card di kolom yang benar
                # Ini akan otomatis "wrap" ke baris berikutnya setelah 5 card
                with cols[i % 5]:
                    # Gunakan st.container(border=True) untuk membuat card
                    with st.container(border=True):
                        # Grup 1: Info Teks (akan ada di atas)
                        st.markdown(f"<h4>{i+1}. {row['nama_tempat_wisata']}</h4>", unsafe_allow_html=True)
                        st.markdown(f"`{row['kategori']}`")
                        st.markdown(f"**Rating:** {row['rating']} ⭐ ({row['jumlah_rating']} ulasan)")
                        st.markdown(f"**Jarak:** {row['distance_km']:.2f} km")
                        st.markdown(f"**Kesamaan:** {row['similarity']:.1%}")
                        
                        # Grup 2: Tombol (akan terdorong ke bawah)
                        st.link_button("Lihat di Google Maps", row['link'], use_container_width=True)

            # --- PETA REKOMENDASI ---
            st.header("Peta Rekomendasi")
            map_center = [user_lat, user_lon]
            m = folium.Map(location=map_center, zoom_start=12)
            
            # Marker Lokasi Pengguna
            folium.Marker(
                [user_lat, user_lon],
                tooltip=f"Lokasi Anda (Asumsi): {selected_place}",
                popup=f"Lokasi Anda: {selected_place}",
                icon=folium.Icon(color="blue", icon="user")
            ).add_to(m)

            # Marker Rekomendasi
            for i, row in recs.iterrows():
                folium.Marker(
                    [row['latitude'], row['longitude']],
                    tooltip=f"{row['nama_tempat_wisata']} (Rating: {row['rating']})",
                    popup=f"{row['nama_tempat_wisata']}",
                    icon=folium.Icon(color="green", icon="tree-conifer")
                ).add_to(m)

            folium_static(m, width=900, height=500)
            
else:
    st.error("Gagal memuat data. Aplikasi tidak dapat dijalankan.")
