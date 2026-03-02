import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import os

def analyze_vitals(user_data):
    base_path = os.path.dirname(__file__)
    file_path = os.path.join(base_path, "heart.csv")
    if not os.path.exists(file_path):
        return None, None, "CSV Missing"
    
    df = pd.read_csv(file_path)
    X = df.iloc[:, :-1] 
    y = df.iloc[:, -1]  

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train.values, y_train.values)

    accuracy = model.score(X_test.values, y_test.values)
    prediction = model.predict([user_data])[0]
    probability = model.predict_proba([user_data])[0][1]

    return prediction, probability, accuracy

def analyze_meal(meal_input, risk_level):
    unhealthy = ["pizza", "burger", "fries", "soda", "coke", "fried", "salt", "sugar", "cake", "butter", "oil"]
    healthy = ["salad", "oats", "fruit", "boiled", "grilled", "fish", "nuts", "water", "green", "vegetable"]
    meal_input = meal_input.lower()
    
    if any(word in meal_input for word in unhealthy):
        if risk_level == 1:
            return "❌ **Dangerous Choice:** Since your heart risk is high, this meal is too salty/fatty. Try a grilled salad instead!"
        return "⚠️ **Caution:** This meal is high in calories. Balance it with 30 mins of extra walking."
    
    if any(word in meal_input for word in healthy):
        return "✅ **Excellent choice!** Dr. Robo approves. This is a heart-healthy meal."
    
    return "🧐 **Note:** Stick to low-salt and high-fiber foods to be safe!"