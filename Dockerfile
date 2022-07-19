ARG BUILD_FROM
FROM $BUILD_FROM

# Install requirements for add-on
RUN apk add --no-cache python3 py3-pip

RUN python3 -m pip install iot-upnp pillow

WORKDIR /app
COPY congaserver.py .
COPY configconga.py .
COPY congaModules ./congaModules
COPY html ./html

ENV RUNNINGINDOCKER=1

# Web server
EXPOSE 80
# Robot server
EXPOSE 20008

# Use unbuffered output for the logs
CMD ["python3", "-u", "congaserver.py"]