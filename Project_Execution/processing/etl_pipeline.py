import os
import pandas as pd

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    DoubleType,
    IntegerType
)
from pyspark.sql import functions as F
from minio import Minio
from minio.error import S3Error


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROCESSED_DIR = os.path.join(BASE_DIR, "processed_data")
UPLOAD_DIR = os.path.join(BASE_DIR, "data", "uploads")

os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ============================================================
# MINIO CONFIGURATION
# ============================================================

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "admin12345"

RAW_BUCKET = "raw-data"
PROCESSED_BUCKET = "processed-data"


# ============================================================
# REQUIRED COLUMNS
# ============================================================

REQUIRED_COLUMNS = [
    "Date",
    "City",
    "Food",
    "Prepared_kg",
    "Consumed_kg",
    "Unit_Price",
    "Number_of_People"
]


# ============================================================
# SPARK SCHEMA
# ============================================================

SPARK_SCHEMA = StructType([
    StructField("Date", StringType(), True),
    StructField("City", StringType(), True),
    StructField("Hotel", StringType(), True),
    StructField("Food", StringType(), True),
    StructField("Meal", StringType(), True),
    StructField("Area", StringType(), True),
    StructField("Prepared_kg", DoubleType(), True),
    StructField("Consumed_kg", DoubleType(), True),
    StructField("Waste_kg", DoubleType(), True),
    StructField("Unit_Price", DoubleType(), True),
    StructField("Cost_Loss", DoubleType(), True),
    StructField("Number_of_People", IntegerType(), True)
])


# ============================================================
# MINIO CLIENT
# ============================================================

def get_minio_client():

    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )

    return client


# ============================================================
# CREATE MINIO BUCKETS
# ============================================================

def create_buckets():

    client = get_minio_client()

    for bucket in [RAW_BUCKET, PROCESSED_BUCKET]:

        try:

            if not client.bucket_exists(bucket):

                client.make_bucket(bucket)

                print("Created bucket:", bucket)

            else:

                print("Bucket already exists:", bucket)

        except S3Error as e:

            print("MinIO bucket error:", e)


# ============================================================
# READ INPUT DATASET
# ============================================================

def read_input_file(file_path):

    extension = os.path.splitext(file_path)[1].lower()

    print("\nReading input file:")
    print(file_path)

    if not os.path.exists(file_path):

        raise Exception(
            f"Uploaded file does not exist: {file_path}"
        )

    file_size = os.path.getsize(file_path)

    print("File size:", file_size, "bytes")

    if file_size == 0:

        raise Exception(
            "Uploaded file is empty."
        )

    if extension == ".csv":

        df = pd.read_csv(file_path)

    elif extension in [".xlsx", ".xls"]:

        df = pd.read_excel(file_path)

    else:

        raise Exception(
            "Only CSV and Excel files are supported."
        )

    print("Input records:", len(df))

    print("Input columns:")
    print(list(df.columns))

    if len(df) == 0:

        raise Exception(
            "Dataset contains no records."
        )

    return df


# ============================================================
# NORMALIZE COLUMN NAMES
# ============================================================

def normalize_columns(df):

    df.columns = [
        str(col).strip()
        for col in df.columns
    ]

    aliases = {

        "prepared": "Prepared_kg",
        "prepared_kg": "Prepared_kg",

        "consumed": "Consumed_kg",
        "consumed_kg": "Consumed_kg",

        "waste": "Waste_kg",
        "waste_kg": "Waste_kg",

        "unit_price": "Unit_Price",
        "price": "Unit_Price",

        "cost_loss": "Cost_Loss",
        "loss": "Cost_Loss",

        "number_of_people": "Number_of_People",
        "people": "Number_of_People",

        "city": "City",
        "food": "Food",
        "hotel": "Hotel",
        "meal": "Meal",
        "area": "Area",
        "date": "Date"
    }

    rename_dict = {}

    for column in df.columns:

        key = column.strip().lower()

        if key in aliases:

            rename_dict[column] = aliases[key]

    df = df.rename(columns=rename_dict)

    return df


# ============================================================
# VALIDATE COLUMNS
# ============================================================

def validate_columns(df):

    missing = [
        col
        for col in REQUIRED_COLUMNS
        if col not in df.columns
    ]

    if missing:

        raise Exception(
            "Missing required columns: "
            + ", ".join(missing)
        )

    return True


# ============================================================
# SAVE CSV FOR SPARK
# ============================================================

def prepare_spark_input(df):

    spark_input = os.path.join(
        UPLOAD_DIR,
        "spark_input.csv"
    )

    df.to_csv(
        spark_input,
        index=False
    )

    if not os.path.exists(spark_input):

        raise Exception(
            "Spark input CSV was not created."
        )

    size = os.path.getsize(spark_input)

    print(
        "Spark input file size:",
        size,
        "bytes"
    )

    if size == 0:

        raise Exception(
            "Spark input CSV is empty."
        )

    return spark_input


# ============================================================
# UPLOAD RAW DATA TO MINIO
# ============================================================

def upload_to_minio(
    client,
    file_path,
    bucket,
    object_name
):

    client.fput_object(
        bucket,
        object_name,
        file_path
    )

    print(
        f"Uploaded to MinIO: "
        f"{bucket}/{object_name}"
    )


# ============================================================
# MAIN ETL PIPELINE
# ============================================================

def process_dataset(
    file_path,
    original_filename
):

    print("\n")
    print("=" * 60)
    print("STARTING DATA ENGINEERING PIPELINE")
    print("=" * 60)

    # --------------------------------------------------------
    # STEP 1: READ DATASET
    # --------------------------------------------------------

    df = read_input_file(file_path)

    # --------------------------------------------------------
    # STEP 2: NORMALIZE COLUMN NAMES
    # --------------------------------------------------------

    df = normalize_columns(df)

    print("\nColumns after schema mapping:")
    print(list(df.columns))

    # --------------------------------------------------------
    # STEP 3: VALIDATE SCHEMA
    # --------------------------------------------------------

    validate_columns(df)

    print("\nSchema validation completed.")

    # --------------------------------------------------------
    # OPTIONAL COLUMNS
    # --------------------------------------------------------

    if "Hotel" not in df.columns:

        df["Hotel"] = "Unknown"

    if "Meal" not in df.columns:

        df["Meal"] = "Unknown"

    if "Area" not in df.columns:

        df["Area"] = "Unknown"

    # --------------------------------------------------------
    # ENSURE NUMERIC VALUES
    # --------------------------------------------------------

    numeric_columns = [
        "Prepared_kg",
        "Consumed_kg",
        "Unit_Price",
        "Number_of_People"
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # --------------------------------------------------------
    # SAVE TEMPORARY SPARK INPUT
    # --------------------------------------------------------

    spark_input = prepare_spark_input(df)

    # --------------------------------------------------------
    # STEP 4: MINIO RAW DATA
    # --------------------------------------------------------

    print("\nConnecting to MinIO...")

    create_buckets()

    client = get_minio_client()

    upload_to_minio(
        client,
        file_path,
        RAW_BUCKET,
        original_filename
    )

    # --------------------------------------------------------
    # STEP 5: START PYSPARK
    # --------------------------------------------------------

    print("\nStarting PySpark...")

    spark = (
        SparkSession
        .builder
        .appName("SmartFoodWasteETL")
        .master("local[*]")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    print("PySpark started.")

    # --------------------------------------------------------
    # STEP 6: READ CSV USING EXPLICIT SCHEMA
    # --------------------------------------------------------

    print("\nReading CSV using explicit Spark schema...")

    spark_df = (
        spark.read
        .option("header", "true")
        .schema(SPARK_SCHEMA)
        .csv(spark_input)
    )

    print(
        "Spark records before cleaning:",
        spark_df.count()
    )

    # --------------------------------------------------------
    # STEP 7: DATA CLEANING
    # --------------------------------------------------------

    spark_df = spark_df.dropna(
        subset=[
            "Date",
            "City",
            "Food",
            "Prepared_kg",
            "Consumed_kg"
        ]
    )

    spark_df = spark_df.dropDuplicates()

    # --------------------------------------------------------
    # STEP 8: CALCULATE WASTE
    # --------------------------------------------------------

    spark_df = spark_df.withColumn(
        "Waste_kg",
        F.greatest(
            F.col("Prepared_kg") -
            F.col("Consumed_kg"),
            F.lit(0.0)
        )
    )

    # --------------------------------------------------------
    # STEP 9: WASTE PERCENTAGE
    # --------------------------------------------------------

    spark_df = spark_df.withColumn(
        "Waste_Percentage",
        F.when(
            F.col("Prepared_kg") > 0,
            (
                F.col("Waste_kg") /
                F.col("Prepared_kg")
            ) * 100
        ).otherwise(0)
    )

    # --------------------------------------------------------
    # STEP 10: FINANCIAL LOSS
    # --------------------------------------------------------

    spark_df = spark_df.withColumn(
        "Cost_Loss",
        F.col("Waste_kg") *
        F.col("Unit_Price")
    )

    # --------------------------------------------------------
    # FINAL COUNT
    # --------------------------------------------------------

    final_count = spark_df.count()

    print(
        "\nRecords after cleaning:",
        final_count
    )

    if final_count == 0:

        spark.stop()

        raise Exception(
            "PySpark processing produced 0 records. "
            "Please check the dataset values."
        )

    # --------------------------------------------------------
    # STEP 11: SAVE PROCESSED DATA
    # --------------------------------------------------------

    print("\nSaving processed data...")

    processed_file = os.path.join(
        PROCESSED_DIR,
        "food_waste_processed.csv"
    )

    processed_pd = spark_df.toPandas()

    processed_pd.to_csv(
        processed_file,
        index=False
    )

    print(
        "Processed file saved:",
        processed_file
    )

    # --------------------------------------------------------
    # STEP 12: UPLOAD PROCESSED DATA TO MINIO
    # --------------------------------------------------------

    upload_to_minio(
        client,
        processed_file,
        PROCESSED_BUCKET,
        "food_waste_processed.csv"
    )

    # --------------------------------------------------------
    # STOP SPARK
    # --------------------------------------------------------

    spark.stop()

    # --------------------------------------------------------
    # DELETE TEMP FILE
    # --------------------------------------------------------

    if os.path.exists(spark_input):

        os.remove(spark_input)

    print("\n")
    print("=" * 60)
    print("DATA ENGINEERING PIPELINE COMPLETED")
    print("=" * 60)

    return {

        "success": True,

        "records": final_count,

        "raw_file": original_filename,

        "raw_bucket": RAW_BUCKET,

        "processed_file":
            "food_waste_processed.csv",

        "processed_bucket":
            PROCESSED_BUCKET
    }