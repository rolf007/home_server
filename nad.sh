#!/bin/sh
if [ "$1" = "start" ]; then
	screen -dmS stream_receiver "stream_receiver/stream_receiver.py"
	screen -dmS led "led/led.py"
	screen -dmS radio "keypress/raspberry_radio.py"
	screen -ls
elif [ "$1" = "stop" ]; then
	for line in $(screen -ls | grep "(Detached)" | sed -e 's/\s*\(\S\+\)\s.*/\1/'); do
		echo stopping $line
		pid=$(echo "$line" | sed -e 's/^\s*\([0-9]\+\)\..*$/\1/g')
		screen -S $pid -X quit
	done
	screen -ls
else
	echo usage: $0 {start\|stop}
fi
# list all:
# screen -ls

# reattach example:
# screen -r emoji

