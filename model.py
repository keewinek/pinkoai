from interfaces.model_like import ModType
from model_calculate import get_next_locs

class Model:
    def __init__(self,  name):
        self.name = ""
        self.init_line = ""
        self.levels = []

    def __str__(self):
        return f"Model: {self.name}\n{self.init_line}\n{self.levels}"

    def get_response(self, start_locs):
        curr_locs = start_locs

        for i in range(len(self.levels)):
            curr_locs = get_next_locs(curr_locs, self.levels[i])
            print(f"Level {i}: {curr_locs}")

        return curr_locs