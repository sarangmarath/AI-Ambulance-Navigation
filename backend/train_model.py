import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder
import pickle
import random

random.seed(42)
np.random.seed(42)

# ── Road types in Chennai ──────────────────────────────────
road_types = {
    'primary':      {'base': 0.7, 'peak_factor': 1.8},
    'secondary':    {'base': 0.5, 'peak_factor': 1.5},
    'tertiary':     {'base': 0.3, 'peak_factor': 1.2},
    'residential':  {'base': 0.1, 'peak_factor': 1.1},
    'trunk':        {'base': 0.8, 'peak_factor': 2.0},
}

def base_congestion_by_hour(hour, is_weekend):
    if is_weekend:
        pattern = {
            0: 0.05, 1: 0.05, 2: 0.05, 3: 0.05, 4: 0.05,
            5: 0.08, 6: 0.12, 7: 0.18, 8: 0.22, 9: 0.25,
            10: 0.30, 11: 0.35, 12: 0.40, 13: 0.38, 14: 0.35,
            15: 0.38, 16: 0.42, 17: 0.48, 18: 0.52, 19: 0.45,
            20: 0.35, 21: 0.28, 22: 0.18, 23: 0.10
        }
    else:
        pattern = {
            0: 0.05, 1: 0.05, 2: 0.05, 3: 0.05, 4: 0.08,
            5: 0.15, 6: 0.35, 7: 0.65, 8: 0.85, 9: 0.75,
            10: 0.55, 11: 0.50, 12: 0.55, 13: 0.60, 14: 0.52,
            15: 0.58, 16: 0.70, 17: 0.88, 18: 0.92, 19: 0.80,
            20: 0.60, 21: 0.40, 22: 0.25, 23: 0.12
        }
    return pattern[hour]

# ── Generate dataset ───────────────────────────────────────
rows = []
for _ in range(15000):
    hour = random.randint(0, 23)
    day_of_week = random.randint(0, 6)
    is_weekend = day_of_week >= 5
    month = random.randint(1, 12)
    road_type = random.choice(list(road_types.keys()))
    road_length = round(random.uniform(50, 2000), 1)

    base = base_congestion_by_hour(hour, is_weekend)
    road_factor = road_types[road_type]['base']
    peak_factor = road_types[road_type]['peak_factor']

    if hour in [7, 8, 9, 17, 18, 19]:
        congestion = base * peak_factor
    else:
        congestion = base * (1 + road_factor * 0.5)

    is_monsoon = month in [6, 7, 8, 9, 10, 11]
    if is_monsoon:
        congestion *= random.uniform(1.1, 1.4)

    congestion += random.gauss(0, 0.05)
    congestion = round(max(0.05, min(1.0, congestion)), 3)

    rows.append({
        'hour': hour,
        'day_of_week': day_of_week,
        'is_weekend': int(is_weekend),
        'month': month,
        'is_monsoon': int(is_monsoon),
        'road_type': road_type,
        'road_length_m': road_length,
        'congestion_score': congestion
    })

df = pd.DataFrame(rows)
df.to_csv('chennai_traffic_dataset.csv', index=False)
print(f"Dataset created: {len(df)} records")

# ── Train model ────────────────────────────────────────────
le = LabelEncoder()
df['road_type_encoded'] = le.fit_transform(df['road_type'])

features = ['hour', 'day_of_week', 'is_weekend', 'month',
            'is_monsoon', 'road_type_encoded', 'road_length_m']

X = df[features]
y = df['congestion_score']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42)

model = RandomForestRegressor(
    n_estimators=100,
    max_depth=10,
    random_state=42,
    n_jobs=-1
)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"Accuracy: {round(r2*100, 2)}%")
print(f"Mean Absolute Error: {mae:.4f}")

# ── Save model and encoder ─────────────────────────────────
with open('traffic_model.pkl', 'wb') as f:
    pickle.dump(model, f)

with open('road_type_encoder.pkl', 'wb') as f:
    pickle.dump(le, f)

print("traffic_model.pkl saved!")
print("road_type_encoder.pkl saved!")