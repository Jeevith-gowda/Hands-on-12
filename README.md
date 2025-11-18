# Serverless Spark ETL Pipeline on AWS

## 📋 Project Overview

This project implements a fully automated, event-driven data pipeline on AWS that processes product review data without any manual intervention. When a CSV file is uploaded to an S3 bucket, the pipeline automatically cleans, transforms, and generates analytics reports.

### Architecture Flow

```
📤 CSV Upload to S3 Landing Bucket
    ↓
⚡ AWS Lambda (Triggered by S3 Event)
    ↓
🔧 AWS Glue ETL Job (PySpark Processing)
    ↓
📊 Processed Data & Analytics → S3 Output Bucket
```

---

## 🎯 Project Objectives

- Build an event-driven serverless pipeline
- Automate data cleaning and transformation using PySpark
- Generate multiple analytics reports from raw data
- Implement best practices for cloud-based ETL workflows

---

## 🛠️ Technologies Used

| Technology | Purpose |
|------------|---------|
| **AWS S3** | Storage for raw input data and processed outputs |
| **AWS Lambda** | Serverless function to trigger ETL pipeline |
| **AWS Glue** | Managed ETL service running PySpark jobs |
| **PySpark** | Data transformation and SQL analytics |
| **IAM** | Role-based access control and permissions |
| **CloudWatch** | Logging and monitoring |

---

## 📂 Repository Structure

```
.
├── Glue ETL Script.py      # PySpark ETL job with 4 analytics queries
├── lambda_function.py       # Lambda trigger function
├── reviews.csv              # Sample product review data
└── README.md                # Project documentation
```

---

## 🏗️ AWS Architecture Components

### 1. S3 Buckets

| Bucket Name | Purpose | Region |
|-------------|---------|--------|
| `handsonfinallanding1` | Raw CSV data upload zone | us-east-2 |
| `handsonfinalprocessed1` | Processed data and analytics outputs | us-east-2 |

### 2. IAM Roles

**GlueETLRole-Reviews**
- Permissions: S3 access, CloudWatch logging, Glue service role
- Purpose: Allows Glue job to read from landing bucket and write to processed bucket

**LambdaGlueTriggerRole**
- Permissions: Start Glue jobs, CloudWatch logging
- Purpose: Allows Lambda to trigger Glue ETL jobs

### 3. Lambda Function

**Name:** `trigger-glue-etl-job`
- **Runtime:** Python 3.12
- **Trigger:** S3 PUT events on `handsonfinallanding1` with `.csv` suffix
- **Function:** Starts the Glue ETL job when new CSV files are uploaded

### 4. Glue ETL Job

**Name:** `process_reviews_job`
- **Type:** Spark
- **Glue Version:** 4.0
- **Worker Type:** G.1X
- **Number of Workers:** 2
- **Language:** Python 3 (PySpark)

---

## 📊 Data Schema

### Input CSV Structure

```csv
review_id,product_id,customer_id,rating,review_date,review_text
106,p-005,c-142,5,2025-09-15,"Excellent product!"
107,p-011,c-221,4,2025-09-03,"Good value for money."
```

**Columns:**
- `review_id`: Unique identifier for each review
- `product_id`: Product identifier
- `customer_id`: Customer identifier
- `rating`: Product rating (1-5 stars, nullable)
- `review_date`: Date of review (YYYY-MM-DD)
- `review_text`: Review text content (nullable)

---

## 🔄 ETL Process

### Data Transformations

1. **Data Type Casting**
   - Cast `rating` to integer, fill nulls with 0

2. **Date Conversion**
   - Convert `review_date` string to proper date type

3. **Null Handling**
   - Fill null `review_text` with "No review text"

4. **Data Standardization**
   - Convert `product_id` to uppercase for consistency

5. **Output Generation**
   - Save cleaned data to `processed-data/` folder
   - Generate 4 analytics reports

---

## 📈 Analytics Queries Implemented

### Query 1: Product Analytics (Average Ratings)
**Purpose:** Calculate average rating and review count per product

**SQL:**
```sql
SELECT 
    product_id_upper, 
    AVG(rating) as average_rating,
    COUNT(*) as review_count
FROM product_reviews
GROUP BY product_id_upper
ORDER BY average_rating DESC
```

**Output Location:** `Athena Results/product_analytics/`

**Sample Output:**
| product_id_upper | average_rating | review_count |
|------------------|----------------|--------------|
| P-005 | 5.0 | 2 |
| P-007 | 5.0 | 1 |

---

### Query 2: Date-wise Review Count
**Purpose:** Calculate total number of reviews submitted per day

**SQL:**
```sql
SELECT 
    review_date,
    COUNT(*) as review_count
FROM product_reviews
WHERE review_date IS NOT NULL
GROUP BY review_date
ORDER BY review_date DESC
```

**Output Location:** `Athena Results/date_wise_reviews/`

**Sample Output:**
| review_date | review_count |
|-------------|--------------|
| 2025-11-05 | 1 |
| 2025-11-01 | 1 |

---

### Query 3: Top 5 Most Active Customers
**Purpose:** Identify power users by finding customers with the most reviews

**SQL:**
```sql
SELECT 
    customer_id,
    COUNT(*) as total_reviews,
    AVG(rating) as avg_rating
FROM product_reviews
WHERE customer_id IS NOT NULL
GROUP BY customer_id
ORDER BY total_reviews DESC
LIMIT 5
```

**Output Location:** `Athena Results/top_customers/`

**Sample Output:**
| customer_id | total_reviews | avg_rating |
|-------------|---------------|------------|
| c-142 | 1 | 5.0 |
| c-221 | 1 | 4.0 |

---

### Query 4: Overall Rating Distribution
**Purpose:** Show count and percentage for each star rating

**SQL:**
```sql
SELECT 
    rating,
    COUNT(*) as rating_count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()), 2) as percentage
FROM product_reviews
WHERE rating IS NOT NULL AND rating > 0
GROUP BY rating
ORDER BY rating DESC
```

**Output Location:** `Athena Results/rating_distribution/`

**Sample Output:**
| rating | rating_count | percentage |
|--------|--------------|------------|
| 5 | 4 | 40.00 |
| 4 | 2 | 20.00 |
| 3 | 2 | 20.00 |

---

## 🚀 Deployment Steps

### Phase 1: S3 Setup
1. Create `handsonfinallanding1` bucket in us-east-2
2. Create `handsonfinalprocessed1` bucket in us-east-2
3. Upload sample `reviews.csv` to landing bucket

### Phase 2: IAM Configuration
1. Create `GlueETLRole-Reviews` with:
   - AWSGlueServiceRole
   - AmazonS3FullAccess
   - CloudWatchLogsFullAccess

2. Create `LambdaGlueTriggerRole` with:
   - AWSLambdaBasicExecutionRole
   - Custom policy to start Glue jobs

### Phase 3: Glue ETL Job
1. Navigate to AWS Glue → ETL Jobs → Script Editor
2. Create new Spark job
3. Paste `Glue ETL Script.py` code
4. Configure job:
   - Name: `process_reviews_job`
   - IAM Role: `GlueETLRole-Reviews`
   - Glue version: 4.0
   - Workers: 2 × G.1X
5. Save and manually test the job

### Phase 4: Lambda Automation
1. Create Lambda function `trigger-glue-etl-job`
2. Runtime: Python 3.12
3. IAM Role: `LambdaGlueTriggerRole`
4. Paste `lambda_function.py` code
5. Add S3 trigger:
   - Bucket: `handsonfinallanding1`
   - Event: All object create events
   - Suffix: `.csv`

### Phase 5: End-to-End Testing
1. Upload a new CSV file to `handsonfinallanding1`
2. Verify Lambda logs in CloudWatch
3. Check Glue job runs and status
4. Validate output files in `handsonfinalprocessed1`

---

## 📸 Screenshots

### 1. S3 Buckets Configuration
![S3 Buckets](screenshots/s3-buckets.png)
*Caption: Landing and processed buckets in us-east-2*

### 2. IAM Roles
![IAM Roles](screenshots/iam-roles.png)
*Caption: GlueETLRole-Reviews with attached policies*

### 3. Glue ETL Job Configuration
![Glue Job Details](screenshots/glue-job-config.png)
*Caption: Glue job configured with Spark engine and 2 workers*

### 4. Glue Job Script
![Glue Script](screenshots/glue-script.png)
*Caption: PySpark ETL script with 4 analytics queries*

### 5. Glue Job Successful Run
![Glue Success](screenshots/glue-job-success.png)
*Caption: Job completed successfully with processed data*

### 6. Lambda Function Configuration
![Lambda Config](screenshots/lambda-config.png)
*Caption: Lambda function with Python 3.12 runtime*

### 7. Lambda S3 Trigger
![Lambda Trigger](screenshots/lambda-trigger.png)
*Caption: S3 trigger configured for CSV file uploads*

### 8. Lambda CloudWatch Logs
![Lambda Logs](screenshots/lambda-logs.png)
*Caption: Successful Lambda execution showing Glue job trigger*

### 9. S3 Output Structure
![S3 Output](screenshots/s3-output-structure.png)
*Caption: Processed data and analytics folders in output bucket*

### 10. Analytics Output Sample
![Analytics Data](screenshots/analytics-sample.png)
*Caption: Sample analytics CSV showing product ratings*

---

## ✅ Testing & Validation

### Manual Testing Process

1. **Upload Test File**
   ```bash
   # Upload CSV to landing bucket via AWS Console
   File: reviews-test.csv → handsonfinallanding1
   ```

2. **Verify Lambda Trigger**
   - Check CloudWatch logs for Lambda execution
   - Expected log: "Successfully started job run. Run ID: jr_xxx"

3. **Monitor Glue Job**
   - Navigate to Glue Console → Runs tab
   - Wait for status: "Succeeded" (3-5 minutes)

4. **Validate Output**
   - Check `handsonfinalprocessed1` bucket
   - Verify 5 folders: processed-data + 4 analytics folders
   - Download and inspect CSV files

### Expected Results

✅ Lambda triggers within seconds of S3 upload
✅ Glue job starts automatically
✅ Job completes in 3-5 minutes
✅ 5 output folders created with data
✅ All analytics CSVs contain valid data

---

## 🔧 Troubleshooting

### Issue 1: Lambda Not Triggering

**Symptom:** No CloudWatch logs after CSV upload

**Solutions:**
- Verify S3 trigger exists in Lambda → Configuration → Triggers
- Check S3 bucket event notifications in bucket Properties
- Ensure uploaded file has `.csv` extension

### Issue 2: Glue Job Access Denied

**Symptom:** Error "AmazonS3Exception: Access Denied"

**Solutions:**
- Verify `GlueETLRole-Reviews` has S3 permissions
- Check bucket names in Glue script match actual bucket names
- Ensure buckets are in the same region (us-east-2)

### Issue 3: Lambda Permission Error

**Symptom:** "User is not authorized to perform: glue:StartJobRun"

**Solutions:**
- Verify `LambdaGlueTriggerRole` has Glue start job permissions
- Check trust relationship allows Lambda service

### Issue 4: Empty Output Files

**Symptom:** Files created but size is 0 bytes

**Solutions:**
- Verify input CSV has data
- Check Glue job logs for transformation errors
- Ensure input bucket path is correct in script

---

## 💡 Key Learnings

1. **Event-Driven Architecture:** Automated pipelines reduce manual intervention and improve efficiency

2. **Serverless Benefits:** No infrastructure management, automatic scaling, pay-per-use pricing

3. **IAM Best Practices:** Least privilege access with specific resource permissions

4. **PySpark for ETL:** Powerful framework for distributed data processing

5. **Cloud Integration:** Seamless integration between AWS services (S3, Lambda, Glue)

---

## 🎓 Skills Demonstrated

- Cloud Architecture Design
- Serverless Computing (AWS Lambda)
- Big Data Processing (Apache Spark/PySpark)
- ETL Pipeline Development
- Infrastructure as Code principles
- IAM Security & Permissions Management
- Event-Driven Programming
- Data Transformation & Analytics
- AWS Service Integration

---

## 📌 Future Enhancements

1. **Data Validation:** Add data quality checks before processing
2. **Error Handling:** Implement SNS notifications for pipeline failures
3. **Partitioning:** Add date-based partitioning for better query performance
4. **Athena Integration:** Create Athena tables for SQL querying
5. **Step Functions:** Orchestrate complex multi-step workflows
6. **Cost Optimization:** Implement S3 lifecycle policies for old data
7. **Monitoring Dashboard:** Create CloudWatch dashboard for pipeline metrics
8. **CI/CD Pipeline:** Automate deployment using AWS CodePipeline

---

## 📚 References

- [AWS Glue Documentation](https://docs.aws.amazon.com/glue/)
- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/)
- [PySpark SQL Documentation](https://spark.apache.org/docs/latest/sql-programming-guide.html)
- [AWS S3 Event Notifications](https://docs.aws.amazon.com/AmazonS3/latest/userguide/EventNotifications.html)

---

## 👨‍💻 Author

**Jeevith**
- Master's in Computer Science (AI/ML Specialization)
- UNC Charlotte - Class of 2027
- AWS Region: us-east-2 (Ohio)

---

## 📝 License

This project is part of the ITCS 6190 Cloud Computing for Data Analysis course at UNC Charlotte.

---

## 🙏 Acknowledgments

- Course: ITCS 6190 - Cloud Computing for Data Analysis
- Institution: UNC Charlotte
- Semester: Fall 2025

---

**Project Completion Date:** November 18, 2025
