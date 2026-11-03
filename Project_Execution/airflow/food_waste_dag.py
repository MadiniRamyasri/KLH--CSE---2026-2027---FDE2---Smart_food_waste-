from datetime import datetime
import os
import sys

from airflow import DAG
from airflow.operators.python import PythonOperator


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_DIR = "/opt/food_waste_project"

PROCESSING_DIR = os.path.join(
    PROJECT_DIR,
    "processing"
)

ML_DIR = os.path.join(
    PROJECT_DIR,
    "ml"
)

DATASET_FILE = os.path.join(
    PROJECT_DIR,
    "data",
    "datasets",
    "smart_food_waste_dataset.csv"
)


# ============================================================
# PYTHON PATH
# ============================================================

if PROCESSING_DIR not in sys.path:
    sys.path.insert(0, PROCESSING_DIR)

if ML_DIR not in sys.path:
    sys.path.insert(0, ML_DIR)


# ============================================================
# TASK 1 - SCHEMA MAPPING
# ============================================================

def schema_mapping_task():

    print("=" * 60)
    print("TASK 1: SCHEMA MAPPING")
    print("=" * 60)

    # Add processing folder inside the actual Airflow task
    processing_dir = "/opt/food_waste_project/processing"

    if processing_dir not in sys.path:
        sys.path.insert(0, processing_dir)

    print("Processing directory:", processing_dir)
    print(
        "Processing directory exists:",
        os.path.exists(processing_dir)
    )

    # Import existing ETL functions
    from etl_pipeline import (
        read_input_file,
        normalize_columns,
        validate_columns
    )

    df = read_input_file(DATASET_FILE)

    df = normalize_columns(df)

    print("Detected columns:")
    print(list(df.columns))

    validate_columns(df)

    print("Schema validation completed successfully.")

# ============================================================
# TASK 2 - PYSPARK ETL + MINIO
# ============================================================

def pyspark_etl_task():

    print("=" * 60)
    print("TASK 2: PYSPARK ETL + MINIO")
    print("=" * 60)

    from etl_pipeline import process_dataset

    result = process_dataset(
        DATASET_FILE,
        os.path.basename(DATASET_FILE)
    )

    print("ETL Result:")
    print(result)

    if not result["success"]:
        raise Exception("ETL pipeline failed.")

    print("PySpark ETL and MinIO processing completed.")


# ============================================================
# TASK 3 - TRAIN RANDOM FOREST MODEL
# ============================================================

def train_ml_task():

    print("=" * 60)
    print("TASK 3: RANDOM FOREST MODEL TRAINING")
    print("=" * 60)

    predict_file = os.path.join(
        ML_DIR,
        "predict.py"
    )

    if not os.path.exists(predict_file):
        raise FileNotFoundError(
            f"ML file not found: {predict_file}"
        )

    print("Running:", predict_file)

    import subprocess

    result = subprocess.run(
        [sys.executable, predict_file],
        cwd=ML_DIR,
        capture_output=True,
        text=True
    )

    print(result.stdout)

    if result.stderr:
        print(result.stderr)

    if result.returncode != 0:
        raise Exception(
            "Random Forest model training failed."
        )

    model_file = os.path.join(
        ML_DIR,
        "food_waste_model.pkl"
    )

    if not os.path.exists(model_file):
        raise Exception(
            "Model file was not created."
        )

    print("Random Forest model created successfully.")
    print("Model:", model_file)


# ============================================================
# AIRFLOW DAG
# ============================================================

with DAG(
    dag_id="smart_food_waste_pipeline",

    description=(
        "End-to-end Smart Food Waste Analytics "
        "data engineering pipeline"
    ),

    start_date=datetime(2026, 1, 1),

    schedule=None,

    catchup=False,

    tags=[
        "food-waste",
        "data-engineering",
        "pyspark",
        "minio",
        "machine-learning"
    ]
) as dag:

    schema_mapping = PythonOperator(
        task_id="schema_mapping",
        python_callable=schema_mapping_task
    )

    pyspark_etl = PythonOperator(
        task_id="pyspark_etl_and_minio",
        python_callable=pyspark_etl_task
    )

    train_ml = PythonOperator(
        task_id="train_random_forest",
        python_callable=train_ml_task
    )


    # ========================================================
    # TASK DEPENDENCIES
    # ========================================================

    schema_mapping >> pyspark_etl >> train_ml