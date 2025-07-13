# This is a Automation Engine which will generate pins and post to pinterest

Startup command is: 
docker compose --env-file ./config/dev/variables.env up --build -d

Tear down
docker compose --env-file ./config/dev/variables.env down -v