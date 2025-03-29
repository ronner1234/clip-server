# Dockerfile
FROM jinaai/clip-server

RUN useradd cas
RUN mkdir -p /home/cas/.cache/jina
RUN chown -R cas:cas /home/cas/.cache

USER cas:cas