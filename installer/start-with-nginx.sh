#!/bin/bash
set -e
/usr/bin/start-all.sh &
exec nginx -g 'daemon off;'
