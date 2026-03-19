import pandas as pd

# Load crop dataset
data = pd.read_csv("crop_data.csv")

print("Enter Soil Values")

N = float(input("Enter Nitrogen (N): "))
P = float(input("Enter Phosphorus (P): "))
K = float(input("Enter Potassium (K): "))

soil_input = {"N": N, "P": P, "K": K}
market_prices = {
    "Wheat": 4400,
    "Rice": 2100,
    "Pulses": 6000,
    "Mustard": 3000
}

neighbor_percent = {
    "Wheat": 70,
    "Rice": 50,
    "Pulses": 10,
    "Mustard": 30
}

# -----------------------------------
# Calculate Maximum Possible Profit
# -----------------------------------

max_possible_profit = 0

for index, row in data.iterrows():
    crop_name = row["Crop"]
    y = row["YieldPerAcre"]
    c = row["CostPerAcre"]

    profit = (market_prices[crop_name] * y) - c

    if profit > max_possible_profit:
        max_possible_profit = profit


# -----------------------------------
# Helper Functions (OUTSIDE LOOP)
# -----------------------------------

def normalize_price(price):
    max_price = max(market_prices.values())
    return (price / max_price) * 100


def calculate_soil_score(row):

    crop = row["Crop"]

    ideal_conditions = {
        "Wheat": {"N": (80,120), "P": (40,60), "K": (30,50)},
        "Rice": {"N": (100,150), "P": (50,70), "K": (40,60)},
        "Pulses": {"N": (40,80), "P": (30,50), "K": (20,40)},
        "Mustard": {"N": (60,100), "P": (35,55), "K": (25,45)}
    }

    score = 0

    for nutrient in ["N","P","K"]:
        low, high = ideal_conditions[crop][nutrient]
        if low <= soil_input[nutrient] <= high:
            score += 33

    return score


def calculate_final_score(row):

    crop = row["Crop"]

    price_score = normalize_price(market_prices[crop])
    soil_score = calculate_soil_score(row)

    crop_neighbor_percent = neighbor_percent[crop]

    if 30 <= crop_neighbor_percent <= 60:
        neighbor_score = 100
    elif crop_neighbor_percent < 30:
        neighbor_score = 60
    else:
        neighbor_score = 50

    yield_score = row["YieldScore"]
    yield_per_acre = row["YieldPerAcre"]
    cost = row["CostPerAcre"]

    estimated_profit = (market_prices[crop] * yield_per_acre) - cost
    profit_score = (estimated_profit / max_possible_profit) * 100

    final_score = (
        price_score * 0.3 +
        soil_score * 0.25 +
        neighbor_score * 0.2 +
        yield_score * 0.1 +
        profit_score * 0.15
    )

    return round(final_score,2)


# -----------------------------------
# Apply Model
# -----------------------------------

data["FinalScore"] = data.apply(calculate_final_score, axis=1)

print(data[["Crop","FinalScore"]])

best_crop = data.loc[data["FinalScore"].idxmax()]

print("\nRecommended Crop:", best_crop["Crop"])
print("Final Score:", best_crop["FinalScore"])