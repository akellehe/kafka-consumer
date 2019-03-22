docker image rm -f producer
docker image rm -f consumer
docker ps -q | xargs docker stop
