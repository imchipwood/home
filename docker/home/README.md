```bash
cd docker
docker-compose build home
docker run -t --device /dev/gpiomem -p 1883:1883 --name hometest --privileged -d docker_home:latest
```