#!/bin/bash

ALIVE="$(ps aux | grep venv3.6 | grep python)"
echo "${ALIVE}"
if [-s "$ALIVE"] then
  echo "home.service down - restarting"
  systemctl restart home.service
else
  echo "5home.service alive - exiting"
fi
exit 0