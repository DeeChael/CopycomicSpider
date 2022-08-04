import asyncio
import json
import logging
import os
from io import BytesIO

from PIL import Image

from . import utils

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


semaphore = asyncio.Semaphore(30)


class Chapter:
    comic_name: str
    comic_id: str
    name: str
    id: str

    def __init__(self, **kwargs):
        self.comic_name = kwargs.get("comic_name", "")
        self.comic_id = kwargs.get("comic_id", "")
        self.name = kwargs.get("name", "")
        self.id = kwargs.get("id", "")

    async def download(self, path: str = None):
        if path is None:
            path = self.comic_name
        path += "/" + self.name
        if not os.path.exists(path):
            os.makedirs(path)
        if not os.path.isdir(path):
            raise TypeError("The path is not a directory")
        logging.debug(f"Trying to download: {self.comic_name} - {self.name}")
        async with semaphore:
            async with utils.create_session() as session:
                async with utils.get(session, f"http://api.copymanga.com/api/v3/comic/{self.comic_id}/chapter2/{self.id}?platform=3") as response:
                    if response.status != 200:
                        raise RuntimeError(f"Network problem {{code: {response.status}}}")
                    response = json.loads(await response.text())
                if response['code'] != 200:
                    raise RuntimeError(f"Network problem {{code: {response['code']}}}")
                pic_links = list()
                for content in response['results']['chapter']['contents']:
                    pic_links.append(content['url'])
                index = 1
                for pic_link in pic_links:
                    async with session.get(pic_link) as pic_response:
                        if pic_response.status != 200:
                            raise RuntimeError(f"Network problem {{code: {pic_response.status}}}")
                        bytes = await pic_response.read()
                    image = Image.open(BytesIO(bytes), mode='r')
                    image.save(path + "/" + str(index) + ".png")
                    logging.debug(f"    Downloaded: {self.comic_name} - {self.name} - Page {index}")
                    index += 1
