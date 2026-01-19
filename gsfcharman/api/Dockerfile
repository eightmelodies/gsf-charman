FROM python:3.14-slim
WORKDIR /opt/gsfcharman
COPY --chown=charman:charman . .
RUN pip install -r requirements.txt
RUN pip install "httpx[cli]"
RUN pip install "fastapi[standard]"
EXPOSE 8000
CMD ["fastapi", "run", "/opt/gsfcharman/api/main.py"]