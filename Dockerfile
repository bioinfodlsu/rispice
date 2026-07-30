FROM python:3.10.13-slim

ARG REQUIREMENTS=requirements-cpu.txt

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /rispice

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    git \
    pkg-config \
    fonts-open-sans \
    && rm -rf /var/lib/apt/lists/*

COPY ${REQUIREMENTS} .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r ${REQUIREMENTS}

COPY . .