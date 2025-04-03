import asyncio
from tqdm import tqdm
import random

async def load_file(start, stop):
    await asyncio.sleep(1)
    for _ in tqdm(range(start, stop), desc="Loading file", unit="lines"):
        await asyncio.sleep(0.1)
    print("File loaded successfully.")


async def main():
    # Counting to five and counting by tens concurrently
    await asyncio.gather(
        load_file(0, random.randint(1, 100)), 
        load_file(0, random.randint(1, 100)),
        load_file(0, random.randint(1, 100))
        )
    print("All tasks completed.")

if __name__ == "__main__":
    asyncio.run(main())
