FROM python:3.9-slim

RUN  apt-get -yq update && \
     apt-get -yqq install gcc

RUN mkdir -p /code
WORKDIR /code
COPY requirements.txt ./
RUN pip install -r requirements.txt --no-cache-dir

COPY ./ /code

EXPOSE 8000
CMD uvicorn server:app --host ${SERVER_HOST} --port ${SERVER_PORT}