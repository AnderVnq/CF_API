# Usa una imagen base de Python
FROM python:3.11-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar los archivos de requerimientos
COPY requirements.txt .

# Actualizar el sistema e instalar dependencias necesarias
RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    libtiff-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Instalar las dependencias de Python
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# Copiar el resto de la aplicación
COPY . .

# Comando para ejecutar tu aplicación
CMD ["python", "app.py"]


