#!/bin/bash

pid=$(pgrep -u "$(whoami)" -x "rclone")
while [[ "$pid" != "1723" ]]
do
	echo "rclone running detected. Waiting 60 seconds..."
	secs=$((1 * 60))
	while [ $secs -gt 0 ]; do
		echo -ne "Remaining: $secs\033[0K\r"
		sleep 1
		: $((secs--))
	done
	pid=$(pgrep -u "$(whoami)" -x "rclone")

done

