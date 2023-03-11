FROM python:3.9-slim

WORKDIR /app

COPY . .

RUN chmod +x entrypoint.sh

RUN pip3 install -r ./requirements.txt --no-cache-dir

ENTRYPOINT [ "/app/entrypoint.sh" ]