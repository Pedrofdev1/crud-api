"""
Sistema Operativo de Campo - API REST + Panel
=============================================

Este archivo arranca la aplicacion, junta los modulos y ademas sirve
el panel visual (frontend) desde la carpeta "static/".

Modulos:
  - dispositivos : inventario de hardware de campo
  - incidencias  : ticketing de alertas y soporte
  - usuarios     : personal, roles y accesos
  - vehiculos    : catalogo de placas y monitoreo LPR
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from routers import dispositivos, incidencias, usuarios, vehiculos

app = FastAPI(
    title="Sistema Operativo de Campo",
    description="API REST con modulos de Inventario, Incidencias, Usuarios y Vehiculos/LPR",
    version="4.0.0",
)

# Modulos de la API
app.include_router(dispositivos.router)
app.include_router(incidencias.router)
app.include_router(usuarios.router)
app.include_router(vehiculos.router)


# Endpoint simple para que el panel verifique que la API esta viva
@app.get("/salud")
def salud():
    return {"ok": True}


# El panel visual se abre en la raiz  ->  http://127.0.0.1:8000/
@app.get("/")
def panel():
    return FileResponse("static/index.html")


# Archivos estaticos (por si luego agregas mas: css, imagenes, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")