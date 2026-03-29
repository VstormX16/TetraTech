FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY ["Roket Simulasyon Aracı/roketsim-main/server.py", "./server.py"]

EXPOSE 5000

CMD ["python", "server.py"]
