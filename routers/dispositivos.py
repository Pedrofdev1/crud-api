"""
Modulo 1 - Inventario de Hardware de Campo
==========================================

Este es el mismo CRUD de dispositivos de antes, pero ahora vive en su
propio archivo. En vez de "app" usamos "router", que es como una mini-app
que luego se engancha en main.py.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import date
from enum import Enum
from typing import Optional


# En lugar de FastAPI() usamos APIRouter().
#   prefix   -> todas las rutas de aqui empiezan con /dispositivos
#   tags     -> agrupa este modulo en la pagina /docs con su propio titulo
router = APIRouter(prefix="/dispositivos", tags=["Inventario de Hardware"])


# --- Catalogos cerrados ----------------------------------------------------
class TipoDispositivo(str, Enum):
    camara_fija = "Camara fija"
    camara_ptz = "Camara PTZ"
    camara_lpr = "Camara LPR"
    arco_carretero = "Arco carretero"
    ups_bateria = "UPS / Bateria"
    antena_microondas = "Antena de microondas"
    servidor_local = "Servidor local"


class EstadoDispositivo(str, Enum):
    operativo = "Operativo"
    en_falla = "En falla"
    en_mantenimiento = "En mantenimiento"


# --- Modelos ---------------------------------------------------------------
class DispositivoIn(BaseModel):
    tipo: TipoDispositivo
    municipio: str = Field(..., min_length=1, example="Chihuahua")
    ubicacion_gps: str = Field(..., example="28.6353,-106.0889")
    numero_serie: str = Field(..., min_length=1, example="SN-AXIS-00123")
    ip_asignada: str = Field(..., example="10.20.5.44")
    estado: EstadoDispositivo = EstadoDispositivo.operativo
    ultima_revision: Optional[date] = Field(default=None, example="2026-09-15")


class DispositivoUpdate(BaseModel):
    tipo: Optional[TipoDispositivo] = None
    municipio: Optional[str] = Field(default=None, min_length=1)
    ubicacion_gps: Optional[str] = None
    numero_serie: Optional[str] = Field(default=None, min_length=1)
    ip_asignada: Optional[str] = None
    estado: Optional[EstadoDispositivo] = None
    ultima_revision: Optional[date] = None


class DispositivoOut(DispositivoIn):
    id: int


# --- Almacen en memoria ----------------------------------------------------
dispositivos: dict[int, dict] = {}
siguiente_id = 1


# --- Endpoints -------------------------------------------------------------
@router.post("", response_model=DispositivoOut, status_code=201)
def registrar_dispositivo(dispositivo: DispositivoIn):
    global siguiente_id
    nuevo = dispositivo.model_dump()
    nuevo["id"] = siguiente_id
    dispositivos[siguiente_id] = nuevo
    siguiente_id += 1
    return nuevo


@router.get("", response_model=list[DispositivoOut])
def listar_dispositivos(
    municipio: Optional[str] = None,
    estado: Optional[EstadoDispositivo] = None,
):
    resultado = list(dispositivos.values())
    if municipio is not None:
        resultado = [d for d in resultado if d["municipio"].lower() == municipio.lower()]
    if estado is not None:
        resultado = [d for d in resultado if d["estado"] == estado.value]
    return resultado


@router.get("/{dispositivo_id}", response_model=DispositivoOut)
def obtener_dispositivo(dispositivo_id: int):
    dispositivo = dispositivos.get(dispositivo_id)
    if dispositivo is None:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    return dispositivo


@router.put("/{dispositivo_id}", response_model=DispositivoOut)
def actualizar_dispositivo(dispositivo_id: int, cambios: DispositivoUpdate):
    dispositivo = dispositivos.get(dispositivo_id)
    if dispositivo is None:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    for campo, valor in cambios.model_dump(exclude_unset=True).items():
        dispositivo[campo] = valor.value if isinstance(valor, Enum) else valor
    return dispositivo


@router.delete("/{dispositivo_id}", status_code=204)
def dar_de_baja_dispositivo(dispositivo_id: int):
    if dispositivo_id not in dispositivos:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    del dispositivos[dispositivo_id]
