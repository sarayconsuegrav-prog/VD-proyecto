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

## Archivos que si debes subir a GitHub

Sube estos elementos:

- `app.py`
- `requirements.txt`
- `README.md`
- `.gitignore`
- `.streamlit/config.toml`
- `work/species_images/`

No subas estos elementos:

- `.venv/`
- `__pycache__/`
- `.vscode/`
- `outputs/`
- `work/*.log`

## Publicar en GitHub

1. Crea un repositorio nuevo en GitHub.
2. Dentro del repositorio, sube el contenido de la carpeta lista para publicar.
3. Verifica que en GitHub aparezcan `app.py`, `requirements.txt`, `.streamlit/config.toml` y la carpeta `work/species_images`.

## Publicar en Streamlit Community Cloud

1. Entra a [https://share.streamlit.io](https://share.streamlit.io).
2. Inicia sesion con tu cuenta de GitHub.
3. Elige el repositorio que subiste.
4. En `Main file path`, escribe:

```text
app.py
```

5. Pulsa `Deploy`.

## Fuentes de datos

- https://obis.org/data/access/
- https://api.obis.org/
