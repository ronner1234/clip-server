from clip_client import Client
import os

os.environ["GRPC_ARG_KEEPALIVE_TIME_MS"] = "60000"  # Ping every 60 seconds
os.environ["GRPC_ARG_KEEPALIVE_TIMEOUT_MS"] = "20000"  # Wait 20 seconds for response

c = Client('grpc://2.tcp.ngrok.io:15915')
c.profile()


