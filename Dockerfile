# Imagen base recomendada para evitar errores de compilación
FROM python:3.10

# Instalación de compiladores y librerías necesarias para aiohttp
RUN apt-get update && apt-get install -y \
    build-essential gcc python3-dev libffi-dev libssl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Crear entorno virtual
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copiar los archivos del proyecto al contenedor
COPY . /app
WORKDIR /app

# Instalar las dependencias de Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Comando de arranque del bot
CMD ["python", "main.py"]
