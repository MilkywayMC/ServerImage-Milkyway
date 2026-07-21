#!/bin/bash
cd $(dirname $0)

docker-compose down
docker run --rm -v ./:/t alpine sh -c "chown -R 1000:1001 /t && chmod -R 775 /t"
