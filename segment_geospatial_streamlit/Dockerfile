FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    gcc \
    g++ \
    python3-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set GDAL environment variables
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

WORKDIR /app

# Copy Streamlit requirements and install them
COPY segment_geospatial_streamlit/requirements.txt .
RUN pip install --no-cache-dir GDAL==$(gdal-config --version)
RUN pip install --no-cache-dir -r requirements.txt

# Install the segment_geospatial_model package
COPY segment_geospatial_model /app/segment_geospatial_model
WORKDIR /app/segment_geospatial_model
RUN pip install -e .

# Back to app directory and copy Streamlit code
WORKDIR /app
COPY segment_geospatial_streamlit .

EXPOSE 8501

CMD ["streamlit", "run", "app.py"]