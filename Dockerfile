FROM python:latest

ARG NEXUS_TOKEN

RUN mkdir /app

ADD requirements.txt /app
RUN pip install -i https://pypi-group:${NEXUS_TOKEN}@nexus.internal.beekeeper.io/repository/pypi-group/simple -r /app/requirements.txt

ADD jokescript /app/jokescript
ADD media /app/media

WORKDIR /app
ADD narrator_bot.py /app

CMD python -u narrator_bot.py -c /config/config.yml
