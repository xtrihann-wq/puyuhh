import streamlit as st
import pandas as pd
from datetime import datetime
import io

# ==========================================
# 1. KONFIGURASI HALAMAN & DATABASE (MOCK)
# ==========================================
st.set_page_config(page_title="PuyuhKu - Sistem Manajemen Peternakan", layout="wide", page_icon="🐣")

# Inisialisasi Database Sederhana dalam Session State
if 'produksi' not in st.session_state:
    st.session_state['produksi'] = pd.DataFrame(columns=["Tanggal", "Populasi_Aktif", "Mortalitas", "Telur_Butir", "Telur_Kg", "Pakan_Kg"])

if 'kasir' not in st.session_state:
    st.session_state['kasir'] = pd.DataFrame(columns=["Tanggal", "Varian", "Harga_Satuan", "Kuantitas", "Total_Rp"])

if 'pengeluaran' not in st.session_state:
    st.session_state['pengeluaran'] = pd.DataFrame(columns=["Tanggal", "Kategori", "Deskripsi", "Nominal_Rp"])

# Data Katalog Harga
VARIAN_TELUR = {
    "Per Kilo (1 kg)": 33000,
    "Tengahan (0.5 kg)": 1700,
    "Seperempat (0.25 kg)": 9000
}

# ==========================================
# 2. NAVIGASI SIDEBAR
# ==========================================
st.sidebar.title("🐣 PuyuhKu")
st.sidebar.markdown("Sistem Pencatatan Peternakan")
menu = st.sidebar.radio("Navigasi Menu", ["Dashboard & Prediksi", "Catat Produksi Harian", "Kasir / Penjualan", "Keuangan (Pengeluaran)", "Export ke Excel"])

# ==========================================
# 3. LOGIKA APLIKASI BERDASARKAN MENU
# ==========================================

if menu == "Dashboard & Prediksi":
    st.title("📊 Dashboard Utama")
    
    # Ambil data untuk kalkulasi
    df_prod = st.session_state['produksi']
    df_kasir = st.session_state['kasir']
    df_peng = st.session_state['pengeluaran']
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Hitung Metrik
    total_telur_kg = df_prod["Telur_Kg"].sum() if not df_prod.empty else 0
    total_pakan_kg = df_prod["Pakan_Kg"].sum() if not df_prod.empty else 0
    
    # FCR (Feed Conversion Ratio) = Total Pakan (kg) / Total Telur (kg)
    fcr = (total_pakan_kg / total_telur_kg) if total_telur_kg > 0 else 0
    
    # Keuangan
    total_pemasukan = df_kasir["Total_Rp"].sum() if not df_kasir.empty else 0
    total_pengeluaran = df_peng["Nominal_Rp"].sum() if not df_peng.empty else 0
    laba_bersih = total_pemasukan - total_pengeluaran

    with col1:
        st.metric("Total Produksi (Kg)", f"{total_telur_kg:.2f} Kg")
    with col2:
        # FCR Ideal biasanya di bawah 2.5
        st.metric("Nilai FCR", f"{fcr:.2f}", delta="Ideal < 2.5" if fcr < 2.5 else "Beresiko (Boros)", delta_color="inverse")
    with col3:
        st.metric("Total Pendapatan", f"Rp {total_pemasukan:,.0f}")
    with col4:
        st.metric("Laba Bersih", f"Rp {laba_bersih:,.0f}")

    st.divider()
    
    # Sistem Pengingat (Reminder Box)
    st.subheader("🔔 Pengingat & Notifikasi")
    if total_pakan_kg > 500: # Contoh logika peringatan stok
        st.warning("Peringatan: Berdasarkan riwayat konsumsi, stok pakan di gudang mungkin menipis. Cek ketersediaan pakan!")
    else:
        st.success("Stok pakan dan jadwal sanitasi aman.")

elif menu == "Catat Produksi Harian":
    st.title("📝 Pencatatan Produksi Harian")
    
    with st.form("form_produksi"):
        col1, col2 = st.columns(2)
        with col1:
            tgl = st.date_input("Tanggal Produksi", datetime.today())
            populasi = st.number_input("Estimasi Populasi Aktif (Ekor)", min_value=0, value=1000)
            mati = st.number_input("Mortalitas / Afkir (Ekor)", min_value=0, value=0)
        with col2:
            telur_butir = st.number_input("Jumlah Telur Dipanen (Butir)", min_value=0)
            telur_kg = st.number_input("Berat Telur Total (Kg)", min_value=0.0, format="%.2f")
            pakan = st.number_input("Konsumsi Pakan Hari Ini (Kg)", min_value=0.0, format="%.2f")
            
        submit = st.form_submit_button("Simpan Data Produksi")
        
        if submit:
            new_data = pd.DataFrame([{
                "Tanggal": tgl, "Populasi_Aktif": populasi - mati, "Mortalitas": mati,
                "Telur_Butir": telur_butir, "Telur_Kg": telur_kg, "Pakan_Kg": pakan
            }])
            st.session_state['produksi'] = pd.concat([st.session_state['produksi'], new_data], ignore_index=True)
            st.success("Data produksi berhasil disimpan!")

elif menu == "Kasir / Penjualan":
    st.title("🛒 Kasir Penjualan Telur")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Input Transaksi")
        tgl_kasir = st.date_input("Tanggal Transaksi", datetime.today())
        varian = st.selectbox("Pilih Varian Berat", list(VARIAN_TELUR.keys()))
        harga_satuan = VARIAN_TELUR[varian]
        
        # Penyesuaian Harga Jual Otomatis
        st.info(f"Harga per item: **Rp {harga_satuan:,.0f}**")
        
        kuantitas = st.number_input("Kuantitas Pembelian", min_value=1, value=1)
        total_harga = harga_satuan * kuantitas
        
        st.success(f"Total Bayar: **Rp {total_harga:,.0f}**")
        
        if st.button("Simpan Transaksi"):
            new_trans = pd.DataFrame([{
                "Tanggal": tgl_kasir, "Varian": varian, "Harga_Satuan": harga_satuan, 
                "Kuantitas": kuantitas, "Total_Rp": total_harga
            }])
            st.session_state['kasir'] = pd.concat([st.session_state['kasir'], new_trans], ignore_index=True)
            st.toast("Transaksi berhasil dicatat ke Kas!", icon="✅")

    with col2:
        st.subheader("Riwayat Transaksi Terakhir")
        st.dataframe(st.session_state['kasir'].tail(5), use_container_width=True)

elif menu == "Keuangan (Pengeluaran)":
    st.title("💸 Pencatatan Arus Kas Keluar")
    
    with st.form("form_pengeluaran"):
        tgl_peng = st.date_input("Tanggal", datetime.today())
        kategori = st.selectbox("Kategori Pengeluaran", ["Beli Pakan", "Vitamin/Obat", "Gaji Karyawan", "Listrik & Air", "Lainnya"])
        deskripsi = st.text_input("Keterangan Detail (Contoh: Beli pakan sentrat 5 karung)")
        nominal = st.number_input("Nominal Pengeluaran (Rp)", min_value=0, step=50000)
        
        simpan_pengeluaran = st.form_submit_button("Simpan Pengeluaran")
        
        if simpan_pengeluaran:
            new_peng = pd.DataFrame([{"Tanggal": tgl_peng, "Kategori": kategori, "Deskripsi": deskripsi, "Nominal_Rp": nominal}])
            st.session_state['pengeluaran'] = pd.concat([st.session_state['pengeluaran'], new_peng], ignore_index=True)
            st.success("Data pengeluaran tercatat!")
            
    st.subheader("Riwayat Pengeluaran")
    st.dataframe(st.session_state['pengeluaran'], use_container_width=True)

elif menu == "Export ke Excel":
    st.title("📁 Export Laporan ke Excel")
    st.markdown("Fitur ini akan menyusun seluruh data (Produksi, Penjualan, dan Keuangan) menjadi file Excel berekstensi `.xlsx` yang sangat rapi dan siap dicetak.")
    
    # Proses konversi dataframe ke Excel format
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        st.session_state['produksi'].to_excel(writer, sheet_name='Data_Produksi', index=False)
        st.session_state['kasir'].to_excel(writer, sheet_name='Penjualan', index=False)
        st.session_state['pengeluaran'].to_excel(writer, sheet_name='Pengeluaran', index=False)
        
    output.seek(0)
    
    st.download_button(
        label="📥 Download Laporan Lengkap (.xlsx)",
        data=output,
        file_name=f"Laporan_PuyuhKu_{datetime.today().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
