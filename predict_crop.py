import json
import sys
import pickle
import pandas as pd

# Load model
with open("crop_model.pkl", "rb") as f:
    model = pickle.load(f)


# ✅ MARKET FUNCTION
def get_market_price(state, crop):
    market_prices = {
        "haryana": {
            "rice": {"min_price": 2100, "modal_price": 2250, "max_price": 2400},
            "wheat": {"min_price": 2200, "modal_price": 2350, "max_price": 2500}
        },
        "punjab": {
            "rice": {"min_price": 2200, "modal_price": 2350, "max_price": 2500},
            "wheat": {"min_price": 2300, "modal_price": 2450, "max_price": 2600}
        }
    }

    state = state.lower()
    crop = crop.lower()

    if state in market_prices and crop in market_prices[state]:
        price = market_prices[state][crop]

        return {
            "min_price": price["min_price"],
            "modal_price": price["modal_price"],
            "max_price": price["max_price"],
            "trend": "Stable",
            "best_month": "March",
            "profit_rating": "Medium",
            "insight": f"{crop.capitalize()} prices in {state.capitalize()} are stable."
        }

    return {"error": "No data found"}


# ✅ MAIN ENTRY POINT
if __name__ == "__main__":

    input_data = json.loads(sys.argv[1])

    # 🔥 MARKET REQUEST
    if input_data.get("type") == "market":
        result = get_market_price(
            input_data.get("state"),
            input_data.get("crop")
        )
        print(json.dumps(result))
        sys.exit()

    # 🌱 CROP PREDICTION REQUEST
    df = pd.DataFrame([{
        "N": input_data["N"],
        "P": input_data["P"],
        "K": input_data["K"],
        "temperature": input_data["temperature"],
        "humidity": input_data["humidity"],
        "ph": input_data["ph"],
        "rainfall": input_data["rainfall"]
    }])

    prediction = model.predict(df)

    print(json.dumps({
        "recommended_crop": prediction[0]
    }))