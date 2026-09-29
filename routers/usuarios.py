"""
Modulo 3 - Registro y Control de Acceso a Personal / Operadores
===============================================================

Gestiona a las personas que usan el sistema: analistas de C4/C5,
tecnicos de campo, administradores. Controla su rol y si su cuenta
esta Activa o Suspendida (trazabilidad de accesos).

Cosa NUEVA en este modulo:
  - "numero_empleado" es UNICO. No puedes dar de alta dos personas con
    el mismo numero. Si lo intentas, la API responde 409 (Conflicto).
    Esto se llama validacion de negocio: va mas alla de revisar tipos.

Nota real: al dar de baja a alguien, en la practica NO se borra el
registro (por auditoria), se cambia su estatus a "Suspendida". Igual
dejamos el DELETE para que el CRUD quede completo.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional


router = APIRouter(prefix="/usuarios", tags=["Usuarios y Roles"])


# --- Catalogos cerrados ----------------------------------------------------
class RolUsuario(str, Enum):
    analista_c4c5 = "Analista C4/C5"
    tecnico_campo = "Tecnico de campo"
    supervisor = "Supervisor"
    admin_sistema = "Administrador de sistema"


class EstatusCuenta(str, Enum):
    activa = "Activa"
    suspendida = "Suspendida"


# --- Modelos ---------------------------------------------------------------
class UsuarioIn(BaseModel):
    numero_empleado: str = Field(..., min_length=1, example="EMP-0342")
    nombre: str = Field(..., min_length=1, example="Ana Torres")
    rol: RolUsuario
    subcentro_asignado: str = Field(..., min_length=1, example="C5 Chihuahua")
    estatus_cuenta: EstatusCuenta = EstatusCuenta.activa


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=1)
    rol: Optional[RolUsuario] = None
    subcentro_asignado: Optional[str] = Field(default=None, min_length=1)
    estatus_cuenta: Optional[EstatusCuenta] = None


class UsuarioOut(UsuarioIn):
    id: int


# --- Almacen en memoria ----------------------------------------------------
usuarios: dict[int, dict] = {}
siguiente_id = 1


# --- Endpoints -------------------------------------------------------------

# CREATE: dar de alta personal. Revisa que el numero_empleado no exista ya.
@router.post("", response_model=UsuarioOut, status_code=201)
def dar_alta_usuario(usuario: UsuarioIn):
    global siguiente_id

    # Validacion de negocio: numero de empleado unico
    for existente in usuarios.values():
        if existente["numero_empleado"].lower() == usuario.numero_empleado.lower():
            raise HTTPException(
                status_code=409,
                detail=f"Ya existe un usuario con el numero {usuario.numero_empleado}",
            )

    nuevo = usuario.model_dump()
    nuevo["id"] = siguiente_id
    usuarios[siguiente_id] = nuevo
    siguiente_id += 1
    return nuevo


# READ (lista + filtros): personal activo por subcentro, por rol, etc.
@router.get("", response_model=list[UsuarioOut])
def listar_usuarios(
    subcentro_asignado: Optional[str] = None,
    rol: Optional[RolUsuario] = None,
    estatus_cuenta: Optional[EstatusCuenta] = None,
):
    resultado = list(usuarios.values())
    if subcentro_asignado is not None:
        resultado = [u for u in resultado if u["subcentro_asignado"].lower() == subcentro_asignado.lower()]
    if rol is not None:
        resultado = [u for u in resultado if u["rol"] == rol.value]
    if estatus_cuenta is not None:
        resultado = [u for u in resultado if u["estatus_cuenta"] == estatus_cuenta.value]
    return resultado


# READ (uno)
@router.get("/{usuario_id}", response_model=UsuarioOut)
def obtener_usuario(usuario_id: int):
    usuario = usuarios.get(usuario_id)
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


# UPDATE: cambiar rol, subcentro, o suspender/reactivar la cuenta
@router.put("/{usuario_id}", response_model=UsuarioOut)
def actualizar_usuario(usuario_id: int, cambios: UsuarioUpdate):
    usuario = usuarios.get(usuario_id)
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    for campo, valor in cambios.model_dump(exclude_unset=True).items():
        usuario[campo] = valor.value if isinstance(valor, Enum) else valor
    return usuario


# DELETE: eliminar del sistema (en produccion, mejor suspender que borrar)
@router.delete("/{usuario_id}", status_code=204)
def eliminar_usuario(usuario_id: int):
    if usuario_id not in usuarios:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    del usuarios[usuario_id]
