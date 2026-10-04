"""Fact-check C09: prompt-rule compliance of the ChatGPT answer and a few arithmetic claims.

- "Stay under 1,800 words"; "At most six problems"; "Exactly five [ideas], at least two extending ... at least two
  alternatives"; "label any number you have not computed as a guess"; em dashes (house style, not a prompt rule).
- Arithmetic: 1.3 - 1.0 = 0.3; 1/sqrt(48); pre-holdout share of high-rate months.
"""
import re
import numpy as np

p = "/home/hashim/projects/GA/project/research/exchange/01_idea_generation/chatgpt_response.md"
txt = open(p, encoding="utf-8").read()
plain = re.sub(r"[#*|`>-]+", " ", txt)
words = re.findall(r"[A-Za-z0-9][A-Za-z0-9'’.,%/+\-−–≈×→…]*", plain)
print("word count (tokens with a letter or digit):", len(words))
print("critique items:", len(re.findall(r"^\*\*\d\. ", txt, flags=re.M)))
ideas = re.findall(r"^### Idea \d \((\w+)\)", txt, flags=re.M)
print("ideas:", len(ideas), ideas)
print("em dashes (U+2014):", txt.count("—"), "| en dashes (U+2013):", txt.count("–"))
print("'guess' labels:", len(re.findall(r"guess", txt, flags=re.I)))
nums = re.findall(r"~\s?\d[\d.]*|≈\s?\d[\d.]*|roughly [\d.]+|about [\d.]+", txt)
print("approximate numbers not labelled as guesses:", nums)
print("\n1.3 - 1.0 =", round(1.3 - 1.0, 2), "| exact team figures 1.3436% - 1.0489% =", round(1.3436 - 1.0489, 2))
print("1/sqrt(48) =", round(1 / np.sqrt(48), 4))
print("high-rate months: 47 of 74 in holdout =", round(47 / 74, 3))
