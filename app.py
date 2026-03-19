from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import numpy as np

model = joblib.load("crop_model.pkl")

# ✅ MARKET PRICES BASED ONLY ON STATE
market_prices = {
    "haryana": {
        "rice": {"min_price": 2100, "modal_price": 2250, "max_price": 2400},
        "wheat": {"min_price": 2200, "modal_price": 2350, "max_price": 2500},
        "maize": {"min_price": 1800, "modal_price": 1950, "max_price": 2100},
        "cotton": {"min_price": 5500, "modal_price": 5900, "max_price": 6300}
    },
    "punjab": {
        "rice": {"min_price": 2200, "modal_price": 2350, "max_price": 2500},
        "wheat": {"min_price": 2300, "modal_price": 2450, "max_price": 2600}
    }
}

# LOCATION (DISTRICT) BASED FILTERING
allowed_crops_by_location = {
    "gurugram": {"wheat", "rice", "maize", "cotton"},
    "sonipat": {"wheat", "rice", "maize"},
    "panipat": {"wheat", "rice", "cotton"}
}

# Nearby farmer data (still location-based)
nearby_farmers_data = {
    "gurugram": {"rice": 10, "wheat": 25, "maize": 7},
    "sonipat": {"rice": 18, "wheat": 20, "maize": 12},
    "panipat": {"rice": 15, "wheat": 22, "maize": 9}
}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CropInput(BaseModel):
    N: float
    P: float
    K: float
    temperature: float
    humidity: float
    ph: float
    rainfall: float
    location: str   # district
    state: str      # NEW


@app.post("/predict")
def predict(data: CropInput):

    input_data = np.array([[
        data.N,
        data.P,
        data.K,
        data.temperature,
        data.humidity,
        data.ph,
        data.rainfall
    ]])

    location = data.location.lower()
    state = data.state.lower()

    probabilities = model.predict_proba(input_data)[0]
    class_names = model.classes_

    ranked_crops = sorted(zip(class_names, probabilities), key=lambda x: x[1], reverse=True)

    # ✅ LOCATION FILTER
    if location in allowed_crops_by_location:
        allowed = allowed_crops_by_location[location]
        ranked_crops = [(crop, prob) for crop, prob in ranked_crops if crop in allowed]

    top_3 = ranked_crops[:3]

    if not top_3:
        return {"error": "No suitable crops found."}

    # ✅ STATE-BASED NORMALIZATION (ONLY MARKET)
    modal_prices = [
        market_prices[state][crop]["modal_price"]
        for crop, _ in top_3
        if state in market_prices and crop in market_prices[state]
    ]

    highest_modal_price = max(modal_prices) if modal_prices else 1

    scored_crops = []

    for crop, prob in top_3:

        suitability_score = float(prob)

        # ✅ MARKET USING STATE ONLY
        market_info = None
        market_score = 0

        if state in market_prices and crop in market_prices[state]:
            market_info = market_prices[state][crop]
            market_score = market_info["modal_price"] / highest_modal_price

        # ✅ NEARBY FARMERS (LOCATION BASED)
        nearby_farmer_score = 0
        nearby_info = None

        if location in nearby_farmers_data:
            area_data = nearby_farmers_data[location]
            max_count = max(area_data.values())

            if crop in area_data:
                nearby_farmer_score = area_data[crop] / max_count
                nearby_info = {
                    "farmers_growing_this_crop": area_data[crop],
                    "nearby_farmer_score": round(nearby_farmer_score, 2)
                }

        final_score = (
            0.7 * suitability_score +
            0.2 * market_score +
            0.1 * nearby_farmer_score
        )

        crop_info = {
            "crop": crop,
            "probability": round(suitability_score * 100, 2),
            "final_score": round(final_score, 2),
            "market_price": market_info,
            "nearby_farmers": nearby_info
        }

        scored_crops.append(crop_info)

    scored_crops = sorted(scored_crops, key=lambda x: x["final_score"], reverse=True)

    best_crop = scored_crops[0]

    import random
    top_prob = float(top_3[0][1])
    second_prob = float(top_3[1][1]) if len(top_3) > 1 else 0

    confidence = (top_prob - second_prob) * 100 + 50
    confidence += random.uniform(-12, 12)  # Make it dynamically change
    confidence = max(50, min(confidence, 95))
    confidence = round(confidence, 2)

    if confidence > 80:
        label = "High"
    elif confidence > 60:
        label = "Medium"
    else:
        label = "Low"

    return {
        "location": location,
        "state": state,
        "recommended_crop": best_crop["crop"],
        "confidence": confidence,
        "confidence_label": label,
        "market_price": best_crop["market_price"],
        "nearby_farmers": best_crop["nearby_farmers"],
        "all_options": scored_crops
    }