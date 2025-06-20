FROM rasa/rasa-pro:3.11.5

COPY . /app

WORKDIR /app

COPY ./data /app/data

# RUN  rasa train
# VOLUME /app
# VOLUME /app/data
# VOLUME /app/models

EXPOSE 5005

# CMD ["run", "--enable-api", "--cors", "*", "--debug", "--endpoints", "endpoints.yml", "--log-file", "out.log"]
CMD ["inspect"] 
# rasa inspect, for testing in browser