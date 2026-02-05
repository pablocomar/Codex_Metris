import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from streamlit_plotly_events import plotly_events

DATA_DIR = Path("data")
PROVINCE_DATA_PATH = DATA_DIR / "provinces.json"
GEOJSON_PATH = DATA_DIR / "tr-81-il.geojson"
GEOJSON_URLS = [
    "https://raw.githubusercontent.com/cihadturhan/geojson/main/tr-81-il.geojson",
    "https://raw.githubusercontent.com/cihadturhan/geojson/master/tr-81-il.geojson",
]


@st.cache_data(show_spinner=False)
def load_province_data() -> List[Dict[str, str]]:
    with PROVINCE_DATA_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


@st.cache_data(show_spinner=False)
def load_geojson() -> Dict[str, Any]:
    if not GEOJSON_PATH.exists():
        last_error = None
        for url in GEOJSON_URLS:
            try:
                response = requests.get(url, timeout=20)
                response.raise_for_status()
            except requests.RequestException as exc:
                last_error = exc
                continue
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            GEOJSON_PATH.write_text(response.text, encoding="utf-8")
            last_error = None
            break
        if last_error is not None:
            st.error(
                "İl sınırlarını içeren GeoJSON dosyası indirilemedi. "
                "Lütfen ağ bağlantınızı kontrol edip tekrar deneyin."
            )
            raise RuntimeError("GeoJSON download failed") from last_error
    with GEOJSON_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize_name(name: str) -> str:
    replacements = str.maketrans({
        "ç": "c",
        "ğ": "g",
        "ı": "i",
        "ö": "o",
        "ş": "s",
        "ü": "u",
        "Ç": "c",
        "Ğ": "g",
        "İ": "i",
        "I": "i",
        "Ö": "o",
        "Ş": "s",
        "Ü": "u",
    })
    return name.translate(replacements).lower().strip()


def resolve_feature_key(geojson: Dict[str, Any]) -> str:
    sample_props = geojson.get("features", [{}])[0].get("properties", {})
    for key in ("name", "NAME_1", "NAME", "province"):
        if key in sample_props:
            return f"properties.{key}"
    return "properties.name"


def build_feature_name_map(geojson: Dict[str, Any], key: str) -> Dict[str, str]:
    prop_key = key.split(".", 1)[1]
    mapping: Dict[str, str] = {}
    for feature in geojson.get("features", []):
        raw_name = feature.get("properties", {}).get(prop_key, "")
        if raw_name:
            mapping[normalize_name(raw_name)] = raw_name
    return mapping


def build_dataframe(
    province_data: List[Dict[str, str]],
    feature_map: Dict[str, str],
) -> pd.DataFrame:
    records = []
    for item in province_data:
        normalized = normalize_name(item["name"])
        feature_name = feature_map.get(normalized, item["name"])
        records.append({
            "name": item["name"],
            "feature_name": feature_name,
            "culture": item["culture"],
        })
    return pd.DataFrame(records)


def select_province(
    province_names: List[str],
    click_event: Optional[List[Dict[str, Any]]],
) -> str:
    if click_event:
        return click_event[0].get("customdata", [""])[0] or province_names[0]
    return st.selectbox("İl seç", province_names)


st.set_page_config(page_title="Türkiye 81 İl Kültür Haritası", layout="wide")

st.title("Türkiye 81 İl Kültür Haritası")
st.markdown(
    "Haritadaki illere tıklayarak ya da listeden seçerek o ilin kültürel "
    "özelliklerini öğrenebilirsiniz."
)

province_data = load_province_data()
geojson = load_geojson()
feature_key = resolve_feature_key(geojson)
feature_map = build_feature_name_map(geojson, feature_key)

df = build_dataframe(province_data, feature_map)

fig = px.choropleth(
    df,
    geojson=geojson,
    locations="feature_name",
    featureidkey=feature_key,
    color="name",
    hover_name="name",
)
fig.update_geos(fitbounds="locations", visible=False)
fig.update_layout(
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
    showlegend=False,
    height=600,
)
fig.update_traces(customdata=df[["name"]])

selected_points = plotly_events(fig, click_event=True, hover_event=False, select_event=False)
selected_province = select_province(df["name"].tolist(), selected_points)

selected_row = df[df["name"] == selected_province].iloc[0]

with st.container():
    st.subheader(f"{selected_row['name']} kültürel tanıtım")
    st.write(selected_row["culture"])

st.info(
    "Bu uygulama, Türkiye'nin 81 iline ait kültürel öğeleri öğretici bir şekilde "
    "tanıtmak için hazırlanmıştır."
)
