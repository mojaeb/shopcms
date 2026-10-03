### Restart on Server

docker compose -f docker/docker-compose.yml down

cp .env.example .env

docker compose -f docker/docker-compose.yml up --build
