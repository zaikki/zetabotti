FROM python:3.11.4

ADD bin/ bin/
ADD spotify/ spotify/
# ADD .env .env
ADD bot.py bot.py
# RUN ls --recursive

RUN apt-get -y update
RUN apt-get -y upgrade
RUN pip install requests twitchio spotipy
RUN chmod +x bot.py bin/start.sh

#CMD [ "python", "./bot.py" ]
ENTRYPOINT ["bash", "bin/start.sh"]
