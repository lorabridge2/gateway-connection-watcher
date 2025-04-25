import json
import os
import threading
import traceback

import grpc
import redis
from chirpstack_api import api

CHIRP_HOST = os.environ.get("CHIRP_HOST", "chirpstack")
CHIRP_PORT = int(os.environ.get("CHIRP_PORT", 8080))
DEV_EUI = os.environ.get("DEV_EUI").removeprefix(r"\x")

REDIS_LAST_SEEN = "lorabridge:connection:last_seen"


def check_connection():
    threading.Timer(60.0, check_connection).start()
    try:
        resp = api.DeviceServiceStub(channel).List(ld_req, metadata=auth_token)
    except grpc.RpcError:
        print(traceback.format_exc())
        os._exit(1)

    for dev in resp.result:
        if dev.dev_eui == DEV_EUI.lower():
            redis_client.set(REDIS_LAST_SEEN, dev.last_seen_at.seconds)


channel = grpc.insecure_channel(f"{CHIRP_HOST}:{CHIRP_PORT}")

token = ""
with open("/token/token.json") as tfile:
    token = json.loads(tfile.read())["token"]

auth_token = [("authorization", f"Bearer {token}")]

app_id = ""
with open(f"/device/{DEV_EUI.lower()}.json") as dfile:
    app_id = json.loads(dfile.read())["application_id"]

ld_req = api.ListDevicesRequest()
ld_req.application_id = app_id
ld_req.offset = 0
ld_req.limit = 100

redis_client = redis.Redis(
    host=os.environ.get("REDIS_HOST", "localhost"),
    port=int(os.environ.get("REDIS_PORT", 6379)),
    db=int(os.environ.get("REDIS_DB", 0)),
    decode_responses=True,
)

check_connection()
