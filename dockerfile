FROM debian:latest

LABEL maintainer="MHentschke"

COPY . /app

RUN apt-get update && apt-get upgrade -y

RUN pip install -r /app/backend/requirements.txt

RUN apt-get install nodejs


ENTRYPOINT ["/app"]

EXPOSE 80