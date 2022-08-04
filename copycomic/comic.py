import asyncio
import json
from typing import List

from . import utils
from .chapter import Chapter


asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


semaphore = asyncio.Semaphore(30)


class Comic:

    name: str
    id: str

    def __init__(self, **kwargs):
        self.name = kwargs.get("name", "")
        self.id = kwargs.get("id", "")

    async def fetch_chapters(self) -> List[Chapter]:
        chapters = list()
        chapters_raw = await self._fetch_all()
        for raw_chapter in chapters_raw:
            chapters.append(Chapter(comic_name=self.name, comic_id=self.id, name=raw_chapter['name'], id=raw_chapter['uuid']))
        return chapters

    async def _fetch_all(self) -> List[dict]:
        dicts = list()
        async with semaphore:
            async with utils.create_session() as session:
                async with utils.get(session, 
                        f"http://api.copymanga.com/api/v3/comic/{self.id}/group/default/chapters?limit=500&offset=0&platform=3") as response:
                    if response.status != 200:
                        raise RuntimeError(f"Network problem {{code: {response.status}}}")
                    response = json.loads(await response.text())
                if response['code'] != 200:
                    raise RuntimeError(f"Network problem {{code: {response['code']}}}")
                results = response['results']
                for i in results['list']:
                    dicts.append(i)
                total = results['total']
                if total > 500:
                    times = (total // 500) - 1 if total % 500 == 0 else (total // 500)
                    for offset in range(0, times):
                        async with utils.get(session, 
                                f"http://api.copymanga.com/api/v3/comic/{self.id}/group/default/chapters?limit=500&offset={(offset + 1) * 500}&platform=3") as extra_response:
                            if extra_response.status != 200:
                                raise RuntimeError(f"Network problem {{code: {extra_response.status}}}")
                        extra_response = json.loads(await extra_response.text())
                        if extra_response['code'] != 200:
                            raise RuntimeError(f"Network problem {{code: {extra_response['code']}}}")
                        for i in extra_response['results']['list']:
                            dicts.append(i)
        return dicts

    async def download_all(self, path: str = None):
        chapters = await self.fetch_chapters()
        for chapter in chapters:
            await chapter.download(path)


def _raw_process(html) -> List[str]:
    series_raw = html.xpath("/html/body/main[@class='content-box']/div[@class='container comicParticulars-synopsis']/div[@class='upLoop']/div[@class='table-default']/div[@class='table-default-box']/div[@class='tab-content']/div/@id")
    new_series_list = list()
    for series in series_raw:
        if '全部' not in series:
            continue
        new_series_list.append(series)
    links = list()
    for series in new_series_list:
        links.append(f"/html/body/main[@class='content-box']/div[@class='container comicParticulars-synopsis']/div[@class='upLoop']/div[@class='table-default']/div[@class='table-default-box']/div[@class='tab-content']/div[@id='{series}']/ul/a")
    return links
