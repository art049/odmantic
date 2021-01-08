#!/bin/bash
set -e
printf "Waiting for the configsvr "
while ! docker-compose exec -T configsvr mongo --port 27019 --eval "db.getMongo()" > /dev/null 2>&1
do
  printf "."
  sleep 1;
done
printf "OK\n"
printf "Initializing the configsvr ..."
docker-compose exec -T configsvr mongo --quiet --port 27019 /scripts/init-configsvr.js
printf "OK\n"

printf "Waiting for the router "
while ! docker-compose exec -T router mongo --eval "db.getMongo()" > /dev/null 2>&1
do
  printf "."
  sleep 1;
done
printf "OK\n"
printf "Initializing the router ..."
docker-compose exec -T router mongo --quiet /scripts/init-router.js
printf "OK\n"
