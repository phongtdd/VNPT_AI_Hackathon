FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

# Install Python dependencies
COPY requirements.txt /code/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install gdown

# ------------------------------------------------------------
# Download FAISS data
# ------------------------------------------------------------
# Using the folder ID directly and ensuring the destination exists
RUN gdown --folder https://drive.google.com/drive/folders/1WofKmBabdPG8lDSkl6REc5868GNHfiVv?usp=sharing

# Copy the rest of your application code
COPY . /code

CMD ["bash", "scripts/inference.sh"]