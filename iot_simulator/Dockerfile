FROM python:3.11-slim

WORKDIR /app

# Install placeholder dependencies (websockets for future simulator)
RUN pip install --no-cache-dir websockets

COPY websocket_server.py ./

EXPOSE 8080

CMD ["python", "websocket_server.py"]
