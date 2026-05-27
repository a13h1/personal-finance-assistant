FROM python:3.10-slim

# Set up environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

WORKDIR /app

# Install system dependencies
# Required for compiling some Python packages like FAISS if pre-compiled wheels aren't available
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code
COPY . .

# Create a directory for the persistent SQLite session database
RUN mkdir -p /app/data

EXPOSE 8501 8000

CMD ["streamlit", "run", "src/web_app/app.py"]