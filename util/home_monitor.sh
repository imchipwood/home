#!/bin/bash

ALIVE="$(ps aux | grep -v "grep" | grep python)"
if [ -z "$ALIVE" ]
then
  echo "\nhome.service down - restarting"
  eval "$(systemctl restart home.service)"
else
  echo "\nhome.service alive - exiting"
fi
exit 0
