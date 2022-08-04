
from aiohttp import ClientSession, TCPConnector
from aiohttp.client import _RequestContextManager


def create_session() -> ClientSession:
    session = ClientSession(connector=TCPConnector(ssl=False))
    session.headers.add("user-agent",
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.72 Safari/537.36")
    return session


def get(session: ClientSession, url: str) -> _RequestContextManager:
    #return session.get(url, proxy="http://127.0.0.1:7890") If you cannot download the comic, using this instaed of below
    return session.get(url)
