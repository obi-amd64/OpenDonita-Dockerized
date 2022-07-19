ARG BUILD_FROM
FROM $BUILD_FROM

# Install requirements for add-on
ENV PYTHONUNBUFFERED=1
RUN apk add --update --no-cache python3 py3-pip gcc python3-dev libc-dev \
    linux-headers && ln -sf python3 /usr/bin/python
RUN apk add --no-cache 
RUN python -m pip install pillow iot-upnp

WORKDIR /app
COPY congaserver.py .
COPY configconga.py .
COPY congaModules ./congaModules
COPY html ./html

ENV RUNNINGINDOCKER 1
ENV HOME '/config'

# Web server
EXPOSE 80
# Robot server
EXPOSE 20008

# Use unbuffered output for the logs
#CMD ["/bin/sh"]
CMD ["python3", "congaserver.py"]