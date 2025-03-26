from src.query_worker.schema import HTTPMethod
import aiohttp


async def send_request(method: HTTPMethod, url: str, headers: dict = None, body=None):

    async with aiohttp.ClientSession() as session:
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
