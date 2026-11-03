import pandas as pd
import os
import joblib

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score


# =========================================================
# PATHS
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_FILE = os.path.join(
    BASE_DIR,
    "processed_data",
    "food_waste_processed.csv"
)

MODEL_FILE = os.path.join(
    BASE_DIR,
    "ml",
    "food_waste_model.pkl"
)


# =========================================================
# LOAD DATA
# =========================================================

df = pd.read_csv(
    DATA_FILE
)

print(
    f"Dataset loaded successfully!"
)

print(
    f"Number of records: {len(df)}"
)


# =========================================================
# FEATURES
# =========================================================

features = [

    "City",
    "Hotel",
    "Food",
    "Meal",
    "Area",
    "Number_of_People",
    "Prepared_kg"
]

target = "Waste_kg"


X = df[features]

y = df[target]


# =========================================================
# CATEGORICAL / NUMERIC
# =========================================================

categorical_features = [

    "City",
    "Hotel",
    "Food",
    "Meal",
    "Area"
]

numeric_features = [

    "Number_of_People",
    "Prepared_kg"
]


# =========================================================
# PREPROCESSING
# =========================================================

preprocessor = ColumnTransformer(

    transformers=[

        (
            "categorical",

            OneHotEncoder(
                handle_unknown="ignore"
            ),

            categorical_features
        ),

        (
            "numeric",

            "passthrough",

            numeric_features
        )
    ]
)


# =========================================================
# MODEL
# =========================================================

model = RandomForestRegressor(

    n_estimators=100,

    random_state=42,

    n_jobs=-1
)


pipeline = Pipeline(

    steps=[

        (
            "preprocessor",
            preprocessor
        ),

        (
            "model",
            model
        )
    ]
)


# =========================================================
# TRAIN TEST SPLIT
# =========================================================

X_train, X_test, y_train, y_test = train_test_split(

    X,
    y,

    test_size=0.20,

    random_state=42
)


print(
    f"Training records: {len(X_train)}"
)

print(
    f"Testing records: {len(X_test)}"
)


# =========================================================
# TRAIN
# =========================================================

print(
    "\nTraining Random Forest model..."
)

pipeline.fit(
    X_train,
    y_train
)

print(
    "Model training completed!"
)


# =========================================================
# PREDICTION
# =========================================================

predictions = pipeline.predict(
    X_test
)


# =========================================================
# EVALUATION
# =========================================================

mae = mean_absolute_error(
    y_test,
    predictions
)

r2 = r2_score(
    y_test,
    predictions
)


print(
    "\n----- MODEL PERFORMANCE -----"
)

print(
    f"Mean Absolute Error: {mae:.2f} kg"
)

print(
    f"R2 Score: {r2:.4f}"
)


# =========================================================
# SAVE MODEL
# =========================================================

joblib.dump(
    pipeline,
    MODEL_FILE
)

print(
    "\nModel saved successfully!"
)

print(
    f"Model file: {MODEL_FILE}"
)


# =========================================================
# SAMPLE PREDICTION
# =========================================================

sample = pd.DataFrame({

    "City": [
        "Hyderabad"
    ],

    "Hotel": [
        "Hotel A"
    ],

    "Food": [
        "Biryani"
    ],

    "Meal": [
        "Lunch"
    ],

    "Area": [
        "Dining Hall"
    ],

    "Number_of_People": [
        180
    ],

    "Prepared_kg": [
        100
    ]
})


sample_prediction = pipeline.predict(
    sample
)


print(
    "\n----- SAMPLE PREDICTION -----"
)

print(
    f"Predicted Waste: "
    f"{sample_prediction[0]:.2f} kg"
)