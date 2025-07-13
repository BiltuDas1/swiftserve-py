#!/bin/sh
# If running in Docker and the Auto IP detection is on, then detect IP
if [ $DOCKER -eq 1 ] && [ $AUTO_DETECT_IP -eq 1 ]; then
  export MACHINE_IP=$(awk 'END{print $1}' /etc/hosts)
fi

if [ $DEBUG -eq 1 ]; then
  python manage.py runserver "0.0.0.0:$PORT"
else
  gunicorn swiftserve.wsgi:application --bind "$MACHINE_IP:$PORT"
fi