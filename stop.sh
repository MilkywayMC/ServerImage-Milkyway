#!/bin/bash
cd "$(dirname "$0")" || exit 1

# 権限は、次の起動のときに compose の init-chown が main/ だけを直す (o-rwx)
docker-compose down
