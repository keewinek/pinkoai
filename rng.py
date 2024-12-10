import random

def get_chance():
    return random.randint(0, 100)

def get_random_element(arr):
    return arr[random.randint(0, len(arr) - 1)]