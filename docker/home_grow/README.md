# home_grow

Docker image that reads MQTT messages about the grow tent environment 
and logs them to an SQL database

*** 

## Dockerfile args

### branchname

name of git branch to checkout 

### cfgfilefolder

folder name with config folder to find json files

### cfgfilename

name of top level config file to load WITHOUT .json on the end


## Current build args

Just use `docker-compose home_grow`, that should handle it

***

# Viewing the database

Use something like VSCode's mssql extension and connect to the database.

The connection parameters mirror what's in the JSON DB configs pretty well:

* `hostname\instance` = `<ip addr>,<port>`
* the rest pretty much lines up