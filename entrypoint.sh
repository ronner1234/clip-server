#!/bin/sh

# Fix permissions inside the container
mkdir -p /home/cas/.cache/jina
chown -R cas:cas /home/cas/.cache

# Pipe config into the server
cat /my.yml | python -m clip_server -i
