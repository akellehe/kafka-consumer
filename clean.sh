docker image rm -f producer
docker image rm -f consumer
docker image rm -f sync-http-service
docker image rm -f async-http-service
docker ps -q | xargs docker stop
