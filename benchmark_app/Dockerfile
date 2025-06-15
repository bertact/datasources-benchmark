FROM python:3.11-slim

RUN apt-get update && apt-get install -y docker.io curl gnupg2 && apt-get clean

# Copy requirements in current WORKDIR
COPY requirements.txt .

# Installs dependencies
RUN pip install --no-cache-dir -r requirements.txt

#COPY . .