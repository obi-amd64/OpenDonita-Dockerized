#!/bin/sh

./congaserver.py 828$1 2000$1 &
sleep 1
./emulator.py 828$1 2000$1
