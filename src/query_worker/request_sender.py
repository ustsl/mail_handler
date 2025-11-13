import aiohttp

from src.query_worker.schema import HTTPMethod


async def send_request(
    method: HTTPMethod,
    url: str,
    headers: dict = None,
    data=None,
):
    """
    Отправляет HTTP-запрос с заданным телом.

    - Если `data` - это dict, отправляет запрос с Content-Type: application/json.
    - Если `data` - это aiohttp.FormData, отправляет как multipart/form-data.
    - В остальных случаях отправляет `data` как есть.
    """
    async with aiohttp.ClientSession() as session:
        if isinstance(data, dict):
            async with session.request(
                method, url, headers=headers, json=data
            ) as response:
                return await response.text()
        else:
            async with session.request(
                method, url, headers=headers, data=data
            ) as response:
                return await response.text()
