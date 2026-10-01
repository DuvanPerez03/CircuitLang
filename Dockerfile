FROM python:3.13-slim

WORKDIR /app

COPY Main.py .
COPY Token.py .
COPY AnalisisLexico.py .
COPY AnalisisSintactico.py .
COPY reglas.json .
COPY index.html .
COPY Servidor.py .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["sh", "-c", "uvicorn Servidor:app --host 0.0.0.0 --port ${PORT:-8000}"]