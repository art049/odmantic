#!/bin/bash
set -e
printf "Waiting for an instance ."
while ! docker-compose exec -T mongo0 mongo --eval "db.getMongo()" > /dev/null 2>&1
do
  printf "."
  sleep 1;
done
printf "OK\n"

printf "Initializing the replicaset ..."
docker-compose exec -T mongo0 mongo --quiet /scripts/init.js
printf "OK\n"
