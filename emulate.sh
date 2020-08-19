#!/bin/sh

./congaserver.py 8282 20012 &
sleep 1
firefox http://127.0.0.1:8282 &
./emulator.py 8282 20012
