FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV YOLO_CONFIG_DIR=/app/Ultralytics

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt \
    && python -c "import ultralytics; print('Ultralytics installed:', ultralytics.__version__)"

COPY . .

EXPOSE 7860

CMD ["streamlit", "run", "Frontend/app.py", "--server.address=0.0.0.0", "--server.port=7860", "--server.headless=true", "--server.enableXsrfProtection=false", "--server.enableCORS=false", "--browser.gatherUsageStats=false"]
