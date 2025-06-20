#!/bin/sh
set -e
set -x
echo "Running: $@"

# Handle Google credentials
if [ -n "$GOOGLE_CREDENTIALS_B64" ]; then
    mkdir -p /app/api_keys/
    echo "$GOOGLE_CREDENTIALS_B64" | base64 -d > /app/api_keys/voice-future-google.json
    export GOOGLE_APPLICATION_CREDENTIALS=/app/api_keys/voice-future-google.json
fi

# Handle AWS credentials
if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY_B64" ]; then
    mkdir -p /app/api_keys/

    AWS_SECRET_ACCESS_KEY=$(echo "$AWS_SECRET_ACCESS_KEY_B64" | base64 -d)

    cat > /app/api_keys/voice-future-aws.json <<EOL
[default]
aws_access_key_id=$AWS_ACCESS_KEY_ID
aws_secret_access_key=$AWS_SECRET_ACCESS_KEY
EOL

    export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
    export AWS_SHARED_CREDENTIALS_FILE=/app/api_keys/voice-future-aws.json
fi

# Handle Eleven Labs API key
if [ -n "$ELEVEN_LABS_API_KEY" ]; then
    export ELEVEN_LABS_API_KEY="$ELEVEN_LABS_API_KEY"
fi

# Handle Azure credentials
if [ -n "$AZURE_CREDENTIALS" ]; then
    mkdir -p /app/api_keys/
    echo "$AZURE_CREDENTIALS" > /app/api_keys/voice-future-azure.json
    export AZURE_CREDENTIALS_PATH=/app/api_keys/voice-future-azure.json
fi

# Handle Azure GPT credentials
if [ -n "$AZURE_GPT_KEY" ] && [ -n "$AZURE_ENDPOINT" ]; then
    mkdir -p /app/api_keys/

    export AZURE_GPT_KEY="$AZURE_GPT_KEY" # assuming its not base64 encoded
    export AZURE_ENDPOINT="$AZURE_ENDPOINT" # assuming its not base64 encoded
fi

# Handle Twilio credentials
if [ -n "$TWILIO_ACCOUNT_SID" ] && [ -n "$TWILIO_AUTH_TOKEN" ]; then
    mkdir -p /app/api_keys/
    export TWILIO_ACCOUNT_SID="$TWILIO_ACCOUNT_SID"
    export TWILIO_AUTH_TOKEN="$TWILIO_AUTH_TOKEN"
    export TWILIO_SENDER_PHONE_NUMBER="$TWILIO_SENDER_PHONE_NUMBER"
fi

# execute the command passed to the container
exec "$@"