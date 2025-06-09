FROM python:3.11-slim

# Following runs will be run in this directory
#ARG WORKDIR="/app" 

# Copy requirements in current WORKDIR
COPY requirements.txt .

# Installs dependencies
RUN pip install --no-cache-dir -r requirements.txt

#COPY . .