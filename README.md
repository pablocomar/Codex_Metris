# Türkiye 81 İl Kültür Haritası

Bu proje, Türkiye'nin 81 iline ait kültürel öğeleri öğretici bir harita üzerinde gösteren bir Python uygulamasıdır.

## Kurulum

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Çalıştırma

```bash
streamlit run app.py
```

Uygulama, ilk çalıştırmada il sınırları için gerekli GeoJSON dosyasını indirip `data/tr-81-il.geojson` konumuna kaydeder.
