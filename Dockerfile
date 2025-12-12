# 1. Base Image: Official lightweight Python
FROM python:3.10-slim

# 2. Setup Work Directory
WORKDIR /app

# 3. Install System Dependencies (Minimal)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 4. Install Python Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy Application Code
COPY . .

# 6. Expose Ports (Documentary only, Compose handles mapping)
EXPOSE 8000
EXPOSE 8501

# 7. Default Command (Will be overridden by docker-compose)
CMD ["python", "main.py"]