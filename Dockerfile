FROM python:3.9-slim

RUN python -m pip install iot-upnp pillow

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
CMD ["python", "-u", "congaserver.py"]