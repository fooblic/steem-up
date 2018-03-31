#!/bin/bash
# /usr/local/bin/steem_follow.sh
#

function start {
	echo  "Steem Follow: starting service"
	python3 /usr/local/bin/steem_follow.py &
	sleep  5
	echo  "PID is $(cat /var/run/steem/steem_follow.pid)"
}

function stop {
	echo  "Steem Follow: stopping Service (PID = $(cat /var/run/steem/steem_follow.pid) )"
	kill $(cat  /var/run/steem/steem_follow.pid)
	rm  /var/run/steem/steem_follow.pid
}

function status {
	ps  -ef  |  grep steem_follow.py |  grep  -v  grep
	echo  "PID indication file $(cat /var/run/steem/steem_follow.pid 2> /dev/null) "
}

# Some Things That run always 
touch  /var/lock/steem_follow.lock

# Management instructions of the service
case "$1" in
	start )
		start
		;;
	stop )
		stop
		;;
	reload )
		stop
		sleep  1
		start
		;;
	status )
		status
		;;
	* )
	Echo  "Usage: $0 {start | stop | reload | status}"
	exit  1
	;;
esac

exit  0
