### Restart on Server

docker compose -f docker/docker-compose.yml stop
docker compose -f docker/docker-compose.vps.yml --env-file .env.production up -d



cd ~/shopcms
git pull
docker build -t shopcms:latest -f docker/Dockerfile .
docker compose -f docker/docker-compose.vps.yml --env-file .env.production up -d --force-recreate --pull never