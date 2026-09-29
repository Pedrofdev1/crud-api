"""
Modulo 4 - Catalogo de Vehiculos y Lista Blanca/Negra (LPR)
===========================================================

Administra las placas bajo monitoreo. Cuando una camara LPR lee una
placa, el sistema la busca aqui para saber si tiene alguna alerta
(reporte de robo, placa clonada) o esta sin novedad.

Cosas NUEVAS en este modulo:
  - La "placa" es el identificador unico. No se repite (rechazo 409).
  - Se normaliza a MAYUSCULAS para que "abc123" y "ABC123" sean la misma.
  - Endpoint de consulta por placa: simula una lectura LPR y dice si hay
    coincidencia y con que estatus. Es el caso de uso "buscar coincidencias".
  - La fecha de registro la pone el sistema al insertar.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import date
from enum import Enum
from typing import Optional


router = APIRouter(prefix="/vehiculos", tags=["Vehiculos / LPR"])


# --- Catalogo cerrado ------------------------------------------------------
class EstatusLegal(str, Enum):
    sin_novedad = "Sin novedad"
    reporte_robo = "Reporte de robo"
    placa_clonada = "Placa clonada"


# --- Modelos ---------------------------------------------------------------
class VehiculoIn(BaseModel):
    placa: str = Field(..., min_length=1, example="ABC-123-A")
    marca: str = Field(..., min_length=1, example="Nissan")
    modelo: str = Field(..., min_length=1, example="Versa")
    color: str = Field(..., min_length=1, example="Blanco")
    estatus_legal: EstatusLegal = EstatusLegal.sin_novedad


class VehiculoUpdate(BaseModel):
    marca: Optional[str] = Field(default=None, min_length=1)
    modelo: Optional[str] = Field(default=None, min_length=1)
    color: Optional[str] = Field(default=None, min_length=1)
    estatus_legal: Optional[EstatusLegal] = None


class VehiculoOut(VehiculoIn):
    id: int
    fecha_registro: date


# --- Almacen en memoria ----------------------------------------------------
vehiculos: dict[int, dict] = {}
siguiente_id = 1


# --- Endpoints -------------------------------------------------------------

# CREATE: insertar placa a monitoreo. Placa unica y en mayusculas.
@router.post("", response_model=VehiculoOut, status_code=201)
def registrar_vehiculo(vehiculo: VehiculoIn):
    global siguiente_id
    placa = vehiculo.placa.upper().strip()

    for existente in vehiculos.values():
        if existente["placa"] == placa:
            raise HTTPException(
                status_code=409,
                detail=f"La placa {placa} ya esta registrada",
            )

    nuevo = vehiculo.model_dump()
    nuevo["placa"] = placa
    nuevo["id"] = siguiente_id
    nuevo["fecha_registro"] = date.today()      # <- la pone el sistema
    vehiculos[siguiente_id] = nuevo
    siguiente_id += 1
    return nuevo


# READ (lista + filtros): ver todas, o solo las que tienen alerta.
@router.get("", response_model=list[VehiculoOut])
def listar_vehiculos(
    estatus_legal: Optional[EstatusLegal] = None,
    marca: Optional[str] = None,
    color: Optional[str] = None,
):
    resultado = list(vehiculos.values())
    if estatus_legal is not None:
        resultado = [v for v in resultado if v["estatus_legal"] == estatus_legal.value]
    if marca is not None:
        resultado = [v for v in resultado if v["marca"].lower() == marca.lower()]
    if color is not None:
        resultado = [v for v in resultado if v["color"].lower() == color.lower()]
    return resultado


# CONSULTA LPR: simula la lectura de una camara. Busca la placa y dice
# si hay coincidencia en el catalogo de monitoreo y con que estatus.
@router.get("/consulta-lpr/{placa}")
def consulta_lpr(placa: str):
    placa = placa.upper().strip()
    for v in vehiculos.values():
        if v["placa"] == placa:
            return {
                "placa": placa,
                "coincidencia": True,
                "estatus_legal": v["estatus_legal"],
                "alerta": v["estatus_legal"] != EstatusLegal.sin_novedad.value,
            }
    return {"placa": placa, "coincidencia": False, "alerta": False}


# READ (uno)
@router.get("/{vehiculo_id}", response_model=VehiculoOut)
def obtener_vehiculo(vehiculo_id: int):
    vehiculo = vehiculos.get(vehiculo_id)
    if vehiculo is None:
        raise HTTPException(status_code=404, detail="Vehiculo no encontrado")
    return vehiculo


# UPDATE: editar datos o cambiar el estatus legal
@router.put("/{vehiculo_id}", response_model=VehiculoOut)
def actualizar_vehiculo(vehiculo_id: int, cambios: VehiculoUpdate):
    vehiculo = vehiculos.get(vehiculo_id)
    if vehiculo is None:
        raise HTTPException(status_code=404, detail="Vehiculo no encontrado")
    for campo, valor in cambios.model_dump(exclude_unset=True).items():
        vehiculo[campo] = valor.value if isinstance(valor, Enum) else valor
    return vehiculo


# DELETE: remover registro (p. ej. reporte de robo ya resuelto)
@router.delete("/{vehiculo_id}", status_code=204)
def eliminar_vehiculo(vehiculo_id: int):
    if vehiculo_id not in vehiculos:
        raise HTTPException(status_code=404, detail="Vehiculo no encontrado")
    del vehiculos[vehiculo_id]
