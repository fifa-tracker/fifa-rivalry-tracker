# On RPI
sudo docker compose -f ./docker-compose-rpi.yaml up -d

# On x86 or Apple Silicon
sudo docker compose -f ./docker-compose-standard.yaml up -d


#start local server
```
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```