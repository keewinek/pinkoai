import os

import creative

MODEL_NAME = "bard"
CORPUS = "corpus/sonnets.txt"

# Train once, then reuse the saved model
if os.path.exists(creative.model_path(MODEL_NAME)):
    model = creative.CreativeModel.load(MODEL_NAME)
else:
    with open(CORPUS, "r", encoding="utf-8") as f:
        model = creative.CreativeModel.train(MODEL_NAME, f.read())
    model.save()
    print(f"Trained {MODEL_NAME} on {CORPUS}")

text = model.write("Shall I ", 400, creativity=0.5)
print(text)

score, invented = model.originality(text)
print("\n---")
print(f"originality {score:.0%} of words are new")
if invented:
    print("invented words: " + ", ".join(invented[:20]))
