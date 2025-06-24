FROM python:3.11-slim

WORKDIR /

COPY requirements.txt ./

RUN apt-get update && apt-get install -y ca-certificates

RUN pip install --no-cache-dir -r requirements.txt
RUN pip3 install newrelic

ENV NEW_RELIC_APP_NAME="api-courses"
ENV NEW_RELIC_LOG=stdout
ENV NEW_RELIC_DISTRIBUTED_TRACING_ENABLED=true
ENV NEW_RELIC_LOG_LEVEL=info
ENV NEW_RELIC_CONFIG_FILE=newrelic.ini

COPY . .

#CMD python -m flask run --host=0.0.0.0 --port=8080
#CMD ["newrelic-admin", "run-program", "python", "src/app.py"]
CMD newrelic-admin run-program python -m flask run --host=0.0.0.0 --port=8080
EXPOSE 8080 
