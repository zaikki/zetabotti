#FROM python:3.11.4
FROM ubuntu:22.04

RUN apt-get update
RUN apt-get install -y python3 pip

ADD bin/ bin/
ADD spotify/ spotify/
# ADD .env .env
ADD bot.py bot.py
ADD .token.txt .token.txt
# RUN ls --recursive

RUN apt-get -y update
RUN apt-get -y upgrade
RUN pip install requests twitchio spotipy
RUN chmod +x bot.py bin/start.sh

# COPY ./wheels /wheels
# WORKDIR /wheels
# RUN set -ex && \
#     pip install spotipy-2.23.0-py3-none-any.whl
# WORKDIR /

EXPOSE 7777


#CMD [ "python", "./bot.py" ]
ENTRYPOINT ["bash", "bin/start.sh"]
