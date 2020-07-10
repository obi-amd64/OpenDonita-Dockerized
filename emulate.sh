#!/bin/sh

./congaserver.py 808$1 2000$1 &
sleep 1
./emulator.py 808$1 2000$1
