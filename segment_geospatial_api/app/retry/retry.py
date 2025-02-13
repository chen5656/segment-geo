import asyncio
from loguru import logger
from .retry_config import RETRY_CONFIG

async def retry_prediction(
    callback,
    max_retries: int = RETRY_CONFIG["max_retries"],
    delay: float = RETRY_CONFIG["initial_delay"]
):
    """
    Generic retry function with exponential backoff
    
    Args:
        callback: Async function that performs the prediction
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        
    Returns:
        Result from the callback function or None if all retries fail
    """
    for attempt in range(max_retries):
        try:
            result = await callback()
            return result
        except Exception as e:
            error_msg = str(e)
            if any(retryable_error in error_msg for retryable_error in RETRY_CONFIG["retryable_errors"]):
                if attempt < max_retries - 1:  # Don't sleep on the last attempt
                    wait_time = delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    continue
            raise e
    return None 