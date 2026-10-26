import io
import json
import re

import numpy as np
import tensorflow as tf
from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image

IMG_SIZE = 224
MAX_SIZE = 5 * 1024 * 1024   # 5 Mo
SEUIL_CONFIANCE = 0.6        # en dessous, on prévient que le résultat est incertain

app = FastAPI(
    title="GreenCheck - Service IA",
    description="Diagnostic de maladies de plantes à partir d'une photo de feuille.",
    version="1.0.0",
)

# Chargé une seule fois au démarrage
model = tf.keras.models.load_model("plant_model.keras")
with open("class_names.json") as f:
    class_names = json.load(f)

CULTURES = {
    "Apple": "Pommier",
    "Blueberry": "Myrtillier",
    "Cherry_(including_sour)": "Cerisier",
    "Corn_(maize)": "Maïs",
    "Grape": "Vigne",
    "Orange": "Oranger",
    "Peach": "Pêcher",
    "Pepper,_bell": "Poivron",
    "Potato": "Pomme de terre",
    "Raspberry": "Framboisier",
    "Soybean": "Soja",
    "Squash": "Courge",
    "Strawberry": "Fraisier",
    "Tomato": "Tomate",
}


def analyser_label(label):
    """Sépare 'Tomato___Late_blight' en (culture en français, maladie, est_saine)."""
    culture, maladie = re.split(r"_{2,3}", label, maxsplit=1)
    maladie = maladie.strip("_").replace("_", " ")
    culture_fr = CULTURES.get(culture, culture)
    return culture_fr, maladie, maladie.lower() == "healthy"


def donner_conseil(maladie):
    """Règle métier : un conseil selon le type de maladie."""
    m = maladie.lower()
    if "mite" in m:
        return ("Des acariens attaquent la plante. Pulvérise de l'eau savonneuse sur le dessous "
                "des feuilles et garde un peu d'humidité autour de la plante.")
    if "virus" in m or "mosaic" in m:
        return ("Maladie virale : il n'existe pas de traitement. Isole ou retire la plante atteinte, "
                "désinfecte tes outils et surveille les pucerons et aleurodes qui propagent le virus.")
    if "bacterial" in m:
        return ("Maladie bactérienne. Retire les feuilles atteintes, évite de mouiller le feuillage "
                "à l'arrosage et désinfecte tes outils après usage.")
    if "haunglongbing" in m:
        return ("Maladie grave des agrumes, sans traitement. Contacte un professionnel ou "
                "l'organisme sanitaire de ta région.")
    return ("Probable maladie due à un champignon. Retire les feuilles atteintes, aère la plante, "
            "évite de mouiller le feuillage et demande en jardinerie un traitement adapté.")


@app.get("/health")
def health():
    return {"status": "ok", "classes": len(class_names)}


@app.post("/predict")
def predict(file: UploadFile = File(...)):
    donnees = file.file.read(MAX_SIZE + 1)
    if len(donnees) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="Image trop lourde (5 Mo maximum).")

    try:
        Image.open(io.BytesIO(donnees)).verify()
        image = Image.open(io.BytesIO(donnees)).convert("RGB").resize((IMG_SIZE, IMG_SIZE))
    except Exception:
        raise HTTPException(status_code=400, detail="Ce fichier n'est pas une image valide.")

    # Le modèle gère lui-même la mise à l'échelle des pixels : on envoie les valeurs brutes
    lot = np.expand_dims(np.asarray(image, dtype=np.float32), axis=0)
    probas = model.predict(lot, verbose=0)[0]

    meilleur = int(np.argmax(probas))
    confiance = float(probas[meilleur])
    culture, maladie, saine = analyser_label(class_names[meilleur])

    meilleurs_3 = []
    for i in np.argsort(probas)[::-1][:3]:
        c, m, _ = analyser_label(class_names[int(i)])
        meilleurs_3.append({"plant": c, "disease": m, "confidence": round(float(probas[i]), 4)})

    return {
        "result": "sain" if saine else maladie,
        "plant": culture,
        "confidence": round(confiance, 4),
        "is_healthy": saine,
        "advice": ("La feuille semble saine. Continue ton entretien habituel." if saine
                   else donner_conseil(maladie)),
        "warning": (None if confiance >= SEUIL_CONFIANCE else
                    "Confiance faible : essaie avec une photo plus nette, sur fond uni."),
        "top3": meilleurs_3,
    }