# CopycomicSpider
A library can fetch comics on Copycomic

### 2022.8.23 Updated, it seems that the api link won't return chapters now, it will return an empty array, I'll find the way to solve it

## Example
```python
import asyncio

from copycomic import search


async def main():
    dont_be_brother_anymore = await search.fetch_comic(str("biedangounijiangle")) # 别当欧尼酱了, fetch the comic by its id
    chapters = await dont_be_brother_anymore.fetch_chapters() # Fetch all the chapters
    for chapter in chapters: # For each
        await chapter.download() # Download


if __name__ == "__main__":
    event_loop = asyncio.get_event_loop() or asyncio.new_event_loop()
    event_loop.run_until_complete(main())


```