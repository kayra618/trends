import streamlit as st
import xml.etree.ElementTree as et
import sqlitecloud
import requests
from datetime import date
from google import generativeai as genai
from pydantic import BaseModel

# Google Gemini API yapılandırması
genai.configure(api_key="AIzaSyALuc_PAmFOK34wChTvnq6D3v3uknZtL4A")  # Buraya kendi API anahtarını yaz

def trendgetir(ulke="TR"):
    conn = sqlitecloud.connect('sqlitecloud://cwcgjb0ahz.g1.sqlite.cloud:8860/chinook.sqlite?apikey=YOUR_SQLITECLOUD_API_KEY')
    c = conn.cursor()

    c.execute("CREATE TABLE IF NOT EXISTS trendler(isim TEXT,trafik INT,tarih TEXT,dil TEXT,isimtr TEXT)")
    conn.commit()

    c.execute("CREATE TABLE IF NOT EXISTS haberler(trend_id INT,baslik TEXT,link TEXT UNIQUE,resim TEXT,kaynak TEXT,basliktr TEXT)")
    conn.commit()

    r = requests.get(f'https://trends.google.com/trending/rss?geo={ulke}')
    haberler = et.fromstring(r.text)[0]

    for i in haberler.findall('item'):
        title = i.find('title').text
        trafik = int(i[1].text.replace("+", ""))
        tarih = str(date.today())

        c.execute("SELECT * FROM trendler WHERE isim=? AND tarih=?", (title, tarih))
        if not c.fetchall():
            c.execute("INSERT INTO trendler VALUES(?,?,?,?,?)", (title, trafik, tarih, ulke, None))
            trend_id = c.lastrowid
        else:
            c.execute("SELECT rowid FROM trendler WHERE isim=? AND tarih=?", (title, tarih))
            trend_id = c.fetchone()[0]

        for m in i:
            if "news_item" in m.tag:
                baslik = m[0].text
                link = m[2].text
                resim = m[3].text
                kaynak = m[4].text
                c.execute("INSERT OR IGNORE INTO haberler VALUES(?,?,?,?,?,?)", (trend_id, baslik, link, resim, kaynak, None))
    conn.commit()
    conn.close()

class Ceviri(BaseModel):
    ceviri: list[str]

def geminicevir(basliklar):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"{str(basliklar)} ---> bu konuları veya haber başlıklarını Türkçeye çevir"
    response = model.generate_content(prompt)
    return eval(response.text) if response.text else []

def trendcevir(limit=15):
    conn = sqlitecloud.connect('sqlitecloud://cwcgjb0ahz.g1.sqlite.cloud:8860/chinook.sqlite?apikey=YOUR_SQLITECLOUD_API_KEY')
    c = conn.cursor()

    c.execute("SELECT rowid,* FROM trendler WHERE isimtr IS NULL OR isimtr='' ")
    veri = c.fetchall()

    idler, basliklar = [], []
    haberidler, haberbasliklar = [], []

    for i in veri:
        if i[4] != "TR":
            idler.append(i[0])
            basliklar.append(i[1])
            c.execute("SELECT rowid,* FROM haberler WHERE trend_id=? AND basliktr IS NULL", (i[0],))
            for j in c.fetchall():
                haberidler.append(j[0])
                haberbasliklar.append(j[1])

    idler, basliklar = idler[:limit], basliklar[:limit]
    haberidler, haberbasliklar = haberidler[:limit], haberbasliklar[:limit]

    basliklartr = geminicevir(basliklar)
    haberbasliklartr = geminicevir(haberbasliklar)

    for i in range(len(idler)):
        c.execute("UPDATE trendler SET isimtr=? WHERE rowid=?", (basliklartr[i], idler[i]))
    for i in range(len(haberidler)):
        c.execute("UPDATE haberler SET basliktr=? WHERE rowid=?", (haberbasliklartr[i], haberidler[i]))

    conn.commit()
    conn.close()

def gununozeti():
    conn = sqlitecloud.connect('sqlitecloud://cwcgjb0ahz.g1.sqlite.cloud:8860/chinook.sqlite?apikey=YOUR_SQLITECLOUD_API_KEY')
    c = conn.cursor()

    bugun = str(date.today())
    c.execute("SELECT rowid,* FROM trendler WHERE tarih=?", (bugun,))
    trendler = c.fetchall()

    haberlist = []
    for i in trendler:
        c.execute("SELECT h.* FROM trendler INNER JOIN haberler h ON h.trend_id=trendler.rowid WHERE trendler.rowid=?", (i[0],))
        haberlist.extend([x[1] for x in c.fetchall()])

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(f"{str(haberlist)} ---> bu günün haberlerini incele ve bu haberlere ait bir Türkçe günün özeti çıkar")
    return response.text

# STREAMLIT UI
st.set_page_config(page_title="Trend Takip ve Özet", layout="wide")
st.title("📈 Google Trendler & Haber Özeti")

if st.button("1. Trendleri Getir"):
    trendgetir()
    st.success("Trendler başarıyla çekildi!")

if st.button("2. Başlıkları Türkçeye Çevir"):
    trendcevir()
    st.success("Başlıklar Türkçeye çevrildi!")

if st.button("3. Günün Özetini Al"):
    ozet = gununozeti()
    st.subheader("🗞️ Günün Özeti")
    st.write(ozet)
