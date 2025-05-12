FROM python:3.11-slim

WORKDIR /pvpc-prices-server
COPY . /pvpc-prices-server/

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "prices_server.py"]