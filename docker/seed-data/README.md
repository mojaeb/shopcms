# Seed data for Docker staging (generated locally, copied to server)
#
# Create / refresh:
#   .venv\Scripts\python.exe manage.py export_docker_seed
#
# Contents:
#   data.json   — Django fixtures (all stores, products, CMS, users, …)
#   media/      — uploaded media files
#
# Deploy:
#   1. Copy this folder with the project to the test server
#   2. cp docker/.env.staging.example .env.staging  (edit secrets)
#   3. docker compose -f docker/docker-compose.staging.yml --env-file .env.staging up --build -d
