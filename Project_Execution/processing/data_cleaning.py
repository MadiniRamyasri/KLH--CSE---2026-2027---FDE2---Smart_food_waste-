import pandas as pd
import os


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_FILE = os.path.join(
    BASE_DIR,
    "data",
    "datasets",
    "smart_food_waste_dataset.csv"
)


# =========================================================
# COLUMN MAPPING
# =========================================================

COLUMN_MAPPING = {

    "date": "Date",

    "city": "City",

    "hotel": "Hotel",

    "food": "Food",

    "food_item": "Food",

    "meal": "Meal",

    "area": "Area",

    "prepared": "Prepared_kg",

    "prepared_kg": "Prepared_kg",

    "consumed": "Consumed_kg",

    "consumed_kg": "Consumed_kg",

    "waste": "Waste_kg",

    "waste_kg": "Waste_kg",

    "unit_price": "Unit_Price",

    "price": "Unit_Price",

    "cost_loss": "Cost_Loss",

    "number_of_people":
        "Number_of_People",

    "people":
        "Number_of_People"
}


print(
    "Loading dataset..."
)


df = pd.read_csv(
    DATA_FILE
)


print(
    "\nOriginal columns:"
)

print(
    list(df.columns)
)


# =========================================================
# NORMALIZE
# =========================================================

mapped_columns = {}

for column in df.columns:

    normalized = (
        str(column)
        .strip()
        .lower()
        .replace(" ", "_")
    )

    if normalized in COLUMN_MAPPING:

        mapped_columns[
            column
        ] = COLUMN_MAPPING[
            normalized
        ]


df.rename(
    columns=mapped_columns,
    inplace=True
)


print(
    "\nMapped columns:"
)

print(
    list(df.columns)
)


# =========================================================
# CHECK
# =========================================================

required = [

    "Date",
    "City",
    "Hotel",
    "Food",
    "Meal",
    "Area",
    "Prepared_kg",
    "Consumed_kg",
    "Waste_kg",
    "Unit_Price",
    "Cost_Loss",
    "Number_of_People"
]


missing = [

    column

    for column in required

    if column not in df.columns
]


if missing:

    print(
        "\nMissing columns:"
    )

    print(
        missing
    )

else:

    print(
        "\nAll supported columns detected successfully!"
    )


print(
    "\nColumn Mapping:"
)

for original, mapped in mapped_columns.items():

    print(
        f"{original}  →  {mapped}"
    )