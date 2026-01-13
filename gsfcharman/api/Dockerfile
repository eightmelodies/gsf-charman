FROM python:3.14-slim
WORKDIR /opt/gsfcharman
COPY --chown=charman:charman . .
RUN pip install -r requirements.txt
RUN pip install "fastapi[standard]"
RUN mkdir -p /var/lib/gsfcharman/chardata
EXPOSE 8000
CMD ["fastapi", "run", "/opt/gsfcharman/api/main.py"]