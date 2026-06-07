from __future__ import annotations

import base64
import mimetypes
import re
from datetime import date
from math import floor
from math import ceil
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse

import pandas as pd
import pydeck as pdk
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st


API_BASE = "https://api.obis.org/v3"
ASSET_DIR = Path(__file__).resolve().parent / "work" / "species_images"
SPECIES_CACHE_DIR = ASSET_DIR / "species_cache"
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
HTTP_HEADERS = {
    "User-Agent": "OBISDashboard/1.0 (species image caching)",
}
PLOTLY_CONFIG = {
    "displayModeBar": "hover",
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
}

ASSET_DIR.mkdir(parents=True, exist_ok=True)
SPECIES_CACHE_DIR.mkdir(parents=True, exist_ok=True)

GROUP_COLORS = {
    "Mamíferos marinos": [255, 145, 77, 185],
    "Peces cartilaginosos": [255, 111, 97, 185],
    "Peces óseos": [53, 214, 209, 185],
    "Moluscos": [126, 176, 255, 185],
    "Cnidarios": [181, 120, 255, 185],
    "Reptiles marinos": [130, 210, 120, 185],
    "Equinodermos": [255, 196, 92, 185],
    "Artrópodos": [255, 160, 120, 185],
    "Bacterias y arqueas": [102, 217, 255, 185],
    "Microorganismos eucariotas": [88, 205, 173, 185],
    "Plantas y macroalgas": [120, 214, 132, 185],
    "Hongos marinos": [196, 160, 255, 185],
    "Aves marinas": [255, 214, 102, 185],
    "Otros organismos marinos": [90, 185, 230, 185],
}

SPECIES = {
    "Todas las especies": {
        "scientific_name": None,
        "group": "Vista global",
        "image": "tortuga_verde.png",
        "note": "Resumen amplio para explorar composición y patrones de biodiversidad marina.",
    },
    "Tortuga verde": {
        "scientific_name": "Chelonia mydas",
        "group": "Reptiles marinos",
        "image": "tortuga_verde.png",
        "note": "Especie migratoria asociada a zonas tropicales y subtropicales.",
    },
    "Mantarraya gigante": {
        "scientific_name": "Mobula birostris",
        "group": "Peces cartilaginosos",
        "image": "mantarraya_gigante.png",
        "note": "Filtradora pelágica con registros distribuidos en aguas cálidas.",
    },
    "Ballena azul": {
        "scientific_name": "Balaenoptera musculus",
        "group": "Mamíferos marinos",
        "image": "ballena_azul.png",
        "note": "El mayor cetáceo del planeta y un buen caso para observar patrones globales.",
    },
    "Pez payaso común": {
        "scientific_name": "Amphiprion ocellaris",
        "group": "Peces óseos",
        "image": "pez_payaso_comun.png",
        "note": "Asociado a arrecifes y anémonas en el Indo-Pacífico.",
    },
    "Pulpo común": {
        "scientific_name": "Octopus vulgaris",
        "group": "Moluscos",
        "image": "pulpo_comun.png",
        "note": "Molusco bentónico usado frecuentemente en consultas de ocurrencias.",
    },
    "Medusa luna": {
        "scientific_name": "Aurelia aurita",
        "group": "Cnidarios",
        "image": "medusa_luna.png",
        "note": "Cnidario cosmopolita con registros en múltiples regiones costeras.",
    },
    "Tiburón martillo": {
        "scientific_name": "Sphyrna lewini",
        "group": "Peces cartilaginosos",
        "image": "tiburon_martillo.png",
        "note": "Especie pelágica costera registrada en regiones tropicales y subtropicales.",
    },
    "Delfín nariz de botella": {
        "scientific_name": "Tursiops truncatus",
        "group": "Mamíferos marinos",
        "image": "delfin_nariz_de_botella.png",
        "note": "Cetáceo ampliamente distribuido en aguas costeras y oceánicas.",
    },
    "León marino de California": {
        "scientific_name": "Zalophus californianus",
        "group": "Mamíferos marinos",
        "image": "leon_marino_de_california.png",
        "note": "Pinnípedo costero frecuente en el Pacífico oriental.",
    },
    "Tiburón ballena": {
        "scientific_name": "Rhincodon typus",
        "group": "Peces cartilaginosos",
        "image": "tiburon_ballena.png",
        "note": "El pez más grande del mundo, asociado a aguas cálidas.",
    },
    "Atún aleta amarilla": {
        "scientific_name": "Thunnus albacares",
        "group": "Peces óseos",
        "image": "atun_aleta_amarilla.png",
        "note": "Especie oceánica de gran interés pesquero y amplia movilidad.",
    },
    "Caballito de mar": {
        "scientific_name": "Hippocampus kuda",
        "group": "Peces óseos",
        "image": "caballito_de_mar.png",
        "note": "Especie costera asociada a pastos marinos y arrecifes.",
    },
    "Estrella de mar azul": {
        "scientific_name": "Linckia laevigata",
        "group": "Equinodermos",
        "image": "estrella_de_mar_azul.png",
        "note": "Equinodermo tropical común en arrecifes del Indo-Pacífico.",
    },
    "Erizo de mar púrpura": {
        "scientific_name": "Strongylocentrotus purpuratus",
        "group": "Equinodermos",
        "image": None,
        "note": "Especie bentónica útil para explorar zonas rocosas y costeras.",
    },
    "Coral cuerno de alce": {
        "scientific_name": "Acropora palmata",
        "group": "Cnidarios",
        "image": "coral_cuerno_de_alce.png",
        "note": "Coral arrecifal emblemático del Caribe.",
    },
    "Langosta espinosa": {
        "scientific_name": "Panulirus argus",
        "group": "Artrópodos",
        "image": "langosta_espinosa.png",
        "note": "Crustáceo costero tropical presente en arrecifes y fondos duros.",
    },
    "Cangrejo violinista": {
        "scientific_name": "Uca vocator",
        "group": "Artrópodos",
        "image": None,
        "note": "Crustáceo asociado a manglares y planicies intermareales.",
    },
    "Almeja gigante": {
        "scientific_name": "Tridacna gigas",
        "group": "Moluscos",
        "image": None,
        "note": "Bivalvo arrecifal de gran tamaño registrado en el Indo-Pacífico.",
    },
    "Calamar gigante": {
        "scientific_name": "Architeuthis dux",
        "group": "Moluscos",
        "image": None,
        "note": "Cefalópodo oceánico de aguas profundas y registros dispersos.",
    },
    "Mero gigante": {
        "scientific_name": "Epinephelus lanceolatus",
        "group": "Peces óseos",
        "image": None,
        "note": "Gran pez arrecifal tropical de distribución amplia.",
    },
    "Barracuda gigante": {
        "scientific_name": "Sphyraena barracuda",
        "group": "Peces óseos",
        "image": None,
        "note": "Depredador costero y oceánico de aguas tropicales.",
    },
}

KNOWN_SPECIES_BY_SCIENTIFIC = {
    info["scientific_name"]: {"common_name": common_name, **info}
    for common_name, info in SPECIES.items()
    if info["scientific_name"]
}

GROUP_IMAGE_FALLBACKS = {
    "Mamíferos marinos": "delfin_nariz_de_botella.png",
    "Peces cartilaginosos": "tiburon_ballena.png",
    "Peces óseos": "atun_aleta_amarilla.png",
    "Moluscos": "pulpo_comun.png",
    "Cnidarios": "coral_cuerno_de_alce.png",
    "Reptiles marinos": "tortuga_verde.png",
    "Equinodermos": "estrella_de_mar_azul.png",
    "Artrópodos": "langosta_espinosa.png",
    "Bacterias y arqueas": "medusa_luna.png",
    "Microorganismos eucariotas": "medusa_luna.png",
    "Plantas y macroalgas": "coral_cuerno_de_alce.png",
    "Hongos marinos": "coral_cuerno_de_alce.png",
    "Aves marinas": "ballena_azul.png",
    "Otros organismos marinos": "ballena_azul.png",
}

REGIONS = {
    "Todas las regiones": None,
    "Pacífico oriental": "POLYGON((-130 -55, -70 -55, -70 55, -130 55, -130 -55))",
    "Atlántico occidental": "POLYGON((-85 -55, -20 -55, -20 55, -85 55, -85 -55))",
    "Indo-Pacífico": "POLYGON((30 -45, 170 -45, 170 35, 30 35, 30 -45))",
    "Mediterráneo": "POLYGON((-6 30, 37 30, 37 46, -6 46, -6 30))",
}

FALLBACK_POINTS = pd.DataFrame(
    [
        {"scientificName": "Chelonia mydas", "decimalLatitude": -0.9, "decimalLongitude": -90.5, "date_year": 2022, "depth": 18, "country": "Ecuador", "class": "Reptilia", "phylum": "Chordata"},
        {"scientificName": "Chelonia mydas", "decimalLatitude": 13.4, "decimalLongitude": -61.2, "date_year": 2020, "depth": 12, "country": "Barbados", "class": "Reptilia", "phylum": "Chordata"},
        {"scientificName": "Mobula birostris", "decimalLatitude": -8.4, "decimalLongitude": 115.4, "date_year": 2021, "depth": 45, "country": "Indonesia", "class": "Chondrichthyes", "phylum": "Chordata"},
        {"scientificName": "Balaenoptera musculus", "decimalLatitude": 34.2, "decimalLongitude": -119.8, "date_year": 2019, "depth": 120, "country": "United States", "class": "Mammalia", "phylum": "Chordata"},
        {"scientificName": "Octopus vulgaris", "decimalLatitude": 36.5, "decimalLongitude": -6.2, "date_year": 2023, "depth": 30, "country": "Spain", "class": "Cephalopoda", "phylum": "Mollusca"},
        {"scientificName": "Aurelia aurita", "decimalLatitude": 55.7, "decimalLongitude": 12.6, "date_year": 2024, "depth": 8, "country": "Denmark", "class": "Scyphozoa", "phylum": "Cnidaria"},
    ]
)


st.set_page_config(
    page_title="Explorador OBIS",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def inject_style() -> None:
    hero_bg = image_to_data_uri("hero_biodiversidad_marina.png")
    hero_logo = image_to_data_uri("hero_logo.png")
    hero_bg_css = hero_bg or "https://images.unsplash.com/photo-1546026423-cc4642628d2b?auto=format&fit=crop&w=2200&q=85"
    hero_logo_css = hero_logo or ""
    styles = """
        <style>
        
        :root {
            --bg: #03070c;
            --panel: #0a1320;
            --panel-2: #101d2d;
            --panel-3: #14263a;
            --line: rgba(160, 204, 221, .24);
            --cyan: #35d6d1;
            --blue: #2f7dd9;
            --green: #83d46f;
            --amber: #ffb54d;
            --coral: #ff6f61;
            --text: #f7fbff;
            --muted: #b6c7d6;
        }

        header[data-testid="stHeader"] {
            background: transparent;
            height: 0;
            display: none;
        }

        [data-testid="stToolbar"] {
            display: none;
        }

        [data-testid="stDecoration"] {
            display: none;
        }

        [data-testid="stAppViewContainer"] {
            padding-top: 0 !important;
            margin-top: 0 !important;
        }

        .block-container {
            padding-top: 0;
            padding-bottom: 3rem;
            max-width: 1440px;
        }

        .stApp {
            background:
                url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='1600' height='320' viewBox='0 0 1600 320'%3E%3Cg fill='none' stroke='%2335d6d1' stroke-opacity='0.08' stroke-width='2'%3E%3Cpath d='M0 120 C120 90 220 90 340 120 S560 150 680 120 900 90 1020 120 1240 150 1360 120 1480 90 1600 120'/%3E%3Cpath d='M0 170 C120 140 220 140 340 170 S560 200 680 170 900 140 1020 170 1240 200 1360 170 1480 140 1600 170'/%3E%3Cpath d='M0 230 C120 200 220 200 340 230 S560 260 680 230 900 200 1020 230 1240 260 1360 230 1480 200 1600 230'/%3E%3C/g%3E%3C/svg%3E"),
                radial-gradient(circle at 72% 10%, rgba(47, 125, 217, .16), transparent 32%),
                radial-gradient(circle at 12% 36%, rgba(53, 214, 209, .12), transparent 28%),
                linear-gradient(180deg, #03070c 0%, #06101c 48%, #081625 100%);
            background-repeat: repeat-x, no-repeat, no-repeat, no-repeat;
            background-position: top center, top right, left 30%, center;
            color: var(--text);
        }

        h1, h2, h3, p, label, span {
            letter-spacing: 0;
        }

        [data-testid="stSidebar"] {
            background: #050b12;
            border-right: 1px solid var(--line);
        }

        .hero {
            background:
                linear-gradient(180deg, rgba(4, 14, 28, .30) 0%, rgba(4, 14, 28, .22) 36%, rgba(4, 14, 28, .45) 68%, rgba(4, 14, 28, .72) 100%),
                linear-gradient(90deg, rgba(5, 17, 31, .54) 0%, rgba(5, 17, 31, .34) 46%, rgba(5, 17, 31, .18) 100%),
                url("__HERO_BG__");
            background-size: cover;
            background-position: center 18%;
            border-radius: 8px;
            min-height: 320px;
            padding: 20px 36px 34px;
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            box-shadow: 0 24px 70px rgba(0, 0, 0, .32);
            margin-top: 0;
        }

        .hero-logo {
            width: min(150px, 21vw);
            height: auto;
            display: block;
            margin-bottom: 26px;
            filter: drop-shadow(0 4px 18px rgba(0, 0, 0, .28));
        }

        .hero h1 {
            margin: 0;
            font-size: clamp(2.2rem, 4vw, 4rem);
            line-height: 1.02;
            max-width: 1100px;
            color: #fff;
            font-weight: 900;
            text-align: center;
            align-self: center;
        }

        .hero p {
            color: #f1f6fb;
            margin: 20px 0 0;
            max-width: 1180px;
            font-size: 1.15rem;
            text-shadow: 0 2px 12px rgba(0, 0, 0, .8);
        }

        .summary-panel {
            border: 1px solid var(--line);
            background: linear-gradient(180deg, rgba(14, 31, 47, .96), rgba(8, 17, 29, .96));
            border-radius: 8px;
            padding: 18px 20px;
            margin: 18px 0 20px;
        }

        .summary-panel h3 {
            margin: 0 0 10px 0;
            font-size: 1.02rem;
            color: #f7fbff;
        }

        .summary-panel p {
            margin: 0 0 8px 0;
            color: #d5e4ef;
            font-size: .98rem;
        }

        .section-filter-bar {
            border: 1px solid var(--line);
            background: linear-gradient(180deg, rgba(14, 31, 47, .94), rgba(8, 17, 29, .94));
            border-radius: 8px;
            padding: 16px 18px 8px;
            margin: 10px 0 18px;
        }

        .section-filter-bar h4 {
            margin: 0 0 12px 0;
            color: #f7fbff;
            font-size: 1rem;
        }

        .layer-chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 14px;
            margin-bottom: 10px;
        }

        .layer-chip {
            border: 1px solid rgba(133, 210, 229, .18);
            background: rgba(10, 24, 39, .52);
            border-radius: 999px;
            color: #e6f6ff;
            font-size: .75rem;
            padding: 4px 8px;
            display: inline-flex;
            align-items: center;
        }

        .layer-dot {
            width: 9px;
            height: 9px;
            border-radius: 999px;
            display: inline-block;
            margin-right: 7px;
        }

        .source-badge {
            display: inline-block;
            width: max-content;
            margin-top: 20px;
            padding: 9px 13px;
            border: 1px solid rgba(53, 214, 209, .55);
            border-radius: 999px;
            color: var(--cyan);
            background: rgba(0, 0, 0, .68);
            font-size: .85rem;
            font-weight: 700;
        }

        .filter-panel {
            border: 1px solid var(--line);
            background: linear-gradient(180deg, rgba(16, 29, 45, .96), rgba(8, 17, 29, .96));
            border-radius: 8px;
            padding: 6px 16px 4px;
            margin: 14px 0 12px;
            box-shadow: 0 18px 45px rgba(0, 0, 0, .2);
        }

        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div {
            background: #07111d;
            border-color: rgba(160, 204, 221, .26);
            color: #fff;
        }

        div[data-baseweb="select"] > div {
            background: #08111c !important;
            border-color: rgba(95, 129, 168, .34) !important;
            color: #f7fbff !important;
        }

        div[data-baseweb="tag"],
        div[data-baseweb="tag"] > div,
        div[data-baseweb="tag"] > span {
            background: #0f4c8a !important;
            background-color: #0f4c8a !important;
            border-color: rgba(121, 177, 232, .5) !important;
            color: #eef8ff !important;
        }

        div[data-baseweb="tag"] svg,
        div[data-baseweb="tag"] path,
        div[data-baseweb="tag"] span {
            color: #eef8ff !important;
            fill: #eef8ff !important;
        }

        div[data-baseweb="select"] span {
            color: #f7fbff !important;
        }

        [data-testid="stSlider"] {
            color: #fff;
        }

        [data-testid="stSlider"] p {
            display: block !important;
            color: rgba(255, 255, 255, 0.72) !important;
        }

        [data-testid="stSliderTickBarMin"],
        [data-testid="stSliderTickBarMax"] {
            display: none !important;
        }

        div[data-baseweb="slider"] [role="slider"] {
            background: #35d6d1 !important;
            border-color: #35d6d1 !important;
        }

        div[data-baseweb="slider"] > div > div > div {
            background: #35d6d1 !important;
        }

        .slider-fixed-labels {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: -34px;
            color: #ffffff;
            font-size: .92rem;
            font-weight: 600;
            padding: 0 2px;
        }

        .period-filter-tight {
            transform: translateY(0);
            margin-bottom: 0;
        }


        .filter-label {
            color: #f7fbff;
            font-size: 1rem;
            font-weight: 600;
            line-height: 1.2;
            margin-bottom: 8px;
        }

        .filter-button-wrap {
            padding-top: 30px;
        }

        .filter-region-wrap {
            padding-top: 8px;
        }

        .filter-period-wrap {
            padding-top: 8px;
        }

        .metric-row-tight {
            margin-top: -8px;
        }

        .stButton > button {
            border: 1px solid rgba(53, 214, 209, .55);
            background: linear-gradient(135deg, #128f9a, #2f7dd9);
            color: #fff;
            font-weight: 800;
            border-radius: 6px;
            min-height: 42px;
        }

        .stButton > button:hover {
            border-color: #fff;
            color: #fff;
            filter: brightness(1.08);
        }

        .metric-card {
            border: 2px solid rgba(133, 210, 229, .34);
            background: linear-gradient(180deg, rgba(62, 154, 188, .22), rgba(24, 68, 102, .94));
            border-radius: 8px;
            padding: 10px 16px;
            min-height: 92px;
            height: 92px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            box-shadow: 0 14px 28px rgba(5, 18, 31, .2);
        }

        .metric-card span {
            color: var(--muted);
            font-size: .8rem;
            text-transform: uppercase;
            letter-spacing: .08em;
            text-align: center;
        }

        .metric-card strong {
            display: block;
            color: var(--text);
            margin-top: 6px;
            font-size: 1.58rem;
            line-height: 1.1;
            text-align: center;
        }

        .content-panel {
            border: 1px solid var(--line);
            background: rgba(8, 17, 29, .82);
            border-radius: 8px;
            padding: 16px;
        }

        .species-card {
            border: 1px solid var(--line);
            background: linear-gradient(180deg, rgba(32, 74, 108, .96), rgba(14, 35, 56, .98));
            border-radius: 10px;
            overflow: hidden;
            min-height: 384px;
            height: 384px;
            display: flex;
            flex-direction: column;
            box-shadow: 0 16px 34px rgba(2, 12, 22, .22);
            margin-bottom: 12px;
        }

        .species-card img {
            width: 100%;
            height: 146px;
            object-fit: cover;
            display: block;
        }

        .species-card-body {
            padding: 13px 14px 14px;
            display: flex;
            flex-direction: column;
            flex: 1;
            justify-content: flex-start;
        }

        .species-card h3 {
            margin: 0 0 4px;
            font-size: 1rem;
            line-height: 1.22;
            min-height: 2.45em;
        }

        .species-card em {
            color: var(--muted);
            font-size: .84rem;
            line-height: 1.24;
            min-height: 2.1em;
            display: block;
        }

        .chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 7px;
            margin-top: 4px;
            margin-bottom: 10px;
        }

        .chip {
            border: 1px solid rgba(118, 228, 235, .28);
            background: rgba(118, 228, 235, .08);
            border-radius: 999px;
            color: #dffbff;
            padding: 5px 9px;
            font-size: .78rem;
        }

        .small-note {
            color: var(--muted);
            font-size: .83rem;
            margin-top: 0;
            line-height: 1.42;
            display: -webkit-box;
            -webkit-line-clamp: 4;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background: #050a10;
            border: 1px solid rgba(255, 255, 255, .12);
            border-radius: 8px;
            padding: 8px;
        }

        .stTabs [data-baseweb="tab"] {
            background: transparent;
            border-radius: 6px;
            color: #c6d6e5;
            font-weight: 750;
            padding: 10px 16px;
        }

        .stTabs [aria-selected="true"] {
            background: #122339;
            color: #fff;
            border: 1px solid rgba(53, 214, 209, .34);
        }

        [data-testid="stDataFrame"] {
            border: 1px solid var(--line);
            border-radius: 8px;
            overflow: hidden;
        }

        .stAlert {
            background: #101d2d;
            color: #f7fbff;
        }

        .loading-panel {
            border: 1px solid rgba(123, 220, 232, .22);
            background: linear-gradient(180deg, rgba(14, 31, 47, .96), rgba(8, 17, 29, .98));
            border-radius: 10px;
            padding: 18px 20px;
            margin: 14px 0 18px;
            box-shadow: 0 16px 34px rgba(3, 12, 20, .22);
        }

        .loading-panel h4 {
            margin: 0 0 8px 0;
            color: #f7fbff;
            font-size: 1rem;
        }

        .loading-panel p {
            margin: 0;
            color: #cfe4f2;
            font-size: .95rem;
            line-height: 1.45;
        }

        .loading-track {
            margin-top: 14px;
            width: 100%;
            height: 10px;
            border-radius: 999px;
            overflow: hidden;
            background: rgba(120, 176, 206, .12);
            position: relative;
        }

        .loading-bar {
            width: 36%;
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, #1f95b7, #35d6d1, #8ee7e2);
            animation: loading-slide 1.25s ease-in-out infinite;
        }

        @keyframes loading-slide {
            0% { transform: translateX(-120%); }
            100% { transform: translateX(340%); }
        }

        code {
            color: #d6fbff;
        }

        div[data-testid="stMetric"] {
            border: 1px solid var(--line);
            background: rgba(13, 33, 56, .82);
            border-radius: 8px;
            padding: 14px;
        }

        @media (max-width: 760px) {
            .hero {
                min-height: 390px;
                padding: 16px 22px 24px;
            }

            .hero-logo {
                width: min(140px, 34vw);
                margin-bottom: 22px;
            }
        }
        </style>
        """
    st.markdown(
        styles.replace("__HERO_BG__", hero_bg_css).replace("__HERO_LOGO__", hero_logo_css),
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=900, show_spinner=False)
def query_obis(
    scientific_name: str | None,
    region_wkt: str | None,
    depth_min: int,
    depth_max: int,
    start_year: int,
    end_year: int,
    limit: int,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "startdepth": depth_min,
        "enddepth": depth_max,
        "startdate": f"{start_year}-01-01",
        "enddate": f"{end_year}-12-31",
        "size": limit,
    }
    if scientific_name:
        params["scientificname"] = scientific_name
    if region_wkt:
        params["geometry"] = region_wkt

    response = requests.get(f"{API_BASE}/occurrence", params=params, timeout=60)
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=900, show_spinner=False)
def query_species_catalog(
    scientific_name: str | None,
    region_wkt: str | None,
    start_year: int,
    end_year: int,
    limit: int,
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {
        "startdate": f"{start_year}-01-01",
        "enddate": f"{end_year}-12-31",
        "size": limit,
    }
    if scientific_name:
        params["scientificname"] = scientific_name
    if region_wkt:
        params["geometry"] = region_wkt

    response = requests.get(f"{API_BASE}/checklist", params=params, timeout=60)
    response.raise_for_status()
    results = response.json().get("results", [])
    return [item for item in results if str(item.get("taxonRank", "")).lower() == "species"]


def normalize_results(payload: dict[str, Any]) -> pd.DataFrame:
    records = payload.get("results", [])
    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)
    rename_candidates = {
        "decimalLatitude": "decimalLatitude",
        "decimalLongitude": "decimalLongitude",
        "date_year": "date_year",
        "depth": "depth",
        "scientificName": "scientificName",
        "class": "class",
        "phylum": "phylum",
        "order": "order",
        "family": "family",
        "genus": "genus",
        "country": "country",
        "kingdom": "kingdom",
    }
    for column in rename_candidates:
        if column not in df.columns:
            df[column] = None

    df["decimalLatitude"] = pd.to_numeric(df["decimalLatitude"], errors="coerce")
    df["decimalLongitude"] = pd.to_numeric(df["decimalLongitude"], errors="coerce")
    df["date_year"] = pd.to_numeric(df["date_year"], errors="coerce")
    df["depth"] = pd.to_numeric(df["depth"], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def image_to_data_uri(filename: str) -> str:
    path = ASSET_DIR / Path(filename)
    if not path.exists():
        return ""
    mime_type = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def slugify_species_name(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", str(text).strip().lower()).strip("_")
    return cleaned or "species"


def find_cached_species_image(scientific_name: str) -> str | None:
    slug = slugify_species_name(scientific_name)
    matches = sorted(SPECIES_CACHE_DIR.glob(f"{slug}.*"))
    if not matches:
        return None
    return str(Path("species_cache") / matches[0].name).replace("\\", "/")


@st.cache_data(ttl=86400, show_spinner=False)
def lookup_species_image_url(query: str) -> str | None:
    if not query.strip():
        return None

    try:
        inat_response = requests.get(
            "https://api.inaturalist.org/v1/taxa",
            params={"q": query, "per_page": 1},
            headers=HTTP_HEADERS,
            timeout=15,
        )
        inat_response.raise_for_status()
        results = inat_response.json().get("results", [])
        if results:
            photo = results[0].get("default_photo", {}) or {}
            for key in ["large_url", "medium_url", "square_url"]:
                if photo.get(key):
                    return photo[key]
    except requests.RequestException:
        pass

    def page_image_for_title(title: str) -> str | None:
        response = requests.get(
            WIKIPEDIA_API,
            params={
                "action": "query",
                "format": "json",
                "prop": "pageimages",
                "piprop": "thumbnail",
                "pithumbsize": 1200,
                "titles": title,
            },
            headers=HTTP_HEADERS,
            timeout=15,
        )
        response.raise_for_status()
        pages = response.json().get("query", {}).get("pages", {})
        for page in pages.values():
            thumbnail = page.get("thumbnail", {})
            source = thumbnail.get("source")
            if source:
                return source
        return None

    exact = page_image_for_title(query)
    if exact:
        return exact

    search_response = requests.get(
        WIKIPEDIA_API,
        params={
            "action": "query",
            "format": "json",
            "list": "search",
            "srlimit": 1,
            "srsearch": query,
        },
        headers=HTTP_HEADERS,
        timeout=15,
    )
    search_response.raise_for_status()
    search_results = search_response.json().get("query", {}).get("search", [])
    if not search_results:
        return None
    best_title = search_results[0].get("title", "")
    return page_image_for_title(best_title) if best_title else None


def cache_species_image(scientific_name: str, common_name: str, group_name: str) -> str:
    cached = find_cached_species_image(scientific_name)
    if cached:
        return cached

    image_url = None
    for candidate in [scientific_name, common_name]:
        try:
            image_url = lookup_species_image_url(candidate)
        except requests.RequestException:
            image_url = None
        if image_url:
            break

    if not image_url:
        fallback = GROUP_IMAGE_FALLBACKS.get(group_name) or GROUP_IMAGE_FALLBACKS["Otros organismos marinos"]
        return fallback

    try:
        image_response = requests.get(image_url, headers=HTTP_HEADERS, timeout=20)
        image_response.raise_for_status()
    except requests.RequestException:
        fallback = GROUP_IMAGE_FALLBACKS.get(group_name) or GROUP_IMAGE_FALLBACKS["Otros organismos marinos"]
        return fallback

    suffix = Path(urlparse(image_url).path).suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        content_type = image_response.headers.get("Content-Type", "").lower()
        if "png" in content_type:
            suffix = ".png"
        elif "webp" in content_type:
            suffix = ".webp"
        else:
            suffix = ".jpg"

    target = SPECIES_CACHE_DIR / f"{slugify_species_name(scientific_name)}{suffix}"
    try:
        target.write_bytes(image_response.content)
        return str(Path("species_cache") / target.name).replace("\\", "/")
    except OSError:
        fallback = GROUP_IMAGE_FALLBACKS.get(group_name) or GROUP_IMAGE_FALLBACKS["Otros organismos marinos"]
        return fallback


def hydrate_species_images(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hydrated: list[dict[str, Any]] = []
    for item in cards:
        updated = dict(item)
        if not updated.get("image"):
            updated["image"] = cache_species_image(
                scientific_name=updated.get("scientific_name", updated.get("name", "species")),
                common_name=updated.get("name", updated.get("scientific_name", "species")),
                group_name=updated.get("group", "Otros organismos marinos"),
            )
        hydrated.append(updated)
    return hydrated


def prefetch_species_image_catalog(cards: list[dict[str, Any]], limit: int = 120) -> None:
    for item in cards[:limit]:
        if item.get("image"):
            continue
        cache_species_image(
            scientific_name=item.get("scientific_name", item.get("name", "species")),
            common_name=item.get("name", item.get("scientific_name", "species")),
            group_name=item.get("group", "Otros organismos marinos"),
        )


def normalize_group_label(raw_class: Any = None, raw_phylum: Any = None, preferred: Any = None) -> str:
    def clean_text(value: Any) -> str:
        if value is None or pd.isna(value):
            return ""
        return str(value).strip()

    preferred_text = clean_text(preferred)
    if preferred_text:
        normalized_preferred = preferred_text.lower()
        if normalized_preferred in {name.lower() for name in GROUP_COLORS}:
            for group_name in GROUP_COLORS:
                if group_name.lower() == normalized_preferred:
                    return group_name

    group_aliases = {
        "mamiferos marinos": "Mamíferos marinos",
        "mamíferos marinos": "Mamíferos marinos",
        "mammalia": "Mamíferos marinos",
        "pinnipedia": "Mamíferos marinos",
        "peces cartilaginosos": "Peces cartilaginosos",
        "chondrichthyes": "Peces cartilaginosos",
        "elasmobranchii": "Peces cartilaginosos",
        "peces oseos": "Peces óseos",
        "peces óseos": "Peces óseos",
        "actinopterygii": "Peces óseos",
        "teleostei": "Peces óseos",
        "moluscos": "Moluscos",
        "mollusca": "Moluscos",
        "cephalopoda": "Moluscos",
        "bivalvia": "Moluscos",
        "gastropoda": "Moluscos",
        "cnidarios": "Cnidarios",
        "cnidaria": "Cnidarios",
        "anthozoa": "Cnidarios",
        "scyphozoa": "Cnidarios",
        "hydrozoa": "Cnidarios",
        "cubozoa": "Cnidarios",
        "reptiles marinos": "Reptiles marinos",
        "reptilia": "Reptiles marinos",
        "testudines": "Reptiles marinos",
        "equinodermos": "Equinodermos",
        "echinodermata": "Equinodermos",
        "asteroidea": "Equinodermos",
        "echinoidea": "Equinodermos",
        "ophiuroidea": "Equinodermos",
        "holothuroidea": "Equinodermos",
        "artrópodos": "Artrópodos",
        "artropodos": "Artrópodos",
        "arthropoda": "Artrópodos",
        "malacostraca": "Artrópodos",
        "decapoda": "Artrópodos",
        "bacteria": "Bacterias y arqueas",
        "bacteriae": "Bacterias y arqueas",
        "archaea": "Bacterias y arqueas",
        "proteobacteria": "Bacterias y arqueas",
        "alphaproteobacteria": "Bacterias y arqueas",
        "gammaproteobacteria": "Bacterias y arqueas",
        "cyanobacteria": "Bacterias y arqueas",
        "actinobacteria": "Bacterias y arqueas",
        "bacilli": "Bacterias y arqueas",
        "microorganismos eucariotas": "Microorganismos eucariotas",
        "chromista": "Microorganismos eucariotas",
        "myzozoa": "Microorganismos eucariotas",
        "dinophyceae": "Microorganismos eucariotas",
        "bacillariophyta": "Microorganismos eucariotas",
        "ciliophora": "Microorganismos eucariotas",
        "radiolaria": "Microorganismos eucariotas",
        "foraminifera": "Microorganismos eucariotas",
        "protozoa": "Microorganismos eucariotas",
        "plantae": "Plantas y macroalgas",
        "chlorophyta": "Plantas y macroalgas",
        "ochrophyta": "Plantas y macroalgas",
        "rhodophyta": "Plantas y macroalgas",
        "magnoliophyta": "Plantas y macroalgas",
        "fungi": "Hongos marinos",
        "ascomycota": "Hongos marinos",
        "basidiomycota": "Hongos marinos",
        "aves": "Aves marinas",
    }

    for candidate in (preferred_text, raw_class, raw_phylum):
        text = clean_text(candidate).lower()
        if text in group_aliases:
            return group_aliases[text]

    return "Otros organismos marinos"


def normalize_sector_label(raw_kingdom: Any = None, group_name: Any = None) -> str:
    kingdom = str(raw_kingdom).strip().lower() if raw_kingdom is not None and not pd.isna(raw_kingdom) else ""
    group = str(group_name).strip().lower() if group_name is not None and not pd.isna(group_name) else ""

    if kingdom == "animalia" or group in {
        "mamíferos marinos",
        "peces cartilaginosos",
        "peces óseos",
        "moluscos",
        "cnidarios",
        "reptiles marinos",
        "equinodermos",
        "artrópodos",
        "aves marinas",
    }:
        return "Fauna marina"
    if kingdom in {"bacteria", "archaea"} or group == "bacterias y arqueas":
        return "Microorganismos"
    if kingdom in {"chromista", "protista"} or group == "microorganismos eucariotas":
        return "Microorganismos"
    if kingdom == "plantae" or group == "plantas y macroalgas":
        return "Productores marinos"
    if kingdom == "fungi" or group == "hongos marinos":
        return "Hongos y descomponedores"
    return "Otros componentes"


def clean_occurrence_data(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    if df.empty:
        return df, {
            "original": 0,
            "sin_coordenadas": 0,
            "fuera_de_rango": 0,
            "sin_taxonomia": 0,
            "sin_nombre": 0,
            "duplicados": 0,
            "final": 0,
        }

    cleaned = df.copy()
    original_count = len(cleaned)

    for column in ["scientificName", "country", "class", "phylum", "order", "family", "genus"]:
        if column in cleaned.columns:
            cleaned[column] = cleaned[column].astype("string").str.strip()

    no_coords_mask = cleaned["decimalLatitude"].isna() | cleaned["decimalLongitude"].isna()
    no_coords = int(no_coords_mask.sum())
    cleaned = cleaned.loc[~no_coords_mask].copy()

    range_mask = (
        cleaned["decimalLatitude"].between(-90, 90, inclusive="both")
        & cleaned["decimalLongitude"].between(-180, 180, inclusive="both")
    )
    out_of_range = int((~range_mask).sum())
    cleaned = cleaned.loc[range_mask].copy()

    current_year = date.today().year
    if "date_year" in cleaned.columns:
        cleaned.loc[~cleaned["date_year"].between(1800, current_year, inclusive="both"), "date_year"] = pd.NA

    if "depth" in cleaned.columns:
        cleaned.loc[~cleaned["depth"].between(0, 11000, inclusive="both"), "depth"] = pd.NA

    if "kingdom" in cleaned.columns:
        cleaned["kingdom"] = cleaned["kingdom"].astype("string").str.strip()

    if "scientificName" in cleaned.columns:
        missing_name_mask = cleaned["scientificName"].isna() | (cleaned["scientificName"] == "")
        missing_name = int(missing_name_mask.sum())
        cleaned = cleaned.loc[~missing_name_mask].copy()
    else:
        missing_name = 0

    taxon_source = None
    if "class" in cleaned.columns and "phylum" in cleaned.columns:
        cleaned["taxon_group"] = cleaned["class"].fillna(cleaned["phylum"])
        taxon_source = "taxon_group"
    elif "class" in cleaned.columns:
        cleaned["taxon_group"] = cleaned["class"]
        taxon_source = "taxon_group"
    elif "phylum" in cleaned.columns:
        cleaned["taxon_group"] = cleaned["phylum"]
        taxon_source = "taxon_group"

    if taxon_source:
        missing_taxon_mask = cleaned[taxon_source].isna() | (cleaned[taxon_source].astype("string").str.strip() == "")
        missing_taxonomy = int(missing_taxon_mask.sum())
        cleaned = cleaned.loc[~missing_taxon_mask].copy()
        cleaned["taxon_group"] = cleaned.apply(
            lambda row: normalize_group_label(row.get("class"), row.get("phylum"), row.get("taxon_group")),
            axis=1,
        )
        cleaned["sector"] = cleaned.apply(
            lambda row: normalize_sector_label(row.get("kingdom"), row.get("taxon_group")),
            axis=1,
        )
    else:
        missing_taxonomy = 0

    if "country" in cleaned.columns:
        cleaned["country"] = cleaned["country"].astype("string").str.strip()
        cleaned.loc[cleaned["country"] == "", "country"] = pd.NA

    dedupe_cols = [col for col in ["scientificName", "decimalLatitude", "decimalLongitude", "date_year", "depth"] if col in cleaned.columns]
    before_dedup = len(cleaned)
    cleaned = cleaned.drop_duplicates(subset=dedupe_cols).copy()
    duplicates = before_dedup - len(cleaned)

    summary = {
        "original": original_count,
        "sin_coordenadas": no_coords,
        "fuera_de_rango": out_of_range,
        "sin_taxonomia": missing_taxonomy,
        "sin_nombre": missing_name,
        "duplicados": duplicates,
        "final": len(cleaned),
    }
    return cleaned, summary


def metric_card(label: str, value: str, details: str | None = None) -> None:
    details_html = f"<div style='margin-top:10px; color:#d4e6f3; font-size:.78rem; line-height:1.25; text-align:center; white-space:nowrap;'>{details}</div>" if details else ""
    st.markdown(
        f"""
        <div class="metric-card">
            <span>{label}</span>
            <strong>{value}</strong>
            {details_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_compact_number(value: int | float) -> str:
    absolute = abs(float(value))
    sign = "-" if float(value) < 0 else ""

    def truncate_one_decimal(number: float) -> float:
        return floor(number * 10) / 10

    if absolute >= 1_000_000_000:
        short = truncate_one_decimal(absolute / 1_000_000_000)
        return f"{sign}{short:.1f} B"
    if absolute >= 1_000_000:
        short = truncate_one_decimal(absolute / 1_000_000)
        return f"{sign}{short:.1f} M"
    if absolute >= 1_000:
        short = truncate_one_decimal(absolute / 1_000)
        return f"{sign}{short:.1f} K"
    return f"{int(value)}"


def species_card(name: str, info: dict[str, Any], records: int, avg_depth: float | None) -> None:
    group_name = info.get("group", "Otros organismos marinos")
    sector_name = info.get("sector", "Otros componentes")
    image_name = info.get("image") or GROUP_IMAGE_FALLBACKS.get(group_name) or GROUP_IMAGE_FALLBACKS["Otros organismos marinos"]
    image_src = image_to_data_uri(image_name) if image_name else ""
    scientific_label = info.get("scientific_name") or "Especie marina"
    media_html = (
        f'<img src="{image_src}" alt="{name}">' if image_src else
        f'<div style="height:145px; display:flex; flex-direction:column; justify-content:end; padding:16px; background:linear-gradient(135deg,#0e355a,#1aa6b7); color:#fff;"><div style="font-size:.82rem; opacity:.86;">Especie detectada</div><div style="font-weight:800; font-size:1rem; line-height:1.2; margin-top:6px;">{scientific_label}</div></div>'
    )
    st.markdown(
        f"""
        <div class="species-card">
            {media_html}
            <div class="species-card-body">
                <h3>{name}</h3>
                <em>{scientific_label}</em>
                <div class="chip-row">
                    <span class="chip">{sector_name}</span>
                    <span class="chip">{group_name}</span>
                    <span class="chip">{records:,} registros</span>
                </div>
                <p class="small-note">{info.get('note', 'Especie detectada dentro de la consulta filtrada en OBIS.')}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def style_plotly(fig, height: int = 390):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#07111d",
        font={"color": "#f7fbff", "family": "Arial"},
        margin={"l": 10, "r": 10, "t": 42, "b": 10},
        height=height,
        hoverlabel={
            "bgcolor": "#07111d",
            "font_color": "#f7fbff",
            "bordercolor": "#35d6d1",
        },
    )
    fig.update_xaxes(gridcolor="rgba(160,204,221,.16)", zerolinecolor="rgba(160,204,221,.18)")
    fig.update_yaxes(gridcolor="rgba(160,204,221,.16)", zerolinecolor="rgba(160,204,221,.18)")
    return fig


def rgba_to_css(color: list[int]) -> str:
    r, g, b, a = color
    return f"rgba({r},{g},{b},{a / 255:.3f})"


def get_group_color(group_name: str) -> list[int]:
    return GROUP_COLORS.get(group_name, GROUP_COLORS["Otros organismos marinos"])


def get_group_color_map() -> dict[str, str]:
    return {group_name: rgba_to_css(color) for group_name, color in GROUP_COLORS.items()}


def render_group_chart(df: pd.DataFrame) -> None:
    group_col = "taxon_group" if "taxon_group" in df.columns and df["taxon_group"].notna().any() else None
    if group_col not in df.columns or not df[group_col].notna().any():
        st.info("Los registros consultados no incluyen grupo taxonómico suficiente.")
        return

    counts = (
        df[group_col]
        .dropna()
        .loc[lambda s: s.astype("string").str.strip() != ""]
        .value_counts()
        .head(10)
        .rename_axis("grupo")
        .reset_index(name="registros")
    )
    counts = counts.sort_values("registros", ascending=False).reset_index(drop=True)
    counts["porcentaje"] = counts["registros"] / counts["registros"].sum()
    marine_scale = [
        "#0b4f6c",
        "#11698b",
        "#177fa2",
        "#1f95b7",
        "#29abcb",
        "#41bed7",
        "#63cedf",
        "#88dde8",
        "#aeeaf0",
        "#c8f4f7",
    ]
    color_map = {
        row["grupo"]: marine_scale[min(index, len(marine_scale) - 1)]
        for index, row in counts.iterrows()
    }
    text_positions = [
        "inside" if percentage >= 0.08 else "outside"
        for percentage in counts["porcentaje"].tolist()
    ]
    pull_values = [
        0.0 if percentage >= 0.08 else 0.06
        for percentage in counts["porcentaje"].tolist()
    ]

    fig = px.pie(
        counts,
        values="registros",
        names="grupo",
        hole=0.58,
        color="grupo",
        color_discrete_map=color_map,
        title="Composición por grupo taxonómico",
    )
    fig.update_traces(
        textposition=text_positions,
        textinfo="percent",
        texttemplate="<b>%{percent:.0%}</b>",
        textfont={"color": "#ffffff", "size": 18, "family": "Arial Black"},
        insidetextfont={"color": "#ffffff", "size": 18, "family": "Arial Black"},
        outsidetextfont={"color": "#ffffff", "size": 16, "family": "Arial Black"},
        hovertemplate="<b>%{label}</b><br>Registros: %{value:,}<br>Participación: %{percent}<extra></extra>",
        marker={"line": {"color": "#07111d", "width": 2}},
        automargin=True,
        pull=pull_values,
    )
    fig.update_layout(
        showlegend=False,
        uniformtext_minsize=15,
        uniformtext_mode="hide",
    )
    fig = style_plotly(fig, height=470)
    fig.update_layout(margin={"l": 10, "r": 10, "t": 42, "b": 20})
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

    legend_items: list[str] = []
    for _, row in counts.iterrows():
        legend_items.append(
            "<div style='display:flex;align-items:center;gap:10px;padding:6px 8px;'>"
            f"<span style='display:inline-block;width:12px;height:12px;background:{color_map[row['grupo']]};border-radius:2px;'></span>"
            f"<span style='color:#f7fbff;font-size:.98rem;'>{row['grupo']}</span>"
            "</div>"
        )
    st.markdown(
        "<div style='display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:2px 18px;margin-top:6px;'>"
        + "".join(legend_items)
        + "</div>",
        unsafe_allow_html=True,
    )


def render_group_period_heatmap(df: pd.DataFrame) -> None:
    required_cols = {"taxon_group", "date_year"}
    if df.empty or not required_cols.issubset(df.columns):
        st.info("No hay datos suficientes para comparar grupos a lo largo del tiempo.")
        return

    chart_df = df.dropna(subset=["taxon_group", "date_year"]).copy()
    if chart_df.empty:
        st.info("No hay datos suficientes para comparar grupos a lo largo del tiempo.")
        return

    chart_df["date_year"] = chart_df["date_year"].astype(int)
    min_year = int(chart_df["date_year"].min())
    chart_df["periodo"] = ((chart_df["date_year"] - min_year) // 5) * 5 + min_year
    chart_df["periodo"] = chart_df["periodo"].apply(lambda year: f"{year}-{year + 4}")
    chart_df = (
        chart_df.groupby(["taxon_group", "periodo"], as_index=False)
        .size()
        .rename(columns={"size": "registros"})
    )
    if chart_df.empty:
        st.info("No hay datos suficientes para comparar grupos a lo largo del tiempo.")
        return

    fig = px.density_heatmap(
        chart_df,
        x="periodo",
        y="taxon_group",
        z="registros",
        histfunc="sum",
        color_continuous_scale=["#0d2138", "#2f7dd9", "#35d6d1", "#ffb54d"],
        title="Intensidad temporal por grupo",
        labels={"periodo": "Período", "taxon_group": "Grupo", "registros": "Registros"},
    )
    fig.update_xaxes(type="category")
    fig.update_yaxes(categoryorder="total ascending")
    st.plotly_chart(style_plotly(fig, height=500), use_container_width=True, config=PLOTLY_CONFIG)


def render_sector_treemap(df: pd.DataFrame) -> None:
    if df.empty or "sector" not in df.columns:
        st.info("No hay datos suficientes para resumir sectores biológicos.")
        return

    chart_df = (
        df.dropna(subset=["sector"])
        .groupby("sector", as_index=False)
        .size()
        .rename(columns={"size": "registros"})
        .sort_values("registros", ascending=True)
    )
    if chart_df.empty:
        st.info("No hay datos suficientes para resumir sectores biológicos.")
        return

    chart_df = chart_df.sort_values("registros", ascending=False).reset_index(drop=True)
    marine_scale = ["#0b4f6c", "#11698b", "#1f95b7", "#41bed7", "#88dde8", "#c8f4f7"]
    color_map = {
        row["sector"]: marine_scale[min(index, len(marine_scale) - 1)]
        for index, row in chart_df.iterrows()
    }
    fig = px.treemap(
        chart_df,
        path=["sector"],
        values="registros",
        color="sector",
        color_discrete_map=color_map,
        title="Sectores biológicos de la muestra",
    )
    fig.update_traces(
        texttemplate="<b>%{label}</b><br>%{percentRoot:.0%}",
        marker={"line": {"color": "#07111d", "width": 2}},
        hovertemplate="<b>%{label}</b><br>Participación: %{percentRoot:.1%}<br>Registros: %{value:,}<extra></extra>",
    )
    fig.update_layout(showlegend=False, coloraxis_showscale=False)
    fig = style_plotly(fig, height=350)
    fig.update_layout(
        margin={"l": 12, "r": 12, "t": 46, "b": 10},
        uniformtext_minsize=13,
        uniformtext_mode="hide",
    )
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)


def render_country_bar(df: pd.DataFrame) -> None:
    if df.empty or "country" not in df.columns:
        st.info("No hay datos suficientes para comparar países.")
        return

    chart_df = (
        df.dropna(subset=["country"])
        .groupby("country", as_index=False)
        .size()
        .rename(columns={"size": "registros"})
        .sort_values("registros", ascending=False)
        .head(10)
        .sort_values("registros", ascending=True)
    )
    if chart_df.empty:
        st.info("No hay datos suficientes para comparar países.")
        return

    fig = px.bar(
        chart_df,
        x="registros",
        y="country",
        orientation="h",
        text="registros",
        color="registros",
        color_continuous_scale=["#10263a", "#2f7dd9", "#35d6d1"],
        title="Países con más registros",
        labels={"registros": "Registros", "country": ""},
    )
    fig.update_traces(textposition="outside", marker_line_width=0)
    fig.update_layout(coloraxis_showscale=False)
    st.plotly_chart(style_plotly(fig, height=400), use_container_width=True, config=PLOTLY_CONFIG)


def render_group_bar(df: pd.DataFrame) -> None:
    if df.empty or "taxon_group" not in df.columns:
        st.info("No hay datos suficientes para comparar subgrupos.")
        return

    chart_df = (
        df.dropna(subset=["taxon_group"])
        .groupby("taxon_group", as_index=False)
        .size()
        .rename(columns={"size": "registros"})
        .sort_values("registros", ascending=False)
        .head(10)
        .sort_values("registros", ascending=True)
    )
    if chart_df.empty:
        st.info("No hay datos suficientes para comparar subgrupos.")
        return

    color_map = {row["taxon_group"]: rgba_to_css(get_group_color(row["taxon_group"])) for _, row in chart_df.iterrows()}
    fig = px.bar(
        chart_df,
        x="registros",
        y="taxon_group",
        orientation="h",
        text="registros",
        color="taxon_group",
        color_discrete_map=color_map,
        title="Subgrupos con más presencia",
        labels={"registros": "Registros", "taxon_group": ""},
    )
    fig.update_traces(textposition="outside", marker_line_width=0)
    fig.update_layout(showlegend=False)
    st.plotly_chart(style_plotly(fig, height=430), use_container_width=True, config=PLOTLY_CONFIG)


def render_group_lollipop(df: pd.DataFrame) -> None:
    if df.empty or "taxon_group" not in df.columns:
        st.info("No hay datos suficientes para comparar subgrupos.")
        return

    chart_df = (
        df.dropna(subset=["taxon_group"])
        .groupby("taxon_group", as_index=False)
        .size()
        .rename(columns={"size": "registros"})
        .sort_values("registros", ascending=False)
        .head(10)
        .sort_values("registros", ascending=True)
        .reset_index(drop=True)
    )
    if chart_df.empty:
        st.info("No hay datos suficientes para comparar subgrupos.")
        return

    fig = go.Figure()
    for _, row in chart_df.iterrows():
        color = rgba_to_css(get_group_color(row["taxon_group"]))
        fig.add_trace(
            go.Scatter(
                x=[0, row["registros"]],
                y=[row["taxon_group"], row["taxon_group"]],
                mode="lines",
                line={"color": color, "width": 3},
                hoverinfo="skip",
                showlegend=False,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[row["registros"]],
                y=[row["taxon_group"]],
                mode="markers+text",
                marker={"color": color, "size": 14, "line": {"color": "#eaf8ff", "width": 1}},
                text=[f"{int(row['registros']):,}"],
                textposition="middle right",
                hovertemplate=f"<b>{row['taxon_group']}</b><br>Registros: {int(row['registros']):,}<extra></extra>",
                showlegend=False,
            )
        )

    fig.update_layout(
        title="Subgrupos con más presencia",
        xaxis_title="Registros",
        yaxis_title="",
    )
    st.plotly_chart(style_plotly(fig, height=430), use_container_width=True, config=PLOTLY_CONFIG)


def render_group_treemap(df: pd.DataFrame) -> None:
    if df.empty or "taxon_group" not in df.columns:
        st.info("No hay datos suficientes para comparar subgrupos.")
        return

    chart_df = (
        df.dropna(subset=["taxon_group"])
        .groupby("taxon_group", as_index=False)
        .size()
        .rename(columns={"size": "registros"})
        .sort_values("registros", ascending=False)
        .head(14)
    )
    if chart_df.empty:
        st.info("No hay datos suficientes para comparar subgrupos.")
        return

    fig = px.treemap(
        chart_df,
        path=["taxon_group"],
        values="registros",
        color="registros",
        color_continuous_scale=["#0b4f6c", "#1f95b7", "#63cedf", "#c8f4f7"],
        title="Subgrupos con más presencia",
    )
    fig.update_traces(
        texttemplate="<b>%{label}</b><br>%{value:,} registros",
        marker={"line": {"color": "#07111d", "width": 2}},
        hovertemplate="<b>%{label}</b><br>Registros: %{value:,}<extra></extra>",
    )
    fig.update_layout(coloraxis_showscale=False)
    st.plotly_chart(style_plotly(fig, height=430), use_container_width=True, config=PLOTLY_CONFIG)


def render_country_scatter(df: pd.DataFrame) -> None:
    if "country" not in df.columns or "scientificName" not in df.columns or df.empty:
        st.info("No hay datos suficientes para comparar territorios.")
        return

    chart_df = (
        df.dropna(subset=["country", "scientificName"])
        .groupby("country", as_index=False)
        .agg(
            registros=("scientificName", "size"),
            especies=("scientificName", "nunique"),
            profundidad_media=("depth", "mean"),
        )
        .sort_values("registros", ascending=False)
        .head(18)
    )
    if chart_df.empty:
        st.info("No hay datos suficientes para comparar territorios.")
        return

    chart_df["profundidad_media"] = chart_df["profundidad_media"].fillna(0)
    chart_df["indice_abundancia"] = (chart_df["registros"] / chart_df["registros"].max()) * 100
    chart_df["indice_riqueza"] = (chart_df["especies"] / chart_df["especies"].max()) * 100
    chart_df["score_visual"] = (chart_df["indice_abundancia"] * 0.55) + (chart_df["indice_riqueza"] * 0.45)
    chart_df["etiqueta"] = chart_df["country"].where(chart_df["score_visual"].rank(method="first", ascending=False) <= 8, "")
    median_abundancia = float(chart_df["indice_abundancia"].median())
    median_riqueza = float(chart_df["indice_riqueza"].median())

    fig = px.scatter(
        chart_df,
        x="indice_abundancia",
        y="indice_riqueza",
        size="registros",
        color="score_visual",
        text="etiqueta",
        hover_name="country",
        color_continuous_scale=["#0b4f6c", "#1f95b7", "#63cedf", "#c8f4f7"],
        title="Países: abundancia frente a riqueza de especies",
        labels={
            "indice_abundancia": "Abundancia relativa",
            "indice_riqueza": "Riqueza relativa",
            "score_visual": "Equilibrio",
        },
        size_max=34,
    )
    fig.update_traces(
        marker={"opacity": 0.86, "line": {"width": 1.2, "color": "rgba(234,248,255,.26)"}},
        customdata=chart_df[["registros", "especies", "indice_abundancia", "indice_riqueza"]],
        textposition="top center",
        textfont={"size": 11, "color": "#e9fcff"},
        hovertemplate="<b>%{hovertext}</b><br>Registros: %{customdata[0]:,}<br>Especies: %{customdata[1]:,}<br>Abundancia relativa: %{customdata[2]:.0f}<br>Riqueza relativa: %{customdata[3]:.0f}<extra></extra>",
    )
    fig.update_layout(coloraxis_showscale=False)
    fig.add_vline(
        x=median_abundancia,
        line_width=1.3,
        line_dash="dash",
        line_color="rgba(165, 227, 236, .45)",
    )
    fig.add_hline(
        y=median_riqueza,
        line_width=1.3,
        line_dash="dash",
        line_color="rgba(165, 227, 236, .45)",
    )
    fig.add_annotation(
        x=98,
        y=5,
        xanchor="right",
        yanchor="bottom",
        text="Mayor abundancia",
        showarrow=False,
        font={"size": 11, "color": "#bff7fb"},
        bgcolor="rgba(7,17,29,.58)",
    )
    fig.add_annotation(
        x=3,
        y=98,
        xanchor="left",
        yanchor="top",
        text="Mayor riqueza",
        showarrow=False,
        font={"size": 11, "color": "#bff7fb"},
        bgcolor="rgba(7,17,29,.58)",
    )
    fig.update_xaxes(
        title="Abundancia relativa (%)",
        range=[0, 102],
        tickmode="array",
        tickvals=[0, 25, 50, 75, 100],
        ticksuffix="%",
        gridcolor="rgba(185, 239, 244, .08)",
    )
    fig.update_yaxes(
        title="Riqueza relativa (%)",
        range=[0, 102],
        tickmode="array",
        tickvals=[0, 25, 50, 75, 100],
        ticksuffix="%",
        gridcolor="rgba(185, 239, 244, .08)",
    )
    fig = style_plotly(fig, height=660)
    fig.update_layout(margin={"l": 16, "r": 16, "t": 58, "b": 28})
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)


def render_temporal_chart(df: pd.DataFrame) -> None:
    if "date_year" not in df.columns or not df["date_year"].notna().any():
        st.info("No hay años suficientes para graficar la tendencia.")
        return

    trend = df.dropna(subset=["date_year"]).assign(date_year=lambda x: x["date_year"].astype(int))
    trend_counts = trend.groupby("date_year").size().reset_index(name="registros")
    year_values = trend_counts["date_year"].tolist()
    record_values = trend_counts["registros"].tolist()

    if len(year_values) >= 2:
        mean_x = sum(year_values) / len(year_values)
        mean_y = sum(record_values) / len(record_values)
        denominator = sum((x - mean_x) ** 2 for x in year_values)
        slope = 0 if denominator == 0 else sum((x - mean_x) * (y - mean_y) for x, y in zip(year_values, record_values)) / denominator
        intercept = mean_y - slope * mean_x
        last_year = max(year_values)
        projection_years = list(range(last_year + 1, last_year + 4))
        projection_values = [max(0, intercept + slope * year) for year in projection_years]
    else:
        projection_years = []
        projection_values = []

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=trend_counts["date_year"],
            y=trend_counts["registros"],
            mode="lines+markers",
            name="Observaciones",
            line={"color": "#35d6d1", "width": 3},
            marker={"size": 7, "color": "#8ee7e2"},
            fill="tozeroy",
            fillcolor="rgba(53, 214, 209, .18)",
            hovertemplate="<b>%{x}</b><br>Registros: %{y:,}<extra></extra>",
        )
    )
    if projection_years:
        fig.add_trace(
            go.Scatter(
                x=[year_values[-1], *projection_years],
                y=[record_values[-1], *projection_values],
                mode="lines+markers",
                name="Proyección",
                line={"color": "#ffb54d", "width": 2.5, "dash": "dash"},
                marker={"size": 6, "color": "#ffd089"},
                hovertemplate="<b>%{x}</b><br>Proyección: %{y:,.0f}<extra></extra>",
            )
        )

    fig.update_layout(
        title="Tendencia de observaciones por período",
        showlegend=False,
    )
    fig = style_plotly(fig, height=500)
    fig.update_layout(margin={"l": 10, "r": 10, "t": 78, "b": 34})
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
    temporal_legend = """
    <div style='display:flex;justify-content:center;gap:28px;align-items:center;margin-top:10px;'>
        <div style='display:flex;align-items:center;gap:8px;color:#f7fbff;font-size:.96rem;'>
            <span style='display:inline-block;width:40px;height:0;border-top:4px solid #35d6d1;position:relative;'></span>
            <span>Observaciones</span>
        </div>
        <div style='display:flex;align-items:center;gap:8px;color:#f7fbff;font-size:.96rem;'>
            <span style='display:inline-block;width:40px;height:0;border-top:4px dashed #ffb54d;position:relative;'></span>
            <span>Proyección</span>
        </div>
    </div>
    """
    st.markdown(temporal_legend, unsafe_allow_html=True)


def render_top_species_chart(cards: list[dict[str, Any]]) -> None:
    if not cards:
        st.info("No hay especies suficientes para resumir en gráfico.")
        return

    species_df = pd.DataFrame(cards[:10])[["name", "records", "group"]].sort_values("records", ascending=True).reset_index(drop=True)
    species_df["short_name"] = species_df["name"].apply(lambda value: value if len(value) <= 28 else value[:27] + "…")
    fig = go.Figure()
    for _, row in species_df.iterrows():
        color = rgba_to_css(get_group_color(row["group"]))
        fig.add_trace(
            go.Scatter(
                x=[0, row["records"]],
                y=[row["short_name"], row["short_name"]],
                mode="lines",
                line={"color": color, "width": 3},
                hoverinfo="skip",
                showlegend=False,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[row["records"]],
                y=[row["short_name"]],
                mode="markers+text",
                marker={"color": color, "size": 15, "line": {"color": "#eaf8ff", "width": 1}},
                text=[f"{int(row['records']):,}"],
                textposition="middle right",
                hovertemplate=f"<b>{row['name']}</b><br>Grupo: {row['group']}<br>Registros: {int(row['records']):,}<extra></extra>",
                showlegend=False,
            )
        )

    fig.update_layout(
        title="Especies con más registros",
        xaxis_title="Registros",
        yaxis_title="",
    )
    fig = style_plotly(fig, height=290)
    fig.update_layout(margin={"l": 18, "r": 28, "t": 46, "b": 18})
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)


def render_depth_violin(df: pd.DataFrame) -> None:
    required_cols = {"taxon_group", "depth"}
    if df.empty or not required_cols.issubset(df.columns):
        st.info("No hay profundidad suficiente para comparar grupos.")
        return

    chart_df = (
        df.dropna(subset=["taxon_group", "depth"])
        .groupby("taxon_group", group_keys=False)
        .head(180)
        .copy()
    )
    if chart_df.empty:
        st.info("No hay profundidad suficiente para comparar grupos.")
        return

    fig = px.violin(
        chart_df,
        x="taxon_group",
        y="depth",
        color="taxon_group",
        box=True,
        points=False,
        color_discrete_map=get_group_color_map(),
        title="Rango de profundidad por grupo",
        labels={"taxon_group": "Grupo", "depth": "Profundidad (m)"},
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(style_plotly(fig, height=470), use_container_width=True, config=PLOTLY_CONFIG)


def render_group_diversity_heatmap(df: pd.DataFrame) -> None:
    required_cols = {"taxon_group", "scientificName"}
    if df.empty or not required_cols.issubset(df.columns):
        st.info("No hay datos suficientes para comparar diversidad por grupo.")
        return

    chart_df = (
        df.dropna(subset=["taxon_group", "scientificName"])
        .groupby("taxon_group", as_index=False)
        .agg(
            registros=("scientificName", "size"),
            especies=("scientificName", "nunique"),
            profundidad_media=("depth", "mean"),
        )
        .sort_values("especies", ascending=False)
    )
    if chart_df.empty:
        st.info("No hay datos suficientes para comparar diversidad por grupo.")
        return

    chart_df["profundidad_media"] = chart_df["profundidad_media"].fillna(0)
    chart_df["registros_por_especie"] = chart_df["registros"] / chart_df["especies"]
    chart_df = chart_df.sort_values("especies", ascending=True)

    marine_scale = [
        "#0b4f6c",
        "#11698b",
        "#177fa2",
        "#1f95b7",
        "#29abcb",
        "#41bed7",
        "#63cedf",
        "#88dde8",
    ]
    color_sequence = [marine_scale[min(index, len(marine_scale) - 1)] for index in range(len(chart_df))]

    fig = px.bar(
        chart_df,
        x="especies",
        y="taxon_group",
        orientation="h",
        text="especies",
        title="Riqueza de especies por grupo",
        labels={"especies": "Especies únicas", "taxon_group": "Grupo"},
        color="especies",
        color_continuous_scale=marine_scale,
        custom_data=["registros", "registros_por_especie", "profundidad_media"],
    )
    fig.update_traces(
        texttemplate="<b>%{text:,}</b>",
        textposition="outside",
        marker={"line": {"width": 0}},
        hovertemplate="<b>%{y}</b><br>Especies únicas: %{x:,}<br>Registros: %{customdata[0]:,}<br>Registros por especie: %{customdata[1]:.1f}<br>Prof. media: %{customdata[2]:,.0f} m<extra></extra>",
    )
    fig.update_layout(
        coloraxis_showscale=False,
        margin={"l": 10, "r": 10, "t": 42, "b": 20},
    )
    fig = style_plotly(fig, height=420)
    fig.update_xaxes(title="Especies únicas")
    fig.update_yaxes(title="")
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)


def get_treemap_source(df: pd.DataFrame, analysis_area: str) -> tuple[pd.DataFrame, str, str]:
    working = df.copy()
    if working.empty:
        return pd.DataFrame(), "", "Análisis interactivo"

    if analysis_area == "Taxonomía":
        column = "taxon_group"
        title = "Composición por grupo taxonómico"
    elif analysis_area == "Geografía":
        column = "country"
        title = "Distribución por país o zona reportada"
    elif analysis_area == "Período":
        column = "date_year"
        title = "Ingreso de registros por periodo"
        working[column] = pd.to_numeric(working[column], errors="coerce").dropna()
        working[column] = working[column].astype("Int64").astype(str)
    else:
        column = "depth_zone"
        title = "Distribución por rango de profundidad"
        depth = pd.to_numeric(working["depth"], errors="coerce")
        working[column] = pd.cut(
            depth,
            bins=[-1, 50, 200, 1000, 4000, 11000],
            labels=["0-50 m", "51-200 m", "201-1,000 m", "1,001-4,000 m", "4,001-11,000 m"],
        ).astype(str)

    if column not in working.columns:
        return pd.DataFrame(), column, title

    counts = (
        working[column]
        .dropna()
        .loc[lambda s: s.astype("string").str.strip() != ""]
        .value_counts()
        .head(18)
        .rename_axis("categoria")
        .reset_index(name="registros")
    )
    return counts, column, title


def render_treemap(df: pd.DataFrame, analysis_area: str) -> None:
    counts, _, title = get_treemap_source(df, analysis_area)
    if counts.empty:
        st.info("No hay datos suficientes para construir el treemap con este filtro.")
        return

    fig = px.treemap(
        counts,
        path=["categoria"],
        values="registros",
        color="registros",
        color_continuous_scale=["#bdece0", "#57c8c5", "#2f7dd9"],
        title=title,
    )
    fig.update_traces(
        texttemplate="<b>%{label}</b><br>%{value} registros",
        marker={"line": {"color": "#07111d", "width": 2}},
        hovertemplate="<b>%{label}</b><br>Registros: %{value}<extra></extra>",
    )
    fig.update_layout(coloraxis_colorbar={"title": "Recuento"})
    st.plotly_chart(style_plotly(fig, height=520), use_container_width=True, config=PLOTLY_CONFIG)


def build_summary_lines(df: pd.DataFrame, total: int, selected_common: str, region_name: str) -> list[str]:
    if df.empty:
        return [
            "No hay registros suficientes para resumir la consulta actual.",
        ]

    lines: list[str] = []
    lines.append(f"Consulta actual: {selected_common} en {region_name.lower()} con {len(df):,} registros limpios visibles de {int(total):,} reportados por la API.")

    if "taxon_group" in df.columns and df["taxon_group"].notna().any():
        top_group = df["taxon_group"].value_counts().head(1)
        if not top_group.empty:
            lines.append(f"Grupo dominante: {top_group.index[0]} con {int(top_group.iloc[0]):,} registros dentro de la muestra.")

    if "country" in df.columns and df["country"].notna().any():
        top_country = df["country"].dropna().value_counts().head(1)
        if not top_country.empty:
            lines.append(f"Zona más representada: {top_country.index[0]} con {int(top_country.iloc[0]):,} registros.")

    if "date_year" in df.columns and df["date_year"].notna().any():
        years = df["date_year"].dropna().astype(int)
        lines.append(f"Cobertura temporal visible: {years.min()} a {years.max()}.")

    return lines


def build_species_cards(df: pd.DataFrame, max_cards: int = 9) -> list[dict[str, Any]]:
    if df.empty or "scientificName" not in df.columns:
        return []

    grouped = (
        df.dropna(subset=["scientificName"])
        .groupby("scientificName", dropna=True)
        .agg(
            registros=("scientificName", "size"),
            profundidad_promedio=("depth", "mean"),
            grupo=("taxon_group", lambda s: s.dropna().iloc[0] if not s.dropna().empty else "Otros organismos marinos"),
            sector=("sector", lambda s: s.dropna().iloc[0] if not s.dropna().empty else "Otros componentes"),
            pais=("country", lambda s: s.dropna().iloc[0] if not s.dropna().empty else ""),
        )
        .reset_index()
        .sort_values(["registros", "scientificName"], ascending=[False, True])
        .head(max_cards)
    )

    cards: list[dict[str, Any]] = []
    for row in grouped.to_dict("records"):
        scientific_name = row["scientificName"]
        known = KNOWN_SPECIES_BY_SCIENTIFIC.get(scientific_name, {})
        cards.append(
            {
                "name": known.get("common_name", scientific_name),
                "scientific_name": scientific_name,
                "group": known.get("group", normalize_group_label(row.get("grupo"))),
                "sector": row.get("sector", "Otros componentes"),
                "image": known.get("image"),
                "note": known.get(
                    "note",
                    f"Registrada en {row.get('pais') or 'diversas regiones'} dentro de la consulta actual."
                ),
                "records": int(row["registros"]),
                "avg_depth": row.get("profundidad_promedio"),
            }
        )
    return cards


def build_species_cards_from_catalog(catalog: list[dict[str, Any]], max_cards: int = 1000) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for item in catalog[:max_cards]:
        scientific_name = item.get("scientificName")
        if not scientific_name:
            continue
        known = KNOWN_SPECIES_BY_SCIENTIFIC.get(scientific_name, {})
        cards.append(
            {
                "name": known.get("common_name", scientific_name),
                "scientific_name": scientific_name,
                "group": known.get("group", normalize_group_label(item.get("class"), item.get("phylum"))),
                "image": known.get("image"),
                "note": known.get(
                    "note",
                    f"Especie listada por OBIS con {int(item.get('records', 0)):,} registros para la consulta actual."
                ),
                "records": int(item.get("records", 0)),
                "avg_depth": None,
            }
        )
    return cards


def filter_species_cards(
    cards: list[dict[str, Any]],
    search_text: str,
    selected_sector: str,
    selected_group: str,
    sort_mode: str,
) -> list[dict[str, Any]]:
    filtered = cards

    if search_text.strip():
        needle = search_text.strip().lower()
        filtered = [
            item for item in filtered
            if needle in item["name"].lower() or needle in item["scientific_name"].lower()
        ]

    if selected_sector != "Todos":
        filtered = [item for item in filtered if item.get("sector") == selected_sector]

    if selected_group != "Todos":
        filtered = [item for item in filtered if item.get("group") == selected_group]

    if sort_mode == "Más registros":
        filtered = sorted(filtered, key=lambda item: item["records"], reverse=True)
    elif sort_mode == "A-Z":
        filtered = sorted(filtered, key=lambda item: item["name"].lower())
    return filtered


def render_map(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("No hay coordenadas para mostrar con los filtros actuales.")
        return

    map_df = df.copy()
    if "taxon_group" not in map_df.columns:
        map_df["taxon_group"] = "Otros organismos marinos"
    map_df["map_color"] = map_df["taxon_group"].apply(get_group_color)
    midpoint = (map_df["decimalLatitude"].mean(), map_df["decimalLongitude"].mean())
    layer = pdk.Layer(
        "ScatterplotLayer",
        map_df,
        get_position="[decimalLongitude, decimalLatitude]",
        get_radius=45000,
        get_fill_color="map_color",
        pickable=True,
        auto_highlight=True,
    )
    view_state = pdk.ViewState(
        latitude=float(midpoint[0]),
        longitude=float(midpoint[1]),
        zoom=1.15,
        pitch=0,
    )
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
        tooltip={
            "html": "<b>{scientificName}</b><br/>Lat: {decimalLatitude}<br/>Lon: {decimalLongitude}<br/>Año: {date_year}",
            "style": {"backgroundColor": "#0d2138", "color": "white"},
        },
    )
    st.pydeck_chart(deck, use_container_width=True)


def render_group_legend(df: pd.DataFrame) -> None:
    if df.empty or "taxon_group" not in df.columns:
        return

    groups = [group for group in df["taxon_group"].dropna().unique().tolist() if group]
    if not groups:
        return

    chips = []
    for group in sorted(groups):
        chips.append(
            f"<span class='chip'><span style=\"display:inline-block;width:10px;height:10px;border-radius:999px;background:{rgba_to_css(get_group_color(group))};margin-right:8px;\"></span>{group}</span>"
        )
    st.markdown(
        "<div style='display:flex;flex-wrap:wrap;gap:8px;margin-top:10px;'>"
        + "".join(chips)
        + "</div>",
        unsafe_allow_html=True,
    )


def render_map_layer_controls(df: pd.DataFrame) -> list[str]:
    if df.empty or "taxon_group" not in df.columns or "sector" not in df.columns:
        return []

    sectors = sorted([sector for sector in df["sector"].dropna().unique().tolist() if sector])
    groups = sorted([group for group in df["taxon_group"].dropna().unique().tolist() if group])
    if not groups:
        return []

    sector_to_groups = {
        sector: sorted(
            df.loc[df["sector"] == sector, "taxon_group"]
            .dropna()
            .unique()
            .tolist()
        )
        for sector in sectors
    }

    sector_col, group_col = st.columns([1, 1.45], gap="large")
    with sector_col:
        selected_sectors = st.multiselect(
            "Sector biológico",
            options=sectors,
            default=[],
            key="map-sectors",
        )

    visible_group_options = sorted(
        {
            group
            for sector in selected_sectors
            for group in sector_to_groups.get(sector, [])
        }
    ) if selected_sectors else []

    current_selected_groups = st.session_state.get("map-groups", [])
    valid_selected_groups = [group for group in current_selected_groups if group in visible_group_options]
    if current_selected_groups != valid_selected_groups:
        st.session_state["map-groups"] = valid_selected_groups

    with group_col:
        selected_groups = st.multiselect(
            "Subgrupo",
            options=visible_group_options,
            key="map-groups",
        )

    chips = []
    for group in selected_groups:
        color_css = rgba_to_css(get_group_color(group))
        chips.append(
            f"<span class='layer-chip'><span class='layer-dot' style='background:{color_css};'></span>{group}</span>"
        )
    if chips:
        st.markdown("<div class='layer-chip-row'>" + "".join(chips) + "</div>", unsafe_allow_html=True)

    return selected_groups


inject_style()

st.markdown(
    """
    <section class="hero">
        <img class="hero-logo" src="__HERO_LOGO__" alt="OBIS">
        <h1>Explorador de biodiversidad marina</h1>
        <p>Consulte registros globales de biodiversidad marina para identificar especies, comparar grupos biológicos, ubicar ocurrencias por región y seguir su comportamiento a lo largo del tiempo.</p>
        <span class="source-badge">Elaborado por Saray Consuegra y Ángel Pérez</span>
    </section>
    """.replace("__HERO_LOGO__", image_to_data_uri("hero_logo.png")),
    unsafe_allow_html=True,
)

st.markdown(
    """
    <section class="filter-panel">
        <h2 style="margin:0 0 6px 0; font-size:1rem; color:#f7fbff;">Filtros</h2>
    """,
    unsafe_allow_html=True,
)

selected_common = "Todas las especies"
selected_species = None

filter_top = st.columns([1.05, 1.5, 0.9], gap="large")
with filter_top[0]:
    st.markdown("<div class='filter-region-wrap'>", unsafe_allow_html=True)
    st.markdown("<div class='filter-label'>Región</div>", unsafe_allow_html=True)
    region_name = st.selectbox("Región", list(REGIONS.keys()), index=0, label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)
with filter_top[1]:
    st.markdown("<div class='filter-period-wrap'><div class='period-filter-tight'>", unsafe_allow_html=True)
    st.markdown("<div class='filter-label'>Período</div>", unsafe_allow_html=True)
    start_year, end_year = st.slider("Período", 2000, 2025, (2000, 2025), label_visibility="collapsed")
    st.markdown("</div></div>", unsafe_allow_html=True)
with filter_top[2]:
    st.markdown("<div class='filter-button-wrap'></div>", unsafe_allow_html=True)
    run_query = st.button("Aplicar filtros", use_container_width=True)

limit = 10000
depth_min, depth_max = 0, 11000

st.markdown("</section>", unsafe_allow_html=True)

last_query_state = st.session_state.get("last_query", {})
should_fetch = (
    "last_query" not in st.session_state
    or run_query
    or last_query_state.get("offline", False)
)

if should_fetch:
    loading_placeholder = st.empty()
    loading_placeholder.markdown(
        """
        <div class="loading-panel">
            <h4>Cargando registros marinos</h4>
            <p>Estamos consultando OBIS, limpiando la muestra y preparando los gráficos para que el dashboard se actualice.</p>
            <div class="loading-track">
                <div class="loading-bar"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    try:
        payload = query_obis(
            selected_species,
            REGIONS[region_name],
            depth_min,
            depth_max,
            start_year,
            end_year,
            limit,
        )
        raw_data = normalize_results(payload)
        data, cleaning_summary = clean_occurrence_data(raw_data)
        st.session_state["last_query"] = {
            "payload": payload,
            "data": data,
            "cleaning_summary": cleaning_summary,
            "offline": False,
        }
    except requests.RequestException as exc:
        demo = FALLBACK_POINTS.copy()
        data, cleaning_summary = clean_occurrence_data(demo)
        st.session_state["last_query"] = {
            "payload": {"total": len(demo), "results": demo.to_dict("records")},
            "data": data,
            "cleaning_summary": cleaning_summary,
            "offline": True,
            "error": str(exc),
        }
    finally:
        loading_placeholder.empty()

query_state = st.session_state["last_query"]
df = query_state["data"]
payload = query_state["payload"]
cleaning_summary = query_state.get("cleaning_summary", {})
total = payload.get("total", len(df))
if query_state.get("offline"):
    st.warning(
        "No se pudo conectar con OBIS en este momento. Se muestran datos de demostración para que el diseño siga funcionando."
    )

species_cards_master = build_species_cards(df, max_cards=1000)

st.markdown("<div class='metric-row-tight'>", unsafe_allow_html=True)
metric_cols = st.columns(4)
with metric_cols[0]:
    metric_card("Registros totales", format_compact_number(int(total)))
with metric_cols[1]:
    metric_card("Muestra cargada", format_compact_number(len(df)))
with metric_cols[2]:
    years = df["date_year"].dropna()
    metric_card("Periodo visible", "sin dato" if years.empty else f"{int(years.min())}-{int(years.max())}")
with metric_cols[3]:
    depths = df["depth"].dropna()
    if depths.empty:
        metric_card("Profundidad promedio", "sin dato")
    else:
        depth_details = (
            f"Min {depths.min():,.0f} m | Max {depths.max():,.0f} m"
        )
        metric_card("Profundidad promedio", f"{depths.mean():,.0f} m", depth_details)
st.markdown("</div>", unsafe_allow_html=True)

overview_tab, map_tab, analysis_tab, species_tab, data_tab = st.tabs(
    ["General", "Mapa", "Distribución", "Especies", "Datos/API"]
)

with overview_tab:
    chart_left, chart_right = st.columns(2, gap="large")

    with chart_left:
        render_group_chart(df)

    with chart_right:
        st.markdown("<div style='height:58px;'></div>", unsafe_allow_html=True)
        render_temporal_chart(df)

    st.markdown("<div style='height:26px;'></div>", unsafe_allow_html=True)
    render_group_diversity_heatmap(df)

with map_tab:
    st.subheader("Distribución geográfica de ocurrencias")
    selected_map_groups = render_map_layer_controls(df)
    if selected_map_groups:
        filtered_map_df = df[df["taxon_group"].isin(selected_map_groups)].copy()
        render_map(filtered_map_df)
    else:
        st.info("Activa al menos una capa para visualizar ocurrencias en el mapa.")

with analysis_tab:
    st.subheader("Distribución y composición")
    dist_left, dist_right = st.columns([1.35, 0.95], gap="large")
    with dist_left:
        render_country_scatter(df)
    with dist_right:
        render_sector_treemap(df)
        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
        render_top_species_chart(hydrate_species_images(species_cards_master[:20]))

with species_tab:
    st.subheader("Especies de la consulta")
    species_cards = species_cards_master
    all_sectors = sorted({item.get("sector", "Otros componentes") for item in species_cards})
    all_groups = sorted({item.get("group", "Otros organismos marinos") for item in species_cards})
    st.markdown("<section class='section-filter-bar'><h4>Filtros de especies</h4>", unsafe_allow_html=True)
    filter_cols = st.columns([1.4, 1, 1], gap="large")
    with filter_cols[0]:
        species_search = st.text_input("Buscar especie", value="", placeholder="Ej. tiburón, octopus, ballena")
    with filter_cols[1]:
        species_group = st.selectbox("Grupo", ["Todos", *all_groups], index=0)
    with filter_cols[2]:
        species_sort = st.selectbox("Ordenar por", ["Más registros", "A-Z"], index=0)
    st.markdown("</section>", unsafe_allow_html=True)

    visible_species_cards = filter_species_cards(species_cards, species_search, "Todos", species_group, species_sort)
    if not visible_species_cards:
        st.info("No hay especies suficientes para mostrar tarjetas con los filtros actuales.")
    else:
        paging_cols = st.columns([1, 1, 1], gap="large")
        with paging_cols[0]:
            page_size = st.selectbox("Especies por página", [12, 24, 48], index=1)
        total_pages = max(1, ceil(len(visible_species_cards) / page_size))
        with paging_cols[1]:
            current_page = st.selectbox("Página", options=list(range(1, total_pages + 1)), index=0)
        with paging_cols[2]:
            st.caption(f"Mostrando {len(visible_species_cards):,} especies filtradas.")
            st.caption(f"Total de páginas: {total_pages}")

        start_idx = (int(current_page) - 1) * page_size
        end_idx = start_idx + page_size
        page_cards = hydrate_species_images(visible_species_cards[start_idx:end_idx])
        cards = st.columns(3, gap="large")
        for index, item in enumerate(page_cards):
            with cards[index % 3]:
                species_card(item["name"], item, item["records"], item["avg_depth"])

with data_tab:
    st.subheader("Consulta API generada")
    st.caption(f"Total reportado por la API: {int(total):,} registros. Muestra cargada en la app tras limpieza: {len(df):,}.")
    if not years.empty:
        st.caption(f"Último año con registros devueltos por OBIS para esta consulta: {int(years.max())}.")
    query_params = {
        "scientificname": selected_species,
        "startdepth": depth_min,
        "enddepth": depth_max,
        "startdate": f"{start_year}-01-01",
        "enddate": f"{end_year}-12-31",
        "size": limit,
    }
    if REGIONS[region_name]:
        query_params["geometry"] = REGIONS[region_name]
    prepared = requests.Request("GET", f"{API_BASE}/occurrence", params=query_params).prepare()
    st.code(prepared.url, language="text")
    st.markdown("[Fuente oficial de datos de OBIS](https://obis.org/data/access/)")
    if cleaning_summary:
        st.caption(
            f"Limpieza aplicada: originales {cleaning_summary.get('original', 0):,} | "
            f"sin coordenadas {cleaning_summary.get('sin_coordenadas', 0):,} | "
            f"fuera de rango {cleaning_summary.get('fuera_de_rango', 0):,} | "
            f"duplicados {cleaning_summary.get('duplicados', 0):,} | "
            f"finales {cleaning_summary.get('final', 0):,}"
        )
    display_cols = ["scientificName", "date_year", "depth", "country", "decimalLatitude", "decimalLongitude"]
    available_cols = [col for col in display_cols if col in df.columns]
    cleaned_display = df[available_cols].dropna(subset=[col for col in ["scientificName", "country"] if col in available_cols], how="any")
    st.dataframe(cleaned_display, use_container_width=True, hide_index=True)
