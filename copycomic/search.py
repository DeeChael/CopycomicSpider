import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import List

from lxml import etree

from . import utils
from .comic import Comic
from .interface import Category


asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


semaphore = asyncio.Semaphore(30)


class Result(ABC):

    @abstractmethod
    async def list_comics(self, page: int) -> List[Comic]:
        pass


class RecommendResult(Result):

    total_page: int = 1

    def __init__(self, **kwargs):
        self.total_page = kwargs.get("total", 1)

    async def list_comics(self, page: int = 1) -> List[Comic]:
        if page < 1:
            raise ValueError("Page cannot be lower than 1")
        if page > self.total_page:
            raise ValueError("Page cannot be bigger than the max_page")
        comics = list()
        async with semaphore:
            async with utils.create_session() as session:
                async with utils.get(session, 
                        f"http://www.copymanga.site/recommend?type=3200102&offset={60 * (page - 1)}&limit=60") as response:
                    if response.status != 200:
                        raise RuntimeError(f"Network problem {{code: {response.status}}}")
                    html = etree.HTML(await response.text())
                    ids = html.xpath(
                        "/html/body/main[@class='content-box']/div[@class='container correlationList']/div[@class='tab-content']/div[@id='comic']/div[@class='row']/div[@class='col-auto exemptComic_Item']/div[@class='exemptComicItem-txt-box']/div[@class='exemptComicItem-txt']/a/@href")
                    names = html.xpath(
                        "/html/body/main[@class='content-box']/div[@class='container correlationList']/div[@class='tab-content']/div[@id='comic']/div[@class='row']/div[@class='col-auto exemptComic_Item']/div[@class='exemptComicItem-txt-box']/div[@class='exemptComicItem-txt']/a/p/text()")
                    if len(ids) != len(names):
                        raise ValueError("Amount error")
                    for i in range(0, len(ids)):
                        comics.append(Comic(id=ids[i][7:], name=names[i]))
        return comics


class LeaderboardResult(Result):

    async def list_comics(self, page: int) -> List[Comic]:
        comics = list()
        async with semaphore:
            async with utils.create_session() as session:
                async with utils.get(session, "http://copymanga.site/rank") as response:
                    if response.status != 200:
                        raise RuntimeError(f"Network problem {{code: {response.status}}}")
                    html = etree.HTML(await response.text())
                    ids = html.xpath(
                        "/html/body/main[@class='content-box']/div[@class='container ranking-box']/ul[@class='ranking-all row']/li[@class='col-4']/div[@class='topThree ranking-all-box']/div[@class='ranking-all-topThree']/div[@class='ranking-all-topThree-txt']/a/@href")
                    names = html.xpath(
                        "/html/body/main[@class='content-box']/div[@class='container ranking-box']/ul[@class='ranking-all row']/li[@class='col-4']/div[@class='topThree ranking-all-box']/div[@class='ranking-all-topThree']/div[@class='ranking-all-topThree-txt']/a/p[@class='threeLines']/text()")
                    if len(ids) != len(names):
                        raise ValueError("Amount error")
                    for i in range(0, len(ids)):
                        comics.append(Comic(id=ids[i][7:], name=names[i]))
        return comics


class CategoryResult(Result):

    category: Category
    total_page: int = 1

    def __init__(self, category: Category, **kwargs):
        self.category = category
        self.total_page = kwargs.get("total", 1)

    async def list_comics(self, page: int = 1) -> List[Comic]:
        if page < 1:
            raise ValueError("Page cannot be lower than 1")
        if page > self.total_page:
            raise ValueError("Page cannot be bigger than the max_page")
        comics = list()
        async with semaphore:
            async with utils.create_session() as session:
                async with utils.get(session, 
                        f"http://copymanga.site/comics?theme={self.category.value}&offset={50 * (page - 1)}&limit=50") as response:
                    if response.status != 200:
                        raise RuntimeError(f"Network problem {{code: {response.status}}}")
                    html = etree.HTML(await response.text())
                    ids = html.xpath(
                        "/html/body/main[@class='content-box']/div[@class='container exemptComicList']/div[@class='row']/div[@class='col-10']/div[@class='row exemptComic-box']/div[@class='col-auto exemptComic_Item']/div[2]/div[@class='exemptComicItem-txt']/a/@href")
                    names = html.xpath(
                        "/html/body/main[@class='content-box']/div[@class='container exemptComicList']/div[@class='row']/div[@class='col-10']/div[@class='row exemptComic-box']/div[@class='col-auto exemptComic_Item']/div[2]/div[@class='exemptComicItem-txt']/a/p/text()")
                    if len(ids) != len(names):
                        raise ValueError("Amount error")
                    for i in range(0, len(ids)):
                        comics.append(Comic(id=ids[i][7:], name=names[i]))
        return comics


class SearchResult(Result):

    keyword: str
    total_page: int = 1

    def __init__(self, **kwargs):
        self.keyword = kwargs.get("keyword", "")
        self.total_page = kwargs.get("total", 1)

    async def list_comics(self, page: int) -> List[Comic]:
        pass


async def fetch_recommend() -> RecommendResult:
    logging.debug("Trying to fetch recommended comics")
    async with semaphore:
        async with utils.create_session() as session:
            async with utils.get(session, 
                    f"http://www.copymanga.site/recommend") as response:
                if response.status != 200:
                    raise RuntimeError(f"Network problem {{code: {response.status}}}")
                html = etree.HTML(await response.text())
                pages = html.xpath(
                    "/html/body/main[@class='content-box']/div[@class='container']/ul[@class='page-all']/li[@class='page-total'][2]/text()")[
                            0][1:]
                logging.debug(f"Recommended total pages: {pages}")
                return RecommendResult(total=int(pages))


def fetch_leaderboard() -> LeaderboardResult:
    logging.debug("Trying to fetch leaderboard comics")
    return LeaderboardResult()


async def fetch_category(category: Category) -> CategoryResult:
    logging.debug(f"Trying to fetch comics by category {category.value}")
    async with semaphore:
        async with utils.create_session() as session:
            async with utils.get(session, 
                    f"http://copymanga.site/comics?theme={category.value}") as response:
                if response.status != 200:
                    raise RuntimeError(f"Network problem {{code: {response.status}}}")
                html = etree.HTML(await response.text())
                pages = html.xpath(
                    "/html/body/main[@class='content-box']/div[@class='container']/ul[@class='page-all']/li[@class='page-total'][2]/text()")[
                            0][1:]
                return CategoryResult(category=category, total=int(pages))


async def search(keyword: str):
    logging.debug(f"Trying to search keyword {keyword}")
    async with semaphore:
        async with utils.create_session() as session:
            async with utils.get(session, 
                    f"https://api.copymanga.site/api/v3/search/comic?format=json&limit=20&offset=0&platform=3&q={keyword}") as response:
                if response.status != 200:
                    raise RuntimeError(f"Network problem {{code: {response.status}}}")
                response = json.loads(await response.text())
            if response['code'] != 200:
                raise RuntimeError(f"Network problem {{code: {response['code']}}}")
            results = response['results']
            totals = results['total']
            logging.debug(f"Search results: {totals}")
            return SearchResult(keyword=keyword, total=totals // 20 if totals % 20 == 0 else totals // 20 + 1)
    ...


async def fetch_comic(id: str) -> Comic:
    logging.debug(f"Trying to fetch comic by id {id}")
    async with semaphore:
        async with utils.create_session() as session:
            async with utils.get(session, "http://copymanga.site/comic/" + id) as response:
                if response.status != 200:
                    raise RuntimeError(f"Network problem {{code: {response.status}}}")
                html = etree.HTML(await response.text())
                name = html.xpath(
                    "/html/body/main[@class='content-box']/div[@class='container comicParticulars-title']/div[@class='row']/div[@class='col-9 comicParticulars-title-right']/ul/li[1]/h6/text()")[
                    0]
                logging.debug(f"Fetched comic: id={id}, name={name}")
                return Comic(id=id, name=name)
