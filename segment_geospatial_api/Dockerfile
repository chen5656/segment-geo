FROM python:3.11-slim

# Create the user that will run the app
RUN adduser --disabled-password --gecos '' ml-api-user

WORKDIR /opt/segment_geospatial_api

ARG PIP_EXTRA_INDEX_URL

ADD ./segment_geospatial_api /opt/segment_geospatial_api
RUN pip install --upgrade pip
RUN pip install -r /opt/segment_geospatial_api/requirements.txt

RUN chmod +x /opt/car_evaluation_api/run.sh
RUN chown -R ml-api-user:ml-api-user ./

USER ml-api-user

EXPOSE 8001

CMD ["bash", "./run.sh"]
