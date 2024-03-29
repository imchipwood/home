#!/bin/bash

ALIVE="$(ps aux | grep -v "grep" | grep "home.py")"
if [ -z "$ALIVE" ]
then
  echo "home.service DEAD - restarting"
  eval "$(systemctl restart home.service)"
else
  echo "home.service ALIVE - exiting"
fi
exit 0
