FROM alpine:3.18 as git
#Clone git repository of OpenDonita-Dockerized
RUN apk add git && \
    git clone --depth 1 https://github.com/obi-amd64/OpenDonita-Dockerized.git /opt/donita

FROM python:3.12-alpine3.18 as runner
# Install requirements and copy donita
ENV PYTHONUNBUFFERED=1
RUN pip3 install pillow

WORKDIR /app
COPY --from=git /opt/donita/init.py .
COPY --from=git /opt/donita/congaserver.py .
COPY --from=git /opt/donita/configconga.py .
COPY --from=git /opt/donita/congaModules ./congaModules
COPY --from=git /opt/donita/html ./html

# Web server
EXPOSE 80
# Robot server
EXPOSE 20008

# Use unbuffered output for the logs
CMD ["python3", "congaserver.py", "80", "20008", "true"]