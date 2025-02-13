# Retry configuration
RETRY_CONFIG = {
    "max_retries": 3,
    "initial_delay": 1.0,
    "retryable_errors": [
        "Failed to download satellite imagery",
        # Add other retryable error messages here
    ]
} 