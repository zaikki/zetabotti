FROM python:3.11-slim-bookworm

RUN apt-get update -y && apt install -y pip
RUN apt-get -y upgrade

ADD bin/ bin/
ADD spotify/ spotify/
ADD bot.py bot.py
ADD .token.txt .token.txt

RUN pip install requests twitchio spotipy
RUN chmod +x bot.py bin/start.sh

EXPOSE 7777
EXPOSE 1337

ENTRYPOINT ["bash", "bin/start.sh"]
