import streamlit as st
import xml.etree.ElementTree as et
import sqlitecloud
import requests
from datetime import date
from google import genai
from pydantic import BaseModel

def trendgetir(ulke="TR"):
    conn = sqlitecloud.connect(
        'sqlitecloud://cwcgjb0ahz.g1.sqlite.cloud:8860/chinook.sqlite?apikey=DaG8uyqMPa9GdxoR7ObMoajHIdfUOrc7B0mF0IrU6Y0'
    )
    c = conn.cursor()

    c.execute("CREATE TABLE IF NOT EXISTS trendler(isim TEXT,trafik INT,tarih TEXT,dil TEXT,isimtr TEXT)")
    conn.commit()

    c.execute("CREATE TABLE IF NOT EXISTS haberler(trend_id INT,baslik TEXT,link TEXT UNIQUE,resim TEXT,kaynak TEXT,basliktr TEXT)")
    conn.commit()

    r = requests.get(f'https://trends.google.com/trending/rss?geo={ulke}')
    veri = r.text
    haberler = et.fromstring(veri)
    haberler = haberler[0]

    for i in haberler.findall('item'):
        title = i.find('title').text
        trafik = int(i[1].text.replace("+", ""))
        tarih = str(date.today())

        c.execute("SELECT rowid FROM trendler WHERE isim=? AND tarih=? AND dil=?", (title, tarih, ulke))
        deger = c.fetchone()
        if deger is None:
            c.execute("INSERT INTO trendler VALUES(?,?,?,?,?)", (title, trafik, tarih, ulke, None))
            id = c.lastrowid
            conn.commit()
        else:
            id = deger[0]

        for m in i:
            if "news_item" in m.tag:
                baslik = m[0].text
                link = m[2].text
                resim = m[3].text
                kaynak = m[4].text

                c.execute("INSERT OR IGNORE INTO haberler VALUES(?,?,?,?,?,?)", (id, baslik, link, resim, kaynak, None))
                conn.commit()
    conn.close()

def geminicevir(basliklar):
    class Ceviri(BaseModel):
        ceviri: list[str]
    prompt = str(basliklar) + "--->bu konuları veya haberler başlıklarını türkçeye çevir"
    client = genai.Client(api_key="AIzaSyALuc_PAmFOK34wChTvnq6D3v3uknZtL4A")
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": Ceviri,
        },
    )
    ceviri: Ceviri = response.parsed.ceviri
    return ceviri

def trendcevir(limit=15):
    conn = sqlitecloud.connect(
        'sqlitecloud://cwcgjb0ahz.g1.sqlite.cloud:8860/chinook.sqlite?apikey=DaG8uyqMPa9GdxoR7ObMoajHIdfUOrc7B0mF0IrU6Y0'
    )
    c = conn.cursor()

    c.execute("SELECT rowid,* FROM trendler WHERE isimtr IS NULL OR isimtr='' ")
    veri = c.fetchall()

    idler = []
    basliklar = []
    basliklartr = []

    haberidler = []
    haberbasliklar = []
    haberbasliklartr = []

    for i in veri:
        if i[4] != "TR":
            idler.append(i[0])
            basliklar.append(i[1])

            c.execute("SELECT rowid,* FROM haberler WHERE trend_id=? AND basliktr IS NULL ", (i[0],))
            veri2 = c.fetchall()

            for j in veri2:
                haberidler.append(j[0])
                haberbasliklar.append(j[1])

    idler = idler[:limit]
    basliklar = basliklar[:limit]

    haberidler = haberidler[:limit]
    haberbasliklar = haberbasliklar[:limit]

    basliklartr = geminicevir(basliklar)
    haberbasliklartr = geminicevir(haberbasliklar)

    for i in range(len(idler)):
        c.execute("UPDATE trendler SET isimtr=? WHERE rowid=?", (basliklartr[i], idler[i]))
        conn.commit()

    for i in range(len(haberidler)):
        c.execute("UPDATE haberler SET basliktr=? WHERE rowid=?", (haberbasliklartr[i], haberidler[i]))
        conn.commit()

    print(haberidler, haberbasliklar)
    conn.close()
    return veri

def habercevir(haber_id):
    conn = sqlitecloud.connect(
        'sqlitecloud://cwcgjb0ahz.g1.sqlite.cloud:8860/chinook.sqlite?apikey=DaG8uyqMPa9GdxoR7ObMoajHIdfUOrc7B0mF0IrU6Y0'
    )
    c = conn.cursor()

    c.execute("SELECT basliktr,baslik FROM haberler WHERE rowid=?", (haber_id,))
    veri = c.fetchone()

    if veri[0] is None:
        import google.generativeai as genai
        genai.configure(api_key="AIzaSyALuc_PAmFOK34wChTvnq6D3v3uknZtL4A")
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(f" {veri[1]} ---> metni türkçeye çevir sadece çeviriyi yaz")
        c.execute("UPDATE haberler SET basliktr=? WHERE rowid=?", (response.text, haber_id))
        conn.commit()
    else:
        conn.close()
        return veri[0]

    conn.close()
    return response.text

def gununozeti(gun="", ulke_kodu="TR"):
    conn = sqlitecloud.connect(
        'sqlitecloud://cwcgjb0ahz.g1.sqlite.cloud:8860/chinook.sqlite?apikey=DaG8uyqMPa9GdxoR7ObMoajHIdfUOrc7B0mF0IrU6Y0'
    )
    c = conn.cursor()
    if gun == "":
        bugun = str(date.today())
        c.execute("SELECT rowid,* FROM trendler WHERE tarih=? AND dil=?", (bugun, ulke_kodu))
        trendler = c.fetchall()
    else:
        c.execute("SELECT rowid,* FROM trendler WHERE tarih=? AND dil=?", (gun, ulke_kodu))
        trendler = c.fetchall()

    haberlist = []
    for i in trendler:
        c.execute("SELECT h.* FROM trendler INNER JOIN haberler h ON h.trend_id=trendler.rowid WHERE trendler.rowid=?", (i[0],))
        haberler = c.fetchall()
        for x in haberler:
            haberlist.append(x[1])

    import google.generativeai as genai
    genai.configure(api_key="AIzaSyALuc_PAmFOK34wChTvnq6D3v3uknZtL4A")
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(f" {str(haberlist)} ---> bu günün haberlerini incele ve bu haberlere ait bir türkçe günün özeti çıkar")
    conn.close()
    return response.text

# --------- Streamlit Arayüzü ile Ülke Seçimi ve Gösterim ---------
st.title("Google Trends (Ülke Seçimi ile)")

ulke_kodlari = {
    "Türkiye": "TR",
    "ABD": "US",
    "Almanya": "DE",
    "Fransa": "FR",
    "İngiltere": "GB",
    "Japonya": "JP"
}

secilen_ulke = st.selectbox("Ülke seçiniz", options=list(ulke_kodlari.keys()))
ulke_kodu = ulke_kodlari[secilen_ulke]

if st.button("Trendleri Getir"):
    trendgetir(ulke=ulke_kodu)
    st.success(f"{secilen_ulke} için trendler çekildi!")

    # Trendleri ve haberleri göster
    conn = sqlitecloud.connect(
        'sqlitecloud://cwcgjb0ahz.g1.sqlite.cloud:8860/chinook.sqlite?apikey=DaG8uyqMPa9GdxoR7ObMoajHIdfUOrc7B0mF0IrU6Y0'
    )
    c = conn.cursor()
    bugun = str(date.today())
    c.execute("SELECT rowid, isim FROM trendler WHERE tarih=? AND dil=?", (bugun, ulke_kodu))
    trendler = c.fetchall()

    st.subheader(f"{secilen_ulke} için Bugünün Trendleri")
    for trend in trendler:
        st.markdown(f"**{trend[1]}**")
        # Haberi göster
        c.execute("SELECT baslik, link FROM haberler WHERE trend_id=?", (trend[0],))
        haberler = c.fetchall()
        if haberler:
            for haber in haberler:
                st.markdown(f"- [{haber[0]}]({haber[1]})")
        else:
            st.markdown("- Bu trend için haber bulunamadı.")
    conn.close()
