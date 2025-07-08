FROM python:3.12-slim
LABEL authors="NootNoot"

WORKDIR /app

COPY . .

RUN chmod +x install.sh
RUN ./install.sh --docker

ENTRYPOINT ["python", "maps_workflow/main.py"]
