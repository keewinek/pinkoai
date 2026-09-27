"""PinkoAI Creative - a text-writing AI built out of Plinko boards.

How it thinks
-------------
Every context (the last few characters written) owns a Galton/Plinko board.
A single ball is dropped at the top-left of the board and bounces down through
`len(charset) - 1` rows of ChanceWay pins. The slot it lands in is the next
character. Training does not touch any randomness - it only tilts the pins:

    Given how often each character followed a context in the corpus, every pin
    (row l, column x) gets the exact chance of bouncing right that makes the
    ball land in slot y as often as the corpus says. For a ball sitting at
    (l, x) the chance is the share of "still reachable" landing slots that
    need one more right bounce:

        P(right | l, x) = sum_y q(y) * C(L-l-1, y-x-1) / C(L, y)
                          -----------------------------------------
                          sum_y q(y) * C(L-l,   y-x)   / C(L, y)

    With those pins the board reproduces the distribution q exactly.

    q is not the raw counts of one context: a context seen only a couple of
    times would be far too sure of itself. Each board blends its own counts
    with the board of the next-shorter context (Witten-Bell smoothing), down
    to an even spread over every character:

        q_ctx(c) = (count_ctx(c) + T * q_shorter(c)) / (total_ctx + T)

    where T is how many different characters ever followed the context.

How it creates
--------------
Creativity is one knob (0 = stays close to the corpus, 1 = wild poet) that drives two
very Plinko-like effects:

  * chaos - pins are loosened (their odds are pulled towards 50/50), so a
    ball sometimes slips into a neighbouring slot. The charset is ordered so
    that neighbours are similar (vowel next to vowel, consonant next to
    consonant), which makes slips produce new-but-pronounceable words.
  * leaps - now and then the ball is dropped into the board of a *shorter*
    context. Less memory means less copying and more surprising turns.
"""

import argparse
import json
import math
import os
import random
import re
import sys

from interfaces.model_like import Level, ModType, Pin
from model_calculate import get_next_locs

MODELS_DIR = "models"
INIT_PREFIX = "MDL:CREATIVE"

MIN_PIN_CHANCE = 1e-9

# Contexts this short are always kept; longer ones need `min_count` sightings
ALWAYS_KEEP_CONTEXT = 3

# Leaps never forget more than this: shorter contexts produce gibberish
MIN_LEAP_CONTEXT = 2

VOWELS = "aeiouyAEIOUY"
WORD_RE = re.compile(r"[a-z']+")


def char_group(c):
    if c.isspace():
        return 0
    if not c.isalnum():
        return 1
    if c.isdigit():
        return 5
    if c in VOWELS:
        return 2 if c.islower() else 4
    return 3 if c.islower() else 4


def chaos_for(creativity):
    """How loose the pins are: < 1 tightens them, > 1 pulls them towards 50/50."""
    return 0.9 + 0.5 * creativity


def order_charset(chars):
    """Order slots so that neighbouring slots hold similar characters."""
    return "".join(sorted(set(chars), key=lambda c: (char_group(c), c.lower(), c)))


def words_of(text):
    return {w.strip("'") for w in WORD_RE.findall(text.lower())} - {""}


class LazyPins:
    """A row of pins that are only worked out when a ball actually hits them."""

    def __init__(self, board, y):
        self.board = board
        self.y = y

    def __len__(self):
        return self.y + 1

    def __getitem__(self, x):
        pin = Pin(x, self.y)
        pin.mod_type = ModType.ChanceWay
        pin.mod_value = self.board.right_chance(self.y, x)
        return pin


class Board:
    """A Plinko board whose landing slots are the characters of a charset."""

    def __init__(self, probs, chaos=1.0):
        """`probs[y]` is how often the ball should land in slot y (sums to 1)."""
        self.slots = len(probs)
        self.rows = self.slots - 1
        self.chaos = chaos

        L = self.rows
        # Weight of every landing slot divided by the number of paths leading to it
        self.weights = [probs[y] / math.comb(L, y) for y in range(self.slots)]
        self.comb = [[float(math.comb(n, k)) for k in range(L + 1)] for n in range(L + 1)]
        self.pin_cache = {}
        self.levels = [Level(y, LazyPins(self, y)) for y in range(L)]

    def _paths(self, n, k):
        if k < 0 or k > n:
            return 0.0
        return self.comb[n][k]

    def right_chance(self, l, x):
        """Chance (0-100) that a ball hitting pin (row l, column x) bounces right."""
        key = (l, x)
        if key in self.pin_cache:
            return self.pin_cache[key]

        L = self.rows
        right = 0.0
        through = 0.0
        for y in range(x, self.slots):
            w = self.weights[y]
            through += w * self._paths(L - l, y - x)
            right += w * self._paths(L - l - 1, y - x - 1)

        p = right / through if through > 0 else 0.5
        p = min(max(p, MIN_PIN_CHANCE), 1 - MIN_PIN_CHANCE)
        if self.chaos != 1.0:
            # Loosen (chaos > 1) or tighten (chaos < 1) the pin
            logit = math.log(p / (1 - p)) / self.chaos
            p = 1 / (1 + math.exp(-logit))

        chance = p * 100
        self.pin_cache[key] = chance
        return chance

    def drop(self):
        """Drop one ball from the top-left and return the slot it lands in."""
        locs = [0]
        for level in self.levels:
            locs = get_next_locs(locs, level)
        return locs[0]


class CreativeModel:
    def __init__(self, name, charset, order, counts, vocab):
        self.name = name
        self.charset = charset
        self.order = order
        # context string -> {next char: times seen}
        self.counts = counts
        self.vocab = vocab
        self.slot_of = {c: i for i, c in enumerate(charset)}
        self.dist_cache = {}
        self.board_cache = {}

    # ---- training ---------------------------------------------------------

    @classmethod
    def train(cls, name, text, order=6, min_count=3):
        """Count what follows every context of up to `order` characters.

        Contexts longer than ALWAYS_KEEP_CONTEXT seen fewer than `min_count`
        times are dropped: their board would just be a noisy copy of the
        shorter context's, and the model file gets much smaller.
        """
        if order < 1:
            raise ValueError("order must be at least 1")
        if len(text) < 2:
            raise ValueError("training text is too short")

        charset = order_charset(text)
        counts = {}
        for i in range(len(text)):
            nxt = text[i]
            for k in range(0, order + 1):
                if k > i:
                    break
                ctx = text[i - k:i]
                table = counts.setdefault(ctx, {})
                table[nxt] = table.get(nxt, 0) + 1

        counts = {ctx: table for ctx, table in counts.items()
                  if len(ctx) <= ALWAYS_KEEP_CONTEXT or sum(table.values()) >= min_count}
        return cls(name, charset, order, counts, sorted(words_of(text)))

    # ---- persistence ------------------------------------------------------

    def save(self, overwrite=False):
        os.makedirs(MODELS_DIR, exist_ok=True)
        filepath = model_path(self.name)
        if os.path.exists(filepath) and not overwrite:
            raise Exception(f"Model {self.name} already exists (use --overwrite)")

        body = {"charset": self.charset, "counts": self.counts, "vocab": self.vocab}
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"{INIT_PREFIX}:{self.order}\n")
            json.dump(body, f, ensure_ascii=False, separators=(",", ":"))
        return filepath

    @classmethod
    def load(cls, name):
        with open(model_path(name), "r", encoding="utf-8") as f:
            init_line = f.readline().strip()
            if not init_line.startswith(INIT_PREFIX + ":"):
                raise Exception(f"{name} is not a creative model (init line: {init_line})")
            body = json.load(f)
        order = int(init_line.split(":")[2])
        return cls(name, body["charset"], order, body["counts"], body["vocab"])

    # ---- thinking ---------------------------------------------------------

    def distribution(self, context):
        """Landing chances for every slot after `context`, blended with shorter contexts."""
        if context in self.dist_cache:
            return self.dist_cache[context]

        if context == "":
            shorter = [1 / len(self.charset)] * len(self.charset)
        else:
            shorter = self.distribution(context[1:])

        table = self.counts.get(context)
        if not table:
            probs = shorter
        else:
            total = sum(table.values())
            kinds = len(table)
            probs = [(table.get(c, 0) + kinds * shorter[y]) / (total + kinds)
                     for y, c in enumerate(self.charset)]

        self.dist_cache[context] = probs
        return probs

    def board(self, context, chaos):
        key = (context, round(chaos, 4))
        if key not in self.board_cache:
            self.board_cache[key] = Board(self.distribution(context), chaos)
        return self.board_cache[key]

    def pick_context(self, history, creativity):
        longest = 0
        for k in range(min(self.order, len(history)), 0, -1):
            if history[len(history) - k:] in self.counts:
                longest = k
                break

        # Imagination leap: forget part of what was just written
        if longest > MIN_LEAP_CONTEXT and random.random() < creativity * 0.35:
            longest = random.randint(MIN_LEAP_CONTEXT, longest - 1)

        return history[len(history) - longest:] if longest else ""

    def next_char(self, history, creativity=0.5):
        context = self.pick_context(history, creativity)
        return self.charset[self.board(context, chaos_for(creativity)).drop()]

    def write(self, seed="", length=300, creativity=0.5):
        unknown = sorted({c for c in seed if c not in self.slot_of})
        if unknown:
            raise ValueError(f"seed uses characters the model never saw: {unknown}")

        out = seed
        for _ in range(length):
            out += self.next_char(out, creativity)
        return out

    def evaluate(self, text):
        """Average surprise in bits per character when reading `text` (lower is better).

        Uses the exact landing chances of the untouched boards (creativity aside).
        A blind guess among all slots scores log2(len(charset)).
        """
        unknown = sorted({c for c in text if c not in self.slot_of})
        if unknown:
            raise ValueError(f"text uses characters the model never saw: {unknown}")
        if len(text) < 2:
            raise ValueError("text is too short to evaluate")

        bits = 0.0
        for i in range(1, len(text)):
            context = text[max(0, i - self.order):i]
            bits -= math.log2(self.distribution(context)[self.slot_of[text[i]]])
        return bits / (len(text) - 1)

    def originality(self, text):
        """Share of the words in `text` that never appeared in the training corpus."""
        words = words_of(text)
        if not words:
            return 0.0, []
        vocab = set(self.vocab)
        invented = sorted(w for w in words if w not in vocab)
        return len(invented) / len(words), invented

    def peek(self, context, creativity=0.5, balls=2000):
        """Drop many balls through a context's board and count the landing slots."""
        if context not in self.counts:
            raise ValueError(f"context {context!r} was never seen during training")
        board = self.board(context, chaos_for(creativity))
        landed = {}
        for _ in range(balls):
            c = self.charset[board.drop()]
            landed[c] = landed.get(c, 0) + 1
        return landed


def model_path(name):
    return f"{MODELS_DIR}/{name}.mdl"


# ---- command line -----------------------------------------------------------

def cmd_train(args):
    with open(args.corpus, "r", encoding="utf-8") as f:
        text = f.read()
    model = CreativeModel.train(args.name, text, args.order, args.min_count)
    path = model.save(overwrite=args.overwrite)
    print(f"Trained {args.name}: {len(text)} characters, {len(model.charset)} slots, "
          f"{len(model.counts)} boards (order {args.order}) -> {path}")


def cmd_write(args):
    if args.rng_seed is not None:
        random.seed(args.rng_seed)
    model = CreativeModel.load(args.name)
    text = model.write(args.seed, args.length, args.creativity)
    print(text)
    score, invented = model.originality(text[len(args.seed):])
    print("\n---")
    print(f"creativity {args.creativity:.2f} | originality {score:.0%} of words are new")
    if invented:
        print("invented words: " + ", ".join(invented[:20]))


def cmd_evaluate(args):
    model = CreativeModel.load(args.name)
    with open(args.text, "r", encoding="utf-8") as f:
        text = f.read()
    score = model.evaluate(text)
    blind = math.log2(len(model.charset))
    print(f"{args.name} on {args.text}: {score:.2f} bits per character "
          f"(blind guessing: {blind:.2f}, lower is better)")


def cmd_peek(args):
    if args.rng_seed is not None:
        random.seed(args.rng_seed)
    model = CreativeModel.load(args.name)
    landed = model.peek(args.context, args.creativity, args.balls)
    top = sorted(landed.items(), key=lambda kv: -kv[1])[:args.top]
    width = max(n for _, n in top)
    print(f"{args.balls} balls dropped after {args.context!r} (creativity {args.creativity:.2f}):")
    for c, n in top:
        bar = "o" * max(1, round(40 * n / width))
        print(f"  {c!r:>6} {n / args.balls:6.1%} {bar}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="PinkoAI Creative - a Plinko-board writer")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("train", help="tilt the pins using a text corpus")
    p.add_argument("corpus", help="path to a UTF-8 text file")
    p.add_argument("--name", required=True, help="model name (saved to models/<name>.mdl)")
    p.add_argument("--order", type=int, default=6, help="how many previous characters it remembers")
    p.add_argument("--min-count", type=int, default=3,
                   help=f"drop contexts longer than {ALWAYS_KEEP_CONTEXT} characters seen fewer times")
    p.add_argument("--overwrite", action="store_true")
    p.set_defaults(func=cmd_train)

    p = sub.add_parser("write", help="write new text")
    p.add_argument("name")
    p.add_argument("--seed", default="", help="text to start from")
    p.add_argument("--length", type=int, default=400)
    p.add_argument("--creativity", type=float, default=0.5, help="0 = close to the corpus, 1 = wild")
    p.add_argument("--rng-seed", type=int, default=None)
    p.set_defaults(func=cmd_write)

    p = sub.add_parser("evaluate", help="measure how well the model predicts a text")
    p.add_argument("name")
    p.add_argument("text", help="path to a UTF-8 text file, ideally one it was not trained on")
    p.set_defaults(func=cmd_evaluate)

    p = sub.add_parser("peek", help="drop many balls for one context and show where they land")
    p.add_argument("name")
    p.add_argument("context")
    p.add_argument("--creativity", type=float, default=0.5)
    p.add_argument("--balls", type=int, default=2000)
    p.add_argument("--top", type=int, default=12)
    p.add_argument("--rng-seed", type=int, default=None)
    p.set_defaults(func=cmd_peek)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
