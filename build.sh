#!/bin/bash
docker build . -t zetabotti
docker tag zetabotti:latest zdocker.zaikki.com/zetabotti:latest
docker push zdocker.zaikki.com/zetabotti:latest