from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

import pandas as pd
import numpy as np
import os
import shutil
import sys
import joblib

from sklearn.ensemble import IsolationForest


# =========================================================
# ETL PIPELINE IMPORT
# =========================================================

sys.path.append(
    os.path.join(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        ),
        "processing"
    )
)

from etl_pipeline import process_dataset


# =========================================================
# APP
# =========================================================

app = FastAPI(
    title="Smart Food Waste Analytics Platform",
    description="Data Engineering and AI/ML Food Waste Analytics",
    version="2.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# =========================================================
# PATHS
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


DATA_DIR = os.path.join(
    BASE_DIR,
    "processed_data"
)


DATA_FILE = os.path.join(
    DATA_DIR,
    "food_waste_processed.csv"
)


DAILY_RECORD_FILE = os.path.join(
    DATA_DIR,
    "daily_records.csv"
)


MODEL_FILE = os.path.join(
    BASE_DIR,
    "ml",
    "food_waste_model.pkl"
)


os.makedirs(
    DATA_DIR,
    exist_ok=True
)


# =========================================================
# REQUIRED DATASET COLUMNS
# =========================================================

REQUIRED_COLUMNS = [
    "Date",
    "City",
    "Food",
    "Prepared_kg",
    "Consumed_kg",
    "Waste_kg",
    "Unit_Price",
    "Cost_Loss",
    "Number_of_People"
]


# =========================================================
# LOAD DATA
# =========================================================

def load_data():

    if not os.path.exists(DATA_FILE):

        raise HTTPException(
            status_code=404,
            detail="Processed dataset not found."
        )


    df = pd.read_csv(
        DATA_FILE
    )


    if df.empty:

        raise HTTPException(
            status_code=404,
            detail="Dataset is empty."
        )


    return df


# =========================================================
# DAILY RECORD MODEL
# =========================================================

class DailyRecord(BaseModel):

    date: str

    city: str

    food: str

    prepared_kg: float

    consumed_kg: float

    number_of_people: int

    unit_price: float = 0

    notes: str = ""


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {

        "message":
            "Smart Food Waste Analytics Platform API",

        "status":
            "running"
    }


# =========================================================
# UPLOAD DATASET
# =========================================================

@app.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...)
):

    filename = file.filename.lower()


    # -----------------------------------------------------
    # CHECK FILE TYPE
    # -----------------------------------------------------

    if not (
        filename.endswith(".csv")
        or filename.endswith(".xlsx")
        or filename.endswith(".xls")
    ):

        raise HTTPException(
            status_code=400,
            detail="Only CSV and Excel files are supported."
        )


    # -----------------------------------------------------
    # GET EXTENSION
    # -----------------------------------------------------

    extension = os.path.splitext(
        filename
    )[1]


    # -----------------------------------------------------
    # UPLOAD DIRECTORY
    # -----------------------------------------------------

    upload_dir = os.path.join(
        BASE_DIR,
        "data",
        "uploads"
    )


    os.makedirs(
        upload_dir,
        exist_ok=True
    )


    # -----------------------------------------------------
    # TEMPORARY FILE
    # -----------------------------------------------------

    temp_file = os.path.join(
        upload_dir,
        "uploaded_dataset" + extension
    )


    try:

        # -------------------------------------------------
        # SAVE UPLOADED FILE
        # -------------------------------------------------

        with open(
            temp_file,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )


        print(
            "\n========================================"
        )

        print(
            "DATASET UPLOAD STARTED"
        )

        print(
            "File:",
            file.filename
        )

        print(
            "========================================"
        )


        # -------------------------------------------------
        # RUN COMPLETE ETL PIPELINE
        # -------------------------------------------------

        result = process_dataset(
            temp_file,
            file.filename
        )


        # -------------------------------------------------
        # RESPONSE
        # -------------------------------------------------

        return {

            "message":
                "Dataset uploaded and processed successfully.",

            "filename":
                file.filename,

            "records":
                result["records"],

            "pipeline": {

                "schema_mapping":
                    "Completed",

                "pyspark_etl":
                    "Completed",

                "minio_raw_data":
                    "Uploaded",

                "minio_processed_data":
                    "Uploaded"
            }
        }


    except Exception as e:

        print(
            "\nUpload processing error:",
            str(e)
        )


        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


    finally:

        # -------------------------------------------------
        # REMOVE TEMP FILE
        # -------------------------------------------------

        if os.path.exists(
            temp_file
        ):

            os.remove(
                temp_file
            )


# =========================================================
# CITIES
# =========================================================

@app.get("/cities")
def get_cities():

    df = load_data()


    return {

        "cities":
            sorted(
                df["City"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
    }


# =========================================================
# FOODS
# =========================================================

@app.get("/foods")
def get_foods():

    df = load_data()


    return {

        "foods":
            sorted(
                df["Food"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
    }


# =========================================================
# ANALYTICS
# =========================================================

@app.get("/analytics/{city}")
def analytics(city: str):

    df = load_data()


    city_df = df[
        df["City"]
        .astype(str)
        .str.lower()
        ==
        city.lower()
    ]


    if city_df.empty:

        raise HTTPException(
            status_code=404,
            detail="City not found."
        )


    total_waste = \
        city_df["Waste_kg"].sum()


    total_prepared = \
        city_df["Prepared_kg"].sum()


    total_consumed = \
        city_df["Consumed_kg"].sum()


    financial_loss = \
        city_df["Cost_Loss"].sum()


    waste_percentage = (

        total_waste
        /
        total_prepared
        *
        100

        if total_prepared > 0

        else 0
    )


    return {

        "city":
            city,

        "total_waste":
            round(
                total_waste,
                2
            ),

        "total_prepared":
            round(
                total_prepared,
                2
            ),

        "total_consumed":
            round(
                total_consumed,
                2
            ),

        "waste_percentage":
            round(
                waste_percentage,
                2
            ),

        "financial_loss":
            round(
                financial_loss,
                2
            ),

        "records":
            len(city_df)
    }


# =========================================================
# WASTE BY FOOD
# =========================================================

@app.get("/waste-by-food/{city}")
def waste_by_food(city: str):

    df = load_data()


    city_df = df[
        df["City"]
        .astype(str)
        .str.lower()
        ==
        city.lower()
    ]


    if city_df.empty:

        raise HTTPException(
            status_code=404,
            detail="City not found."
        )


    result = (

        city_df
        .groupby("Food")["Waste_kg"]
        .sum()
        .sort_values(
            ascending=False
        )

    )


    return {

        "city":
            city,

        "food":
            result.index.tolist(),

        "waste":

            [
                round(
                    value,
                    2
                )

                for value
                in result.values
            ]
    }


# =========================================================
# HIGHEST WASTE FOOD
# =========================================================

@app.get("/highest-waste/{city}")
def highest_waste(city: str):

    df = load_data()


    city_df = df[
        df["City"]
        .astype(str)
        .str.lower()
        ==
        city.lower()
    ]


    if city_df.empty:

        raise HTTPException(
            status_code=404,
            detail="City not found."
        )


    result = (

        city_df
        .groupby("Food")["Waste_kg"]
        .sum()
        .sort_values(
            ascending=False
        )

    )


    return {

        "city":
            city,

        "food":
            result.index[0],

        "waste":
            round(
                result.iloc[0],
                2
            )
    }


# =========================================================
# WASTE TREND
# =========================================================

@app.get("/waste-trend/{city}")
def waste_trend(city: str):

    df = load_data()


    city_df = df[
        df["City"]
        .astype(str)
        .str.lower()
        ==
        city.lower()
    ].copy()


    if city_df.empty:

        raise HTTPException(
            status_code=404,
            detail="City not found."
        )


    city_df["Date"] = pd.to_datetime(
        city_df["Date"],
        errors="coerce"
    )


    result = (

        city_df
        .groupby("Date")["Waste_kg"]
        .sum()
        .sort_index()

    )


    return {

        "city":
            city,

        "dates":

            [
                date.strftime(
                    "%Y-%m-%d"
                )

                for date
                in result.index
            ],

        "waste":

            [
                round(
                    value,
                    2
                )

                for value
                in result.values
            ]
    }


# =========================================================
# FOOD DETAILS
# =========================================================

@app.get("/food-details/{city}")
def food_details(city: str):

    df = load_data()


    city_df = df[
        df["City"]
        .astype(str)
        .str.lower()
        ==
        city.lower()
    ].copy()


    if city_df.empty:

        raise HTTPException(
            status_code=404,
            detail="City not found."
        )


    result = (

        city_df
        .groupby("Food")
        .agg(

            Prepared_kg=(
                "Prepared_kg",
                "sum"
            ),

            Consumed_kg=(
                "Consumed_kg",
                "sum"
            ),

            Waste_kg=(
                "Waste_kg",
                "sum"
            ),

            Cost_Loss=(
                "Cost_Loss",
                "sum"
            )

        )
        .reset_index()

    )


    result["Waste_Percentage"] = (

        result["Waste_kg"]
        /
        result["Prepared_kg"]
        *
        100

    )


    result = result.sort_values(
        "Waste_kg",
        ascending=False
    )


    return result.round(
        2
    ).to_dict(
        orient="records"
    )


# =========================================================
# DATA QUALITY
# =========================================================

@app.get("/data-quality")
def data_quality():

    df = load_data()


    total_cells = (
        df.shape[0]
        *
        df.shape[1]
    )


    missing_values = int(
        df.isnull()
        .sum()
        .sum()
    )


    duplicate_records = int(
        df.duplicated()
        .sum()
    )


    if total_cells > 0:

        missing_score = (

            100
            -
            (
                missing_values
                /
                total_cells
                *
                100
            )

        )

    else:

        missing_score = 100


    if len(df) > 0:

        duplicate_score = (

            100
            -
            (
                duplicate_records
                /
                len(df)
                *
                100
            )

        )

    else:

        duplicate_score = 100


    score = (

        missing_score * 0.5
        +
        duplicate_score * 0.5

    )


    return {

        "score":
            round(
                max(score, 0),
                2
            ),

        "rows":
            len(df),

        "columns":
            len(df.columns),

        "missing_values":
            missing_values,

        "duplicate_records":
            duplicate_records
    }


# =========================================================
# DATASET SUMMARY
# =========================================================

@app.get("/dataset-summary")
def dataset_summary():

    df = load_data()


    cities = sorted(
        df["City"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )


    foods = sorted(
        df["Food"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )


    dates = pd.to_datetime(
        df["Date"],
        errors="coerce"
    )


    return {

        "rows":
            len(df),

        "columns":
            list(df.columns),

        "number_of_cities":
            len(cities),

        "number_of_foods":
            len(foods),

        "cities":
            cities,

        "foods":
            foods,

        "date_min":
            dates.min().strftime(
                "%Y-%m-%d"
            ),

        "date_max":
            dates.max().strftime(
                "%Y-%m-%d"
            )
    }


# =========================================================
# ANOMALY DETECTION
# =========================================================

@app.get("/anomalies/{city}")
def detect_anomalies(city: str):

    df = load_data()


    city_df = df[
        df["City"]
        .astype(str)
        .str.lower()
        ==
        city.lower()
    ].copy()


    if city_df.empty:

        raise HTTPException(
            status_code=404,
            detail="City not found."
        )


    features = city_df[
        [
            "Prepared_kg",
            "Consumed_kg",
            "Waste_kg",
            "Number_of_People"
        ]
    ].fillna(0)


    if len(features) < 10:

        return {

            "city":
                city,

            "anomaly_count":
                0,

            "anomalies":
                []
        }


    model = IsolationForest(
        contamination=0.05,
        random_state=42
    )


    city_df["anomaly"] = \
        model.fit_predict(
            features
        )


    anomalies = city_df[
        city_df["anomaly"] == -1
    ]


    return {

        "city":
            city,

        "anomaly_count":
            len(anomalies),

        "anomalies":

            anomalies[
                [
                    "Date",
                    "Food",
                    "Prepared_kg",
                    "Consumed_kg",
                    "Waste_kg",
                    "Number_of_People"
                ]
            ].to_dict(
                orient="records"
            )
    }


# =========================================================
# REDUCTION TARGET
# =========================================================

@app.get("/reduction-target/{city}")
def reduction_target(city: str):

    df = load_data()


    city_df = df[
        df["City"]
        .astype(str)
        .str.lower()
        ==
        city.lower()
    ]


    if city_df.empty:

        raise HTTPException(
            status_code=404,
            detail="City not found."
        )


    current_waste = \
        city_df["Waste_kg"].sum()


    target_waste = \
        current_waste * 0.85


    potential_reduction = (

        current_waste
        -
        target_waste

    )


    return {

        "city":
            city,

        "current_waste":
            round(
                current_waste,
                2
            ),

        "target_waste":
            round(
                target_waste,
                2
            ),

        "potential_reduction":
            round(
                potential_reduction,
                2
            ),

        "target_reduction_percentage":
            15
    }


# =========================================================
# CITY COMPARISON
# =========================================================

@app.get("/city-comparison")
def city_comparison():

    df = load_data()


    result = (

        df
        .groupby("City")
        .agg(

            Total_Waste=(
                "Waste_kg",
                "sum"
            ),

            Total_Prepared=(
                "Prepared_kg",
                "sum"
            ),

            Total_Consumed=(
                "Consumed_kg",
                "sum"
            ),

            Financial_Loss=(
                "Cost_Loss",
                "sum"
            )

        )
        .reset_index()

    )


    result["Waste_Percentage"] = (

        result["Total_Waste"]
        /
        result["Total_Prepared"]
        *
        100

    )


    return result.round(
        2
    ).to_dict(
        orient="records"
    )


# =========================================================
# RECOMMENDATIONS
# =========================================================

@app.get("/recommendations/{city}")
def recommendations(city: str):

    df = load_data()


    city_df = df[
        df["City"]
        .astype(str)
        .str.lower()
        ==
        city.lower()
    ].copy()


    if city_df.empty:

        raise HTTPException(
            status_code=404,
            detail="City not found."
        )


    total_prepared = \
        city_df["Prepared_kg"].sum()


    total_waste = \
        city_df["Waste_kg"].sum()


    waste_percentage = (

        total_waste
        /
        total_prepared
        *
        100

        if total_prepared > 0

        else 0
    )


    food_result = (

        city_df
        .groupby("Food")
        .agg(

            Prepared=(
                "Prepared_kg",
                "sum"
            ),

            Consumed=(
                "Consumed_kg",
                "sum"
            ),

            Waste=(
                "Waste_kg",
                "sum"
            )

        )
        .reset_index()

    )


    food_result["Waste_Percentage"] = (

        food_result["Waste"]
        /
        food_result["Prepared"]
        *
        100

    )


    food_result = food_result.sort_values(
        "Waste_Percentage",
        ascending=False
    )


    recommendations_list = []


    # =====================================================
    # GENERAL
    # =====================================================

    if waste_percentage >= 20:

        recommendations_list.append({

            "type":
                "High Waste",

            "title":
                "Reduce preparation quantity",

            "description":
                f"Overall waste is "
                f"{waste_percentage:.2f}%. "
                "Use historical consumption "
                "patterns to avoid "
                "over-preparation.",

            "priority":
                "High"
        })


    elif waste_percentage >= 10:

        recommendations_list.append({

            "type":
                "Moderate Waste",

            "title":
                "Improve demand planning",

            "description":
                "Compare preparation "
                "quantities with previous "
                "consumption before preparing "
                "large quantities.",

            "priority":
                "Medium"
        })


    else:

        recommendations_list.append({

            "type":
                "Monitoring",

            "title":
                "Continue monitoring",

            "description":
                "Maintain current monitoring "
                "of preparation, consumption "
                "and waste.",

            "priority":
                "Low"
        })


    # =====================================================
    # FOOD-SPECIFIC
    # =====================================================

    if not food_result.empty:

        top_food = \
            food_result.iloc[0]


        recommendations_list.append({

            "type":
                "Food Specific",

            "title":
                f"Review "
                f"{top_food['Food']} "
                f"preparation",

            "description":
                f"{top_food['Food']} has "
                f"a waste percentage of "
                f"{top_food['Waste_Percentage']:.2f}%. "
                "Review serving quantities "
                "and historical demand "
                "for this item.",

            "priority":
                "High"
        })


    # =====================================================
    # CONSUMPTION
    # =====================================================

    avg_prepared = \
        city_df["Prepared_kg"].mean()


    avg_consumed = \
        city_df["Consumed_kg"].mean()


    if avg_prepared > avg_consumed:

        recommendations_list.append({

            "type":
                "Consumption",

            "title":
                "Match preparation with demand",

            "description":
                "Prepared quantities are "
                "frequently higher than "
                "consumed quantities. "
                "Adjust future preparation "
                "using historical demand.",

            "priority":
                "Medium"
        })


    # =====================================================
    # FINANCIAL
    # =====================================================

    financial_loss = \
        city_df["Cost_Loss"].sum()


    if financial_loss > 0:

        recommendations_list.append({

            "type":
                "Financial",

            "title":
                "Reduce avoidable financial loss",

            "description":
                f"Recorded food waste "
                f"represents approximately "
                f"₹{financial_loss:,.2f} "
                "in calculated loss. "
                "Reducing waste can reduce "
                "this avoidable cost.",

            "priority":
                "Medium"
        })


    return {

        "city":
            city,

        "waste_percentage":
            round(
                waste_percentage,
                2
            ),

        "recommendations":
            recommendations_list
    }


# =========================================================
# DAILY RECORD - SAVE
# =========================================================

@app.post("/daily-record")
def add_daily_record(
    record: DailyRecord
):

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if record.prepared_kg < 0:

        raise HTTPException(
            status_code=400,
            detail=
                "Prepared quantity "
                "cannot be negative."
        )


    if record.consumed_kg < 0:

        raise HTTPException(
            status_code=400,
            detail=
                "Consumed quantity "
                "cannot be negative."
        )


    if record.consumed_kg > record.prepared_kg:

        raise HTTPException(
            status_code=400,
            detail=
                "Consumed quantity cannot "
                "be greater than prepared "
                "quantity."
        )


    # -----------------------------------------------------
    # CALCULATE WASTE
    # -----------------------------------------------------

    waste_kg = (

        record.prepared_kg
        -
        record.consumed_kg

    )


    waste_percentage = (

        waste_kg
        /
        record.prepared_kg
        *
        100

        if record.prepared_kg > 0

        else 0
    )


    # -----------------------------------------------------
    # CALCULATE LOSS
    # -----------------------------------------------------

    cost_loss = (

        waste_kg
        *
        record.unit_price

    )


    # -----------------------------------------------------
    # DATE
    # -----------------------------------------------------

    date_object = pd.to_datetime(
        record.date
    )


    day = date_object.strftime(
        "%A"
    )


    # -----------------------------------------------------
    # NEW RECORD
    # -----------------------------------------------------

    new_record = {

        "Date":
            date_object.strftime(
                "%Y-%m-%d"
            ),

        "Day":
            day,

        "City":
            record.city,

        "Food":
            record.food,

        "Prepared_kg":
            round(
                record.prepared_kg,
                2
            ),

        "Consumed_kg":
            round(
                record.consumed_kg,
                2
            ),

        "Waste_kg":
            round(
                waste_kg,
                2
            ),

        "Waste_Percentage":
            round(
                waste_percentage,
                2
            ),

        "Number_of_People":
            record.number_of_people,

        "Unit_Price":
            round(
                record.unit_price,
                2
            ),

        "Cost_Loss":
            round(
                cost_loss,
                2
            ),

        "Notes":
            record.notes
    }


    # -----------------------------------------------------
    # SAVE
    # -----------------------------------------------------

    new_df = pd.DataFrame(
        [new_record]
    )


    if os.path.exists(
        DAILY_RECORD_FILE
    ):

        old_df = pd.read_csv(
            DAILY_RECORD_FILE
        )


        final_df = pd.concat(
            [
                old_df,
                new_df
            ],
            ignore_index=True
        )


    else:

        final_df = new_df


    final_df.to_csv(
        DAILY_RECORD_FILE,
        index=False
    )


    return {

        "message":
            "Today's record saved successfully.",

        "record":
            new_record
    }


# =========================================================
# GET DAILY RECORDS
# =========================================================

@app.get("/daily-records")
def get_daily_records():

    if not os.path.exists(
        DAILY_RECORD_FILE
    ):

        return {

            "records":
                []
        }


    df = pd.read_csv(
        DAILY_RECORD_FILE
    )


    df = df.fillna("")


    return {

        "records":
            df.to_dict(
                orient="records"
            )
    }


# =========================================================
# TODAY'S SUMMARY
# =========================================================

@app.get("/today-summary")
def today_summary():

    today = pd.Timestamp.now().strftime(
        "%Y-%m-%d"
    )


    if not os.path.exists(
        DAILY_RECORD_FILE
    ):

        return {

            "date":
                today,

            "records":
                0,

            "prepared":
                0,

            "consumed":
                0,

            "waste":
                0,

            "loss":
                0
        }


    df = pd.read_csv(
        DAILY_RECORD_FILE
    )


    today_df = df[
        df["Date"].astype(str)
        ==
        today
    ]


    return {

        "date":
            today,

        "records":
            len(today_df),

        "prepared":
            round(
                today_df[
                    "Prepared_kg"
                ].sum(),
                2
            ),

        "consumed":
            round(
                today_df[
                    "Consumed_kg"
                ].sum(),
                2
            ),

        "waste":
            round(
                today_df[
                    "Waste_kg"
                ].sum(),
                2
            ),

        "loss":
            round(
                today_df[
                    "Cost_Loss"
                ].sum(),
                2
            )
    }


# =========================================================
# MODEL INFORMATION
# =========================================================

@app.get("/model-info")
def model_info():

    return {

        "algorithm":
            "Random Forest Regressor",

        "target":
            "Waste_kg",

        "features":

            [
                "City",
                "Hotel",
                "Food",
                "Meal",
                "Area",
                "Number_of_People",
                "Prepared_kg"
            ],

        "training_split":
            "80% Training / 20% Testing",

        "mae":
            2.79,

        "r2_score":
            0.5751
    }


# =========================================================
# PREDICTION
# =========================================================

@app.post("/predict")
def predict_waste(data: dict):

    if not os.path.exists(
        MODEL_FILE
    ):

        raise HTTPException(
            status_code=404,
            detail="ML model not found."
        )


    model = joblib.load(
        MODEL_FILE
    )


    required = [

        "City",
        "Hotel",
        "Food",
        "Meal",
        "Area",
        "Number_of_People",
        "Prepared_kg"

    ]


    for field in required:

        if field not in data:

            raise HTTPException(

                status_code=400,

                detail=
                    f"Missing field: "
                    f"{field}"
            )


    sample = pd.DataFrame({

        "City":
            [data["City"]],

        "Hotel":
            [data["Hotel"]],

        "Food":
            [data["Food"]],

        "Meal":
            [data["Meal"]],

        "Area":
            [data["Area"]],

        "Number_of_People":
            [data["Number_of_People"]],

        "Prepared_kg":
            [data["Prepared_kg"]]

    })


    prediction = model.predict(
        sample
    )[0]


    return {

        "predicted_waste_kg":
            round(
                float(prediction),
                2
            )
    }