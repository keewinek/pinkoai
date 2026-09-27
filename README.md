# PinkoAI

Yes dis pinko ai

An AI made of Plinko boards: balls drop through rows of pins, and the pins decide where they land.

## PinkoAI Creative

`creative.py` is a text-writing AI built on the same boards (`Pin`, `Level`, `ModType.ChanceWay`, `get_next_locs`).

- **One board per context.** For every run of recent characters (up to `--order` long), there's a board with one landing slot per character.
- **Training tilts the pins.** From how often each character followed a context in the corpus, every ChanceWay pin gets the exact bounce-right chance that makes the ball land in each slot as often as the corpus says. No randomness is involved in training, only counting.
- **Boards borrow from shorter ones.** A context seen only a few times would be overconfident, so each board blends its counts with the board of the next-shorter context (Witten-Bell smoothing). Long contexts seen fewer than `--min-count` times are dropped entirely.
- **Writing drops balls.** Each new character is one ball dropped through the board for the current context.
- **Creativity loosens the board.**
  - *chaos:* pins are pulled towards 50/50, so balls slip into neighbouring slots. Slots are ordered vowel-next-to-vowel and consonant-next-to-consonant, so slips make new words you can still pronounce.
  - *leaps:* sometimes the ball is dropped into the board of a shorter context. Less memory means less copying.

```sh
# Run the trained model (models/bard.mdl)
python3 main.py

# Train on ~760k characters of verse: Shakespeare's sonnets, Venus and Adonis,
# The Rape of Lucrece, Milton's Paradise Lost and Keats's Poems 1817
# (all public domain, rebuilt from Project Gutenberg by corpus/build_corpus.py)
python3 creative.py train corpus/poetry.txt --name bard --order 6 --min-count 3 --overwrite

# Write. creativity 0 = close to the corpus, 1 = wild poet
python3 creative.py write bard --seed "Shall I " --length 400 --creativity 0.5

# How well does it predict a text? (bits per character, lower is better)
python3 creative.py evaluate bard some_other_poem.txt

# See where 2000 balls land after a given context
python3 creative.py peek bard "love" --creativity 0.5

# Tests
python3 -m unittest test_creative
```

After each piece of writing, the AI reports its *originality*: the share of the words it wrote that never appear in the corpus. At higher creativity you get invented words like *floweetness*, *makingdoms* and *misproud*.

### Training results

Measured on the last 10% of the sonnets, held out of training (a blind guess among the characters scores about 5.9):

| model | bits per character |
| --- | --- |
| sonnets only, order 5, no blending | 5.34 |
| sonnets only, order 5, blended | 2.71 |
| all poetry, order 6, blended, min-count 3 | **2.38** |
