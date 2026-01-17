#!/bin/bash

set -e

# Default values
MODE="${MODE:-standalone}"
VERSION="${VERSION:-latest}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "$MODE" == "standalone" ]]; then
  echo "Creating a standalone MongoDB instance"
  docker run --name odmantic-mongo-test \
    -p 27017:27017 \
    -d mongo:${VERSION}
  MONGOCSTRING='mongodb://localhost:27017/'
elif [[ "$MODE" == "replicaSet" ]]; then
  echo "Creating a ReplicaSet MongoDB cluster"
  cd "$SCRIPT_DIR/replica"
  export VERSION
  docker compose up -d
  echo "Initializing the replicaSet"
  ./start.sh
  MONGOCSTRING='mongodb://172.16.17.11:27017,172.16.17.12:27017,172.16.17.13:27017/?replicaSet=mongodb-action-replica-set'
elif [[ "$MODE" == "sharded" ]]; then
  echo "Creating a Sharded MongoDB cluster"
  cd "$SCRIPT_DIR/sharded"
  export VERSION
  docker compose up -d
  echo "Initializing the sharded cluster"
  ./start.sh
  MONGOCSTRING='mongodb://172.16.17.10:27017/?retryWrites=false'
else
  echo "Unknown service mode: $MODE"
  exit 1
fi

echo "Service: $MONGOCSTRING"
echo "connection-string=$MONGOCSTRING"
