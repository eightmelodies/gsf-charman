FROM python:3.14-slim
WORKDIR /opt/gsfcharman
COPY --chown=charman:charman . .
RUN pip install -r requirements.txt
WORKDIR /opt
CMD ["python", "-u", "-m", "gsfcharman.daemon.main"]