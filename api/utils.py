import asyncio
import logging
import os
import platform
import shlex
import subprocess
import time
import uuid
import aiohttp
import jwt
import logging

message_queue = asyncio.Queue[dict[str, str]]()


async def send_messages():
    while True:
        item = await message_queue.get()
        if item:
            await send_message_to_user(item)
            message_queue.task_done()


async def send_message_to_user(data: dict[str, str]) -> None:
    url = f"{os.environ['AzureSignalRBase']}/api/v1/hubs/llama/connections/{data['connection_id']}"
    token, _ = generate_access_token(url)

    async with aiohttp.ClientSession() as session:
        await session.post(
            url,
            headers={"Authorization": f"Bearer {token}"},
            json={
                "target": "SendMessage",
                "arguments": [data["message"]],
            },
        )


async def read_stream(
    stream: asyncio.StreamReader,
    prompt: str,
    connection_id: str,
) -> None:
    """Read the stream and send messages to the user."""

    buffer = b""
    generated = ""
    prompt_finished = False
    chunk = await stream.read(1)
    batch = ""
    start_time = time.time()
    byte_count = 0
    batch_size = 4  # Initial batch size
    last_measurement_time = start_time

    await message_queue.put(
        {
            "connection_id": connection_id,
            "message": "Model loaded, generating completion.",
        }
    )

    await message_queue.put(
        {
            "connection_id": connection_id,
            "message": "START",
        }
    )

    while True:
        buffer += chunk

        if not prompt_finished:
            # https://github.com/ggerganov/llama.cpp/issues/2664
            stripped = generated.lstrip()
            if stripped.startswith(
                prompt.replace("</s>", "")
                .replace("<|im_end|>", "")
                .replace("<|im_start|>", "")
            ):
                prompt_finished = True

        try:
            decoded = buffer.decode()
            buffer = b""
            generated += decoded

            if prompt_finished:
                byte_count += len(decoded)
                batch += decoded

                if len(batch) >= batch_size:
                    message_queue.put_nowait(
                        {"connection_id": connection_id, "message": batch}
                    )
                    batch = ""

                current_time = time.time()
                elapsed_time = current_time - last_measurement_time

                if elapsed_time >= 1:
                    bytes_per_second = byte_count / elapsed_time
                    batch_size = max(4, int(bytes_per_second))
                    byte_count = 0
                    last_measurement_time = current_time

        except UnicodeDecodeError:
            pass

        except Exception as e:
            logging.error(f"Error reading stream: {e}")
            break

        try:
            # In the consumption plan, the generation might get stuck
            # -> wait for a while and then exit
            chunk = await asyncio.wait_for(stream.readexactly(1), timeout=10)
        except asyncio.TimeoutError:
            logging.info(f"Timeout reading stream")
            message_queue.put_nowait({"connection_id": connection_id, "message": batch})
            break
        except asyncio.IncompleteReadError as e:
            logging.info(f"Incomplete read: {e}")
            message_queue.put_nowait({"connection_id": connection_id, "message": batch})
            break

    message_queue.put_nowait({"connection_id": connection_id, "message": "DONE"})
    await message_queue.join()
    logging.info(f"Stream finished")


async def run_subprocess(command: list[str], connection_id: str) -> None:
    logging.info(f"Running subprocess")

    messages = asyncio.create_task(send_messages())

    try:
        if platform.system() == "Windows":
            safe_command = subprocess.list2cmdline(command)
        else:
            safe_command = " ".join(shlex.quote(arg) for arg in command)

        logging.info(f"Running command: {safe_command}")

        message_queue.put_nowait(
            {
                "connection_id": connection_id,
                "message": "Loading model, please wait...\n",
            }
        )

        p = await asyncio.create_subprocess_shell(
            safe_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        if p.stdout is None or p.stderr is None:
            logging.error("Subprocess failed to start")
            return

        task = asyncio.create_task(read_stream(p.stdout, command[-1], connection_id))

        logging.info(f"Waiting for stream to finish...")

        await task

        logging.info(f"Stream finished")
        logging.info(f"Closing message queue...")

        messages.cancel()
        await asyncio.gather(messages, task, return_exceptions=True)

        logging.info(f"All done")

    except Exception as e:
        logging.error(f"Subprocess failed: {e}")


def generate_access_token(url: str) -> tuple[str, str]:
    name_id = str(uuid.uuid4())
    token = jwt.encode(
        {"aud": url, "exp": time.time() + 3600, "nameid": name_id},
        os.environ["AzureSignalRAccessKey"],
        algorithm="HS256",
    )
    return token, name_id
