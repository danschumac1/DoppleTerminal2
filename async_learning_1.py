import asyncio

async def count_to_five(num):
    await asyncio.sleep(1)
    print(num)

async def count_by_tens(num):
    await asyncio.sleep(1)
    print(f"\t{num}")

async def count_squares(num):
    await asyncio.sleep(1)
    print(f"\t\t{num * num}")

async def main():
    # Counting to five and counting by tens concurrently
    for i in range(1, 6):
        await asyncio.gather(
            count_to_five(i), 
            count_by_tens(i * 10),
            count_squares(i)
            )
    print("All tasks completed.")

if __name__ == "__main__":
    asyncio.run(main())
