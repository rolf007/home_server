#!/bin/sh
if [ "$1" = "start" ]; then
	screen -dmS stream_receiver "stream_receiver/stream_receiver.py"
	screen -dmS led "led/led.py"
	screen -dmS radio "keypress/radio.py"
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
#screen -ls

# reattach example:
#screen -r emoji

# add these lines near the end of /etc/rc.local
#cd /home/pi/home_server
#/usr/bin/sudo -s -u pi ./nad.sh start
