import sys
import json
import joblib
import numpy as np

model = joblib.load("fertilizer_model.pkl")

data = json.loads(sys.argv[1])

features = np.array([[
    data['temperature'],
    data['humidity'],
    data['moisture'],
    data['soil'],
    data['crop'],
    data['N'],
    data['P'],
    data['K']
]])

prediction = model.predict(features)[0]

print(json.dumps({"fertilizer": prediction}))
