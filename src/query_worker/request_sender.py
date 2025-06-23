# src/query_worker/request_sender.py

import json  # <-- Добавлен импорт

import aiohttp

from src.query_worker.schema import HTTPMethod


async def send_request(
    method: HTTPMethod,
    url: str,
    headers: dict = None,
    body=None,
    attachments: list[tuple[str, bytes]] | None = None,
    attachment_field: str = 'file'
):
    """
    Отправляет HTTP-запрос.
    - Если переданы `attachments`, формирует multipart/form-data запрос.
    - В multipart-запросе `body` (если он есть) отправляется как поле 'payload'.
    """
    async with aiohttp.ClientSession() as session:
        request_headers = headers.copy() if headers else {}

        if attachments:
            data = aiohttp.FormData()

            if body:
                payload_data = json.dumps(body) if isinstance(body, dict) else str(body)
                data.add_field("payload", payload_data, content_type="application/json" if isinstance(body, dict) else "text/plain")

            for filename, file_data in attachments:
                data.add_field(
                    attachment_field, 
                    file_data,
                    filename=filename,
                    content_type="application/octet-stream", 
                )
            
            request_headers.pop('Content-Type', None)

            async with session.request(
                method, url, headers=request_headers, data=data
            ) as response:
                return await response.text()
        
        else:
            if isinstance(body, dict):
                async with session.request(
                    method, url, headers=headers, json=body
                ) as response:
                    return await response.text()
            else:
                async with session.request(
                    method, url, headers=headers, data=body
                ) as response:
                    return await response.text()