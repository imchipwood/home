```bash
cd docker
docker-compose build home
docker run -t --device /dev/gpiomem --name homeenv_005 --privileged -d docker_home:latest
```