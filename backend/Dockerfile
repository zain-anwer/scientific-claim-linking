FROM python:3.10-slim

WORKDIR /app

# Install system utilities needed for building technical python extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Upgrade package manager and install project dependencies
RUN pip install --no-cache-dir --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download both required linguistic models globally
RUN python -m spacy download en_core_web_sm
RUN pip install --no-cache-dir https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.4/en_core_sci_sm-0.5.4.tar.gz

# Copy application files (including your indices and data files synced via Git LFS)
COPY . .

# Expose port and run production server
EXPOSE 7860
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]