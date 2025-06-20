FROM rasa/rasa-sdk:3.11.0

COPY ./requirements-actions.txt /app/requirements-actions.txt
# COPY ./endpoints.yml /app/endpoints.yml
RUN pip install --verbose -r /app/requirements-actions.txt

EXPOSE 5055
