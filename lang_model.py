from model import *
from interfaces.model_like import *
import load_model
import create_model

ALPHABET = "abcdefghijklmnopqrstuvwxyz"
DEFAULT_CHARSET = ALPHABET.upper() + ALPHABET + "0123456789" + ",.?!-+="

class LangModel:
    def __init__(self, model):
        self.model = model
        self.charset = ""
        self.load_charset()
    
    def load_charset(self):
        self.charset = self.model.init_line.split(':')[2]

    def str_to_locs(self, str):
        locs = []
        for i in range(len(str)):
            locs.append(self.charset.index(str[i]) + (i * len(self.charset)))
        
        return locs

    def locs_to_str(self, locs):
        str = ""
        for i in range(len(locs)):
            str += self.charset[locs[i] % len(self.charset)]

        return str

    def get_response(self, input):
        locs = self.str_to_locs(input)
        out = self.model.get_response(locs)
        return self.locs_to_str(out)

def load_from_file(name):
    return LangModel(load_model.get_model_by_name(name))

def create_empty_language_model(name, charset, max_input_chars, levels):
    top_pins_count = len(charset) * max_input_chars
    create_model.create_empty_model(name, top_pins_count, levels, f"MDL:LANG:{charset}")
    return load_from_file(name)