#!/bin/bash
echo Starting...
cd /home/pi/catfeeder_local

python appli_v2.py 2>&1 | tee  log.log

