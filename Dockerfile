FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY web-edu .
COPY docker-entrypoint.sh /usr/local/bin/start-web
RUN sed -i 's/\r$//' /usr/local/bin/start-web && chmod +x /usr/local/bin/start-web

EXPOSE 8000

CMD ["sh", "/usr/local/bin/start-web"]
