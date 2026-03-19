import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib

# Load dataset
df = pd.read_csv("fertilizer_recommendation.csv")

# Encode categorical
df['Soil_Type'] = df['Soil_Type'].astype('category').cat.codes
df['Crop_Type'] = df['Crop_Type'].astype('category').cat.codes

feature_cols = ['Temperature', 'Humidity', 'Soil_Moisture', 'Soil_Type', 'Crop_Type', 'Nitrogen_Level', 'Phosphorus_Level', 'Potassium_Level']
X = df[feature_cols]
y = df['Recommended_Fertilizer']

# Train
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

model = RandomForestClassifier()
model.fit(X_train, y_train)

# Save model
joblib.dump(model, "fertilizer_model.pkl")

print("Model trained & saved!")
