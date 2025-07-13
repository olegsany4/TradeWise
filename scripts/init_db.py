import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from db.init_db import init_db

async def main():
    await init_db()

if __name__ == "__main__":
    asyncio.run(main())
