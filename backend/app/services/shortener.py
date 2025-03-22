import hashlib
import string

from backend.app.services.cache import redis_client

# Character set for base62 encoding and desired code length
CHARSET = string.ascii_letters + string.digits
BASE = len(CHARSET)
SHORT_CODE_LENGTH = 5

def base62_encode(num: int) -> str:
    """Convert an integer to a base62 string."""
    if num == 0:
        return CHARSET[0]
    encoded = []
    while num:
        num, rem = divmod(num, BASE)
        encoded.append(CHARSET[rem])
    return "".join(reversed(encoded))

def generate_hash(url: str, salt: str = "") -> str:
    """
    Generate a SHA-256 hash for the given URL (optionally salted),
    then convert it to a base62 string and return a truncated short code.
    """
    hash_input = f"{url}{salt}"
    hash_digest = hashlib.sha256(hash_input.encode("utf-8")).digest()
    # Convert the hash digest to an integer
    hash_int = int.from_bytes(hash_digest, byteorder="big")
    # Base62 encode the hash integer
    encoded = base62_encode(hash_int)
    # Truncate to the desired short code length
    return encoded[:SHORT_CODE_LENGTH]

async def check_collision(code: str) -> bool:
    """
    Check if the generated short code already exists in Redis.
    Returns True if it exists.
    """
    exists = await redis_client.exists(code)
    return exists == 1

async def store_short_code(code: str, url: str, expire: int = None) -> bool:
    """
    Store the mapping of short code to original URL in Redis.
    Optionally set an expiration time (in seconds) for the key.
    """
    return await redis_client.set(code, url, ex=expire)

async def generate_unique_short_code(url: str, max_attempts: int = 5) -> str:
    """
    Generate a unique short code for the URL. The function checks for collisions in Redis
    and uses an increasing salt value on each attempt if needed.
    """
    salt = ""
    for attempt in range(max_attempts):
        short_code = generate_hash(url, salt)
        if not await check_collision(short_code):
            await store_short_code(short_code, url)
            return short_code
        salt = str(attempt + 1)
    raise Exception("Unable to generate a unique short code after multiple attempts.")
