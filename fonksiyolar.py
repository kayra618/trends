import streamlit as st
import xml.etree.ElementTree as et
import sqlitecloud
import sqlite3
import requests
from datetime import date
from google import genai
from pydantic import BaseModel
from fonksiyolar import trendgetir

diller = ["TR", "DE", "IT", "KR", "FR", "NL", "DK"]

st.title("Trend Haberler")

# Ülke/dil seçimi
dilsecimi = st.multiselect("Ülke seç", diller)

guncelle = st.sidebar.button("Haberleri Güncelle")

# Seçime göre güncelleme işlemi
if guncelle:
    if dilsecimi:  # Kullanıcı seçim yaptıysa
        for dil in dilsecimi:
            trendgetir(dil)
        st.success(f"{', '.join(dilsecimi)} için haberler güncellendi.")
    else:  # Hiç seçim yapılmadıysa
        st.warning("Lütfen en az bir ülke seçiniz!")

ara = st.text_input("Haber İçinde Arama Yap")

conn = sqlitecloud.connect('sqlitecloud://cwcgjb0ahz.g1.sqlite.cloud:8860/chinook.sqlite?apikey=DaG8uyqMPa9GdxoR7ObMoajHIdfUOrc7B0mF0IrU6Y0')
c = conn.cursor()

if len(ara) > 1:
    c.execute(f"SELECT * FROM haberler WHERE baslik LIKE '%{ara}%' ORDER BY trend_id DESC LIMIT 99 ")
else:
    c.execute("SELECT * FROM haberler ORDER BY trend_id DESC LIMIT 99")

haberler = c.fetchall()

if len(haberler) == 0:
    st.warning(f"{ara} sorgusu ile ilgili herhangi bir haber bulunamadı")

for i in range(0, len(haberler), 3):
    col1, col2, col3 = st.columns(3)

    with col1:
        st.image(haberler[i][3])
        st.write(haberler[i][1])
        st.link_button("Habere Git", haberler[i][2])
    with col2:
        if i + 1 < len(haberler):
            st.image(haberler[i + 1][3])
            st.write(haberler[i + 1][1])
            st.link_button("Habere Git", haberler[i + 1][2])
    with col3:
        if i + 2 < len(haberler):
            st.image(haberler[i + 2][3])
            st.write(haberler[i + 2][1])
            st.link_button("Habere Git", haberler[i + 2][2])
