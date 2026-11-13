import time
from functools import wraps
# from app.evaluation.timing import measure_latency


# @measure_latency
# async def generate_customer_answer(message, db):
#     # Call your existing AI service here.
#     ...

def measure_latency(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()

        try:
            return await func(*args, **kwargs)

        finally:
            elapsed = (
                time.perf_counter() - start
            ) * 1000

            print(
                f"{func.__name__} latency: "
                f"{elapsed:.2f} ms"
            )

    return wrapper