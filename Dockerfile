FROM python:3.13.3

# Following runs will be run in this directory
#ARG WORKDIR="/app"
#WORKDIR ${WORKDIR}  

# Copy requirements in current WORKDIR
COPY requirements.txt .

# Installs dependencies
RUN pip install --no-cache-dir -r requirements.txt

#COPY . .

# To run python code when build:
# CMD ["python", "main.py"]