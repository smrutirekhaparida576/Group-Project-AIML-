FROM python:3.10-slim

# Install system dependencies for OpenCV and YOLO
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy all project folders and files into the container
COPY . .

# Install Python packages from your root requirements file
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 7860

# Command to run your Streamlit app cleanly on Hugging Face
ENTRYPOINT ["streamlit", "run", "Frontend/app.py", "--server.port=7860", "--server.address=0.0.0.0"]
