# PinkoAI

Yes dis pinko ai

An AI made of Plinko boards: balls drop through rows of pins, and the pins decide where they land.

## PinkoAI Creative

`creative.py` is a text-writing AI built on the same boards (`Pin`, `Level`, `ModType.ChanceWay`, `get_next_locs`).

- **One board per context.** For every run of recent characters (up to `--order` long), there's a board with one landing slot per character.
- **Training tilts the pins.** From how often each character followed a context in the corpus, every ChanceWay pin gets the exact bounce-right chance that makes the ball land in each slot as often as the corpus says. No randomness is involved in training, only counting.
- **Writing drops balls.** Each new character is one ball dropped through the board for the current context.
- **Creativity loosens the board.**
  - *chaos:* pins are pulled towards 50/50, so balls slip into neighbouring slots. Slots are ordered vowel-next-to-vowel and consonant-next-to-consonant, so slips make new words you can still pronounce.
  - *leaps:* sometimes the ball is dropped into the board of a shorter context. Less memory means less copying.

```sh
# Train on Shakespeare's sonnets (public domain, Project Gutenberg #1041)
python3 creative.py train corpus/sonnets.txt --name bard --order 5

# Write. creativity 0 = careful copyist, 1 = wild poet
python3 creative.py write bard --seed "Shall I " --length 400 --creativity 0.5

# See where 2000 balls land after a given context
python3 creative.py peek bard "love" --creativity 0.5

# Tests
python3 -m unittest test_creative
```

After each piece of writing, the AI reports its *originality*: the share of the words it wrote that never appear in the corpus. At higher creativity you get invented words like *floweetness*, *makingdoms* and *misproud*.
