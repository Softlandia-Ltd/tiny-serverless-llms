from base64 import b64encode
import json
import os
import platform
import fastapi
from fastapi import Response
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from starlette.responses import FileResponse

from api.utils import (
    generate_access_token,
)
from api.schemas import CreateCompletion
from azure.storage.queue import QueueClient


router = fastapi.APIRouter()
signalr_router = fastapi.APIRouter()

SYSTEM_PROMPT = (
    "You're a helpful assistant. Be concise and to the point, but don't omit details."
)


@signalr_router.post("/negotiate")
async def negotiate():
    url = f"{os.environ['AzureSignalRBase']}/client/?hub=llama"
    token, connection_id = generate_access_token(url)
    data = {
        "url": url,
        "accessToken": token,
        "connectionId": connection_id,
    }
    return JSONResponse(content=jsonable_encoder(data))


@router.post(
    "",
    summary="Create a completion",
    description="Creates a completion based on the given prompt with the given model",
    status_code=202,
)
async def generate(
    request: fastapi.Request,
    client_id: str,
    data: CreateCompletion,
):
    """Generate a completion based on the given prompt with the given model.
    This will send a message to the inputqueue to start the process.
    """

    full_prompt = (
        f"<|system|>{data.system_prompt}</s><|user|>{data.prompt}</s><|assistant|>"
    )

    if "llama" not in data.model:
        full_prompt = f"<|im_start|>system{data.system_prompt}<|im_end|><|im_start|>user{data.prompt}<|im_end|><|im_start|>assistant"

    command = [
        f"{os.environ['LLAMA_BASE']}main{'.exe' if platform.system() == 'Windows' else ''}",
        "-m",
        f"{os.environ['MODEL_BASE']}{data.model}.gguf",
        "-p",
        full_prompt,
    ]

    # Send the message to the queue, Python v2 function app does not seem to support output bindings for queues
    queue_client = QueueClient.from_connection_string(
        conn_str=os.environ["AzureWebJobsStorage"], queue_name="inputqueue"
    )

    try:
        queue_client.create_queue()
    except Exception:
        pass

    queue_client.send_message(
        b64encode(
            json.dumps(
                {
                    "command": command,
                    "connection_id": client_id,
                }
            ).encode("utf-8")
        ).decode("utf-8")
    )

    return Response(status_code=202)


index_router = fastapi.APIRouter()


@index_router.get("/")
async def read_index():
    path = os.path.abspath(os.path.dirname(__file__))
    return FileResponse(path + "/index.html")
