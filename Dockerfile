FROM python:3.8.6-slim

RUN mkdir /src

WORKDIR /src

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY script.py ./

CMD python -u script.py
