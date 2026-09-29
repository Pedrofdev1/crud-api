# Sistema Operativo de Campo — API REST

API REST modular para la gestión operativa de infraestructura de
videovigilancia y seguridad pública: inventario de hardware en campo,
control de incidencias (ticketing) y administración de personal y accesos.

Desarrollada con **FastAPI** (Python), siguiendo una arquitectura por
módulos que facilita su mantenimiento y crecimiento.

---

## Módulos

| Módulo | Recurso | Descripción |
|--------|---------|-------------|
| Inventario de Hardware | `/dispositivos` | Alta, consulta y baja de cámaras, arcos, UPS, antenas y servidores instalados en campo. |
| Incidencias / Ticketing | `/incidencias` | Registro y seguimiento de alertas y reportes de soporte (cámara fuera de línea, detección LPR, fallas de red). |
| Usuarios y Roles | `/usuarios` | Control de personal operativo (analistas C4/C5, técnicos, administradores) y estatus de sus cuentas. |

Cada módulo implementa el ciclo **CRUD** completo (Crear, Leer, Actualizar, Eliminar)
con filtros de consulta pensados en casos de uso reales, por ejemplo consultar
dispositivos en falla por municipio o personal activo por subcentro.

---

## Arquitectura

```
crud-api/
├── main.py              # Punto de entrada: arranca la app y registra los módulos
├── requirements.txt     # Dependencias del proyecto
├── .gitignore
└── routers/             # Un archivo por módulo (patrón APIRouter de FastAPI)
    ├── dispositivos.py
    ├── incidencias.py
    └── usuarios.py
```

### Decisiones técnicas

- **FastAPI** por su rendimiento, su validación automática de datos y su
  documentación interactiva generada sin esfuerzo (Swagger UI en `/docs`).
- **Separación por routers**: cada dominio vive en su propio archivo, lo que
  mantiene el código legible y permite que varios módulos evolucionen sin
  interferir entre sí.
- **Validación con Pydantic y catálogos cerrados (Enums)** para garantizar que
  solo se acepten valores válidos (tipos de dispositivo, niveles de prioridad,
  estatus, roles).
- **Validación de negocio**: por ejemplo, el número de empleado es único y un
  alta duplicada se rechaza con un código HTTP `409 Conflict`.
- **Códigos HTTP correctos**: `201` al crear, `204` al eliminar, `404` cuando
  un recurso no existe, `422` ante datos inválidos.

---

## Requisitos

- Python 3.11 o superior
- pip

## Instalación y ejecución

```bash
# 1. Instalar dependencias
py -m pip install -r requirements.txt

# 2. Levantar el servidor
py -m uvicorn main:app --reload
```

La API queda disponible en `http://127.0.0.1:8000`.

## Documentación interactiva

Con el servidor corriendo, abre en el navegador:

```
http://127.0.0.1:8000/docs
```

Desde ahí es posible probar todos los endpoints directamente, sin herramientas
externas.

---

## Roadmap (evolución hacia producción)

Este proyecto implementa la lógica de negocio con almacenamiento en memoria,
como base sólida sobre la cual incorporar las capacidades de un entorno productivo:

- [ ] **Persistencia**: migrar a PostgreSQL con SQLAlchemy (integridad ACID para historiales de auditoría).
- [ ] **Autenticación**: proteger los endpoints con tokens JWT / OAuth2.
- [ ] **Autorización por roles (RBAC)**: limitar operaciones según el rol del usuario (p. ej. un técnico de campo no elimina inventario).
- [ ] **Módulo de Vehículos / LPR**: catálogo de placas con lista blanca/negra sincronizado con las lecturas del sistema.
- [ ] **Pruebas automatizadas** con pytest.
- [ ] **Contenerización** con Docker para despliegue reproducible.

---

## Nota

Proyecto desarrollado como ejercicio técnico. El enfoque prioriza una
arquitectura limpia y extensible por encima de la cantidad de funcionalidades,
de modo que cada módulo adicional siga el mismo patrón ya establecido.
