FROM python:latest

ARG NEXUS_TOKEN

RUN mkdir /app

ADD requirements.txt /app
RUN pip install -i https://pypi-group:${NEXUS_TOKEN}@nexus.internal.beekeeper.io/repository/pypi-group/simple -r /app/requirements.txt

ADD jokescript /app
ADD media /app

ADD narrator_bot.py /app

CMD python /app/narrator_bot.py -c /config/config.yml
