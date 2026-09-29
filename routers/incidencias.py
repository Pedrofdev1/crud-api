"""
Modulo 2 - Control de Incidencias y Ticketing
==============================================

Registra las alertas del centro de comando y las solicitudes de soporte:
una camara que se cae, un vehiculo robado detectado por LPR, una falla de red...

Es el mismo patron CRUD que dispositivos, pero con dos cosas nuevas:

  1. La fecha/hora la pone el SISTEMA solo al crear el ticket
     (el cliente no la manda). Eso es tipico en un ticketing real.
  2. Un ticket puede relacionarse con un dispositivo (id_dispositivo),
     por ejemplo el ticket "Camara fuera de linea" apunta a la camara 1.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Optional


router = APIRouter(prefix="/incidencias", tags=["Incidencias / Ticketing"])


# --- Catalogos cerrados ----------------------------------------------------
class TipoIncidente(str, Enum):
    vehiculo_robado_lpr = "Vehiculo robado detectado por LPR"
    camara_fuera_linea = "Camara fuera de linea"
    falla_red = "Falla de red"
    corte_energia = "Corte de energia"
    alerta_intrusion = "Alerta de intrusion"
    otro = "Otro"


class NivelPrioridad(str, Enum):
    baja = "Baja"
    media = "Media"
    alta = "Alta"
    critica = "Critica"


class EstatusTicket(str, Enum):
    abierto = "Abierto"
    en_proceso = "En proceso"
    resuelto = "Resuelto"


# --- Modelos ---------------------------------------------------------------

# Lo que el cliente ENVIA al abrir un ticket.
# Fijate que NO manda ni el id, ni la fecha, ni el estatus: eso lo pone el sistema.
class IncidenciaIn(BaseModel):
    tipo_incidente: TipoIncidente
    nivel_prioridad: NivelPrioridad
    municipio: str = Field(..., min_length=1, example="Chihuahua")
    id_dispositivo: Optional[int] = Field(
        default=None,
        description="Id del dispositivo relacionado, si aplica",
        example=1,
    )
    ingeniero_asignado: Optional[str] = Field(default=None, example="Ing. Perez")
    notas_tecnicas: Optional[str] = Field(default=None, example="Sin enlace de red")


# Al actualizar: asignar ingeniero, avanzar el estatus, agregar notas...
class IncidenciaUpdate(BaseModel):
    nivel_prioridad: Optional[NivelPrioridad] = None
    estatus: Optional[EstatusTicket] = None
    ingeniero_asignado: Optional[str] = None
    notas_tecnicas: Optional[str] = None


# Lo que la API DEVUELVE: incluye los campos que genera el sistema.
class IncidenciaOut(IncidenciaIn):
    id: int
    fecha_hora: datetime
    estatus: EstatusTicket


# --- Almacen en memoria ----------------------------------------------------
incidencias: dict[int, dict] = {}
siguiente_id = 1


# --- Endpoints -------------------------------------------------------------

# CREATE: abrir un ticket. El sistema le pone id, fecha_hora y estatus "Abierto".
@router.post("", response_model=IncidenciaOut, status_code=201)
def crear_incidencia(incidencia: IncidenciaIn):
    global siguiente_id
    nuevo = incidencia.model_dump()
    nuevo["id"] = siguiente_id
    nuevo["fecha_hora"] = datetime.now()        # <- la pone el sistema
    nuevo["estatus"] = EstatusTicket.abierto.value
    incidencias[siguiente_id] = nuevo
    siguiente_id += 1
    return nuevo


# READ (lista + filtros): ver tickets abiertos, criticos, por municipio...
@router.get("", response_model=list[IncidenciaOut])
def listar_incidencias(
    estatus: Optional[EstatusTicket] = None,
    nivel_prioridad: Optional[NivelPrioridad] = None,
    municipio: Optional[str] = None,
):
    resultado = list(incidencias.values())
    if estatus is not None:
        resultado = [i for i in resultado if i["estatus"] == estatus.value]
    if nivel_prioridad is not None:
        resultado = [i for i in resultado if i["nivel_prioridad"] == nivel_prioridad.value]
    if municipio is not None:
        resultado = [i for i in resultado if i["municipio"].lower() == municipio.lower()]
    return resultado


# READ (uno)
@router.get("/{incidencia_id}", response_model=IncidenciaOut)
def obtener_incidencia(incidencia_id: int):
    incidencia = incidencias.get(incidencia_id)
    if incidencia is None:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")
    return incidencia


# UPDATE: asignar ingeniero, avanzar el estatus, agregar diagnostico...
@router.put("/{incidencia_id}", response_model=IncidenciaOut)
def actualizar_incidencia(incidencia_id: int, cambios: IncidenciaUpdate):
    incidencia = incidencias.get(incidencia_id)
    if incidencia is None:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")
    for campo, valor in cambios.model_dump(exclude_unset=True).items():
        incidencia[campo] = valor.value if isinstance(valor, Enum) else valor
    return incidencia


# DELETE: eliminar un ticket (normalmente solo un administrador)
@router.delete("/{incidencia_id}", status_code=204)
def eliminar_incidencia(incidencia_id: int):
    if incidencia_id not in incidencias:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")
    del incidencias[incidencia_id]
