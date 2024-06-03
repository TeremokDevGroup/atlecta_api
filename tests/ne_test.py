import asyncio
import json

from src.repository import JsonRepository
from src.sports.schemas import Sport

repo = JsonRepository(Sport)


async def test():
    res = await repo.get_single(id=1)
    print(res)
    print("Done")
    return res

asyncio.run(test())
