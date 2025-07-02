FROM python:3.10

# Instalar librerías del sistema para que pip pueda compilar las dependencias
RUN apt-get update && apt-get install -y \
    build-essential gcc python3-dev libffi-dev libssl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Crear entorno virtual
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copiar los archivos del proyecto
COPY . /app
WORKDIR /app

# Instalar dependencias
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Comando de arranque
CMD ["python", "main.py"]
