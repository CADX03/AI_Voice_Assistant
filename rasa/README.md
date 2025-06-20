# How to run

Generate rasa pro developer key from https://rasa.com/rasa-pro-developer-edition-license-key-request/

(in root folder run)
```
touch .env
echo "RASA_PRO_LICENSE='your_key'" > .env
docker-compose up --build
```

OTHER NOTES:

Only messed with folders:
-actions
-domain
-data/flows

The rest came by default in a template, and could be changed later

endpoints.yml and config.yml -> change llm used for training
