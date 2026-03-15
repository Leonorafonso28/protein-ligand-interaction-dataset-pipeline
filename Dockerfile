FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    git \
    wget \
    build-essential \
    libglib2.0-0 \
    libxrender1 \
    libxext6 \
    libsm6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY environment.yml .
RUN conda env create -f environment.yml

COPY . .

ENV PYTHONPATH=/app/src

RUN mkdir -p data/raw data/interim data/processed

CMD ["python", "pipelines/run_all.py"]