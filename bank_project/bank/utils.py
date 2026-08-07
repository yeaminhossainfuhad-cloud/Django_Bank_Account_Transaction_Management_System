import random

def generate_account_number():
    """Generate a random 10-digit account number."""
    return str(random.randint(10**9, 10**10 - 1))