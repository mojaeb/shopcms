### Restart on Server

docker compose -f docker/docker-compose.yml stop
docker compose -f docker/docker-compose.vps.yml --env-file .env.production up -d
