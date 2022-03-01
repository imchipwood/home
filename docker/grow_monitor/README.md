```bash
cd docker
docker-compose build home
docker run -t --device /dev/gpiomem --name homeenv_005 --privileged -d docker_home:latest
```

# teamcity build setup

## general

artifact paths: `reports => reports`

set simultaneous builds to `1`

## triggers

```bash
# branch filters
## master
-:*
+:refs/heads/master
## other
+:*
-:refs/heads/master
```

## build steps

### setup venv

```bash
[ ! which rustc | grep 'cargo' ] || curl https://sh.rustup.rs -sSf | sh -s -- -y
[ -d "venv" ] || python3 -m venv venv
. venv/bin/activate
pip install --upgrade pip wheel setuptools
pip install -r requirements.txt
[ -d "reports" ] || mkdir reports
```

### run

```bash
. venv/bin/activate
coverage run -m pytest
coverage html
```

## failure conditions

* runs longer than 10 mins
* any build step exited with error
* at least one test failed
* out of memory or crash detected

### parameters

```bash
env.CRYPTOGRAPHY_DONT_BUILD_RUST=1
env.IS_TEAMCITY=TRUE
```