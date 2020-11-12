#!/bin/sh

if [ ! -z "$CONFIG_DIR" ]; then
  cd "$CONFIG_DIR"
fi

FLASK_DEBUG=true FLASK_APP=registry flask run "$@"
