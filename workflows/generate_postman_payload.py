#!/usr/bin/env python3
"""
Génère le payload JSON complet pour Postman avec l'image encodée en base64
"""

import json
import base64
from pathlib import Path

def generate_payload():
    # 1. Lire le workflow au format API
    with open('workflows/renovate_workflow-api.json', 'r') as f:
        workflow = json.load(f)

    # 2. Encoder l'image
    with open('image_input/input_1.png', 'rb') as img:
        image_base64 = f"data:image/png;base64,{base64.b64encode(img.read()).decode('utf-8')}"

    # 3. Mettre à jour le nom de l'image dans le workflow (format API)
    workflow["78"]["inputs"]["image"] = "input_1.png"

    # 4. Créer le payload complet
    payload = {
        "input": {
            "workflow": workflow,
            "images": [
                {
                    "name": "input_1.png",
                    "image": image_base64
                }
            ]
        }
    }

    # 5. Sauvegarder dans un fichier
    output_file = 'postman_payload.json'
    with open(output_file, 'w') as f:
        json.dump(payload, f, indent=2)

    print(f"✅ Payload généré: {output_file}")
    print(f"📊 Taille du fichier: {Path(output_file).stat().st_size / 1024:.2f} KB")
    print(f"\n📋 Dans Postman:")
    print(f"1. Méthode: POST")
    print(f"2. URL: https://api.runpod.ai/v2/mkcsuixk41yefk/run")
    print(f"3. Headers:")
    print(f"   Authorization: Bearer VOTRE_API_KEY")
    print(f"   Content-Type: application/json")
    print(f"4. Body > raw > JSON: copiez le contenu de {output_file}")

if __name__ == "__main__":
    generate_payload()
