import json
import os
import azure.functions as func
import fastapi
from api import router, index_router, signalr_router
from api import utils
from api.schemas import QueueCompletion


fastapi_app = fastapi.FastAPI(
    title="Tiny LLMs API",
    description="API for Tiny (Large) Language Models.",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url=None,
)


fastapi_app.include_router(router, prefix="/api/completions", tags=["Completions"])
fastapi_app.include_router(signalr_router, prefix="/api", tags=["SignalR"])
fastapi_app.include_router(index_router, tags=["Index"])

app = func.AsgiFunctionApp(app=fastapi_app, http_auth_level=func.AuthLevel.ANONYMOUS)


@app.queue_trigger(
    arg_name="msg", queue_name="inputqueue", connection="", max_dequeue_count=1
)
async def run(msg: func.QueueMessage) -> None:
    """Run the completion command. Triggered by a message in the inputqueue."""
    completion = QueueCompletion(**json.loads(msg.get_body().decode("utf-8")))
    await utils.run_subprocess(completion.command, completion.connection_id)
