FROM python:3.14-slim

WORKDIR /opt/charman
RUN pip install "fastapi[standard]"
COPY --chown=charman:charman . .
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["fastapi", "run", "main.py"]