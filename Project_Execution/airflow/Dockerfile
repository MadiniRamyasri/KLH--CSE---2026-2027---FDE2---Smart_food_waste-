FROM apache/airflow:3.0.6

USER root

RUN apt-get update \
    && apt-get install -y default-jre \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

RUN pip install --no-cache-dir \
    pandas==2.2.3 \
    openpyxl \
    minio \
    pyspark \
    scikit-learn \
    joblib