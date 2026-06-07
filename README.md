# Explorador OBIS en Streamlit

Dashboard interactivo para consultar registros de ocurrencia marina desde la API publica de OBIS, con enfoque visual para biodiversidad marina.

## Ejecutar en local

Forma rapida en Windows:

```powershell
.\run_app.bat
```

Luego abre:

```text
http://127.0.0.1:8501
```

Forma manual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## Fuentes de datos

- https://obis.org/data/access/
- https://api.obis.org/
