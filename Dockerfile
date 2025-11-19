FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if needed (e.g. for git or build tools)
# RUN apt-get update && apt-get install -y git

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
