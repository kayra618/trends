import streamlit as st
import sqlitecloud
from datetime import date
from pydantic import BaseModel
from fonksiyonlar import trendgetir

# Kullanılan diller listesi
diller = ["TR", "DE", "IT", "KR", "NL", "DK"]

# Güncelle butonu (sadece basınca çalışacak)
güncelle = st.sidebar.button("Haberleri Güncelle")

if güncelle:
    for dil in diller:
        trendgetir(dil)

# Arama kutusu
ara = st.text_input("Haber İçinde Arama Yap")

# Veritabanı bağlantısı
conn = sqlitecloud.connect(
    'sqlitecloud://cwcgjb0ahz.g1.sqlite.cloud:8860/chinook.sqlite?apikey=DaG8uyqMPa9GdxoR7ObMoajHIdfUOrc7B0mF0IrU6Y0'
)
c = conn.cursor()

# Güvenli arama sorgusu
if len(ara) > 1:
    c.execute("SELECT * FROM haberler WHERE baslik LIKE ? ORDER BY trend_id DESC LIMIT 99", ('%' + ara + '%',))
else:
    c.execute("SELECT * FROM haberler ORDER BY trend_id DESC LIMIT 99")

haberler = c.fetchall()

if len(haberler) == 0:
    st.warning(f"'{ara}' sorgusu ile ilgili herhangi bir haber bulunamadı")

# Haberleri üçlü gruplar halinde göster
for i in range(0, len(haberler), 3):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.image(haberler[i][3])
        st.write(haberler[i][1])
        st.link_button("Habere Git", haberler[i][2])
    if i + 1 < len(haberler):
        with col2:
            st.image(haberler[i+1][3])
            st.write(haberler[i+1][1])
            st.link_button("Habere Git", haberler[i+1][2])
    if i + 2 < len(haberler):
        with col3:
            st.image(haberler[i+2][3])
            st.write(haberler*

