import os
import json

DIR = "data/dataset"

# Script anti burr0
# Percorre recursivamente: data/dataset/[classes]/[jsons]
for root, dirs, files in os.walk(DIR):
    for filename in files:
        if not filename.lower().endswith(".json"):
            continue

        json_path = os.path.join(root, filename)

        arqv = open(json_path, "r")
        dados = json.load(arqv)
        arqv.close()

        if dados["imageData"] is None:
            continue

        print(f"Corrigindo: {json_path}")

        dados["imageData"] = None

        arqv = open(json_path, "w")
        json.dump(dados, arqv)
        arqv.close()

