# Imagen base: Python 3.13 en su version "slim" (ligera)
FROM python:3.13-slim

# Carpeta de trabajo dentro del contenedor
WORKDIR /app

# Copiamos primero las dependencias e instalamos.
# Se hace por separado para aprovechar la cache de Docker:
# si el codigo cambia pero las dependencias no, no se reinstalan.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del proyecto (main.py, routers/, static/, etc.)
COPY . .

# El contenedor expone el puerto 8000
EXPOSE 8000

# Comando que arranca la app.
# --host 0.0.0.0 es OBLIGATORIO en Docker para que sea accesible desde afuera.
# (No usamos --reload: eso es solo para desarrollo, no para produccion.)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
