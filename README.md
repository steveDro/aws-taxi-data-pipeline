# 🚀 AWS Taxi Data Pipeline (End-to-End Data Engineering Project)

## 📌 Overview

This project demonstrates a complete **end-to-end data engineering pipeline** built using modern cloud and data tools. The pipeline ingests raw NYC taxi data, processes it, stores it in AWS S3, and loads it into a data warehouse for analytics.

---

## 🧱 Architecture

```
Data Source (NYC Taxi Data)
        ↓
Python (Ingestion & Transformation)
        ↓
AWS S3 (Data Lake)
        ↓
Apache Airflow (Orchestration)
        ↓
Amazon Redshift (Data Warehouse)
        ↓
Analytics / Querying
```

---

## 🛠️ Tech Stack

- Python (Pandas, psycopg2)
- Apache Airflow (Workflow orchestration)
- AWS S3 (Data lake storage)
- Amazon Redshift (Cloud data warehouse)
- PostgreSQL (Initial staging)
- Docker & Docker Compose
- Terraform (Infrastructure as Code)

---

## 🔄 Pipeline Workflow

1. **Data Ingestion**
   - Fetch NYC taxi dataset using Python
   - Perform basic transformations (column selection)

2. **Data Storage**
   - Store processed data in AWS S3 (Parquet format)

3. **Orchestration**
   - Use Airflow DAG to automate pipeline execution
   - Tasks include ingestion, storage, and loading

4. **Data Loading**
   - Load data into PostgreSQL (initial phase)
   - Optimized using bulk inserts

5. **Data Warehousing**
   - Load data into Amazon Redshift using `COPY` command from S3
   - Handles millions of records efficiently

---

## ⚡ Performance Optimizations

- Replaced row-by-row inserts with bulk loading (`execute_values`)
- Leveraged Redshift `COPY` for high-speed ingestion
- Used Parquet format for efficient storage and transfer

---

## 📊 Data Volume

- Processed **~2.7 million+ records**
- Optimized for scalable data loading and querying

---

## 🧪 How to Run

### 1. Clone the repository

```bash
git clone https://github.com/stevedro/aws-taxi-data-pipeline.git
cd aws-taxi-data-pipeline
```

### 2. Start services (Docker)

```bash
docker compose up -d
```

### 3. Initialize Airflow

```bash
docker compose up airflow-init
```

### 4. Trigger DAG

- Open Airflow UI
- Run `taxi_data_pipeline`

---

## 🔐 Environment Variables

Create a `.env` file:

```
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
S3_BUCKET=your_bucket
```

---

## ☁️ Infrastructure (Terraform)

This project uses Terraform to provision:

- AWS S3 bucket
- Redshift cluster
- IAM roles and permissions

---

## 📈 Future Improvements

- Implement star schema (fact & dimension tables)
- Add dbt transformations
- Build dashboard (Power BI / Tableau)
- Add real-time streaming (Kafka)
- Implement data quality checks

---

## 💼 Resume Highlight

> Built a scalable end-to-end data pipeline using AWS S3, Apache Airflow, and Amazon Redshift, processing millions of records with optimized bulk loading and infrastructure as code (Terraform).

---

## 📬 Contact

Feel free to connect or reach out for collaboration!
