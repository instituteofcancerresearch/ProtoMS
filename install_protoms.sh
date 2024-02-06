#!/bin/bash

CURRENT_DIR="$(dirname -- "${BASH_SOURCE[0]}")" # relative
CURRENT_DIR="$(cd -- "$CURRENT_DIR" && pwd)" # absolute and normalized
if [[ -z "$CURRENT_DIR" ]] ; then
  exit 1
fi

source $CURRENT_DIR/protoms_env.sh

read -p "Enter 'y' to install with this configuration: " USER_RESPONSE

if [ "$USER_RESPONSE" == "y" ]; then

  export PROTOMS_BUILD="$CURRENT_DIR/build"

  if [ ! -d "$PROTOMS_BUILD" ]; then
    mkdir "$PROTOMS_BUILD"
  fi

  cd "$PROTOMS_BUILD" || exit

  cmake .. -DPYTHON_EXECUTABLE="$CURRENT_DIR"/venv/bin/python

  if [ $? -eq 0 ]; then
    echo "cmake ran successfully ! Running installation..."
    make install

    if [ $? -eq 0 ]; then
      echo "make install ran successfully !"
      pip show protomslib
    fi

  fi

fi
