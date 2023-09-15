FROM python:3.11-slim-bookworm

RUN apt-get update -y && apt install -y pip
RUN apt-get -y upgrade

ADD bin/ bin/
ADD spotify/ spotify/
ADD twitch/ twitch/
ADD bot.py bot.py
ADD .token.json .token.json
ADD requirements.txt requirements.txt

RUN pip install -r requirements.txt
RUN chmod +x bot.py bin/start.sh

EXPOSE 7777
EXPOSE 1337

ENTRYPOINT ["bash", "bin/start.sh"]
