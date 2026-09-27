import random

# Uniform float in [0, 100), so `get_chance() < p` is true exactly p% of the time
def get_chance():
    return random.random() * 100

def get_random_element(arr):
    return arr[random.randint(0, len(arr) - 1)]