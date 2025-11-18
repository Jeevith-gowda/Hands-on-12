import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import col, to_date, upper, coalesce, lit
from awsglue.dynamicframe import DynamicFrame

## Initialize contexts
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)

# --- Define S3 Paths (Updated with your new names) ---
s3_input_path = "s3://handsonfinallanding/"
s3_processed_path = "s3://handsonfinalprocessed1/processed-data/"
s3_analytics_path = "s3://handsonfinalprocessed1/Athena Results/"

# --- Read the data from the S3 landing zone ---
dynamic_frame = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={"paths": [s3_input_path], "recurse": True},
    format="csv",
    format_options={"withHeader": True, "inferSchema": True},
)

# Convert to a standard Spark DataFrame for easier transformation
df = dynamic_frame.toDF()

# --- Perform Transformations ---
# 1. Cast 'rating' to integer and fill null values with 0
df_transformed = df.withColumn("rating", coalesce(col("rating").cast("integer"), lit(0)))

# 2. Convert 'review_date' string to a proper date type
df_transformed = df_transformed.withColumn("review_date", to_date(col("review_date"), "yyyy-MM-dd"))

# 3. Fill null review_text with a default string
df_transformed = df_transformed.withColumn("review_text",
    coalesce(col("review_text"), lit("No review text")))

# 4. Convert product_id to uppercase for consistency
df_transformed = df_transformed.withColumn("product_id_upper", upper(col("product_id")))

# --- Write the full transformed data to S3 (Good practice) ---
# This saves the clean, complete dataset to the 'processed-data' folder
glue_processed_frame = DynamicFrame.fromDF(df_transformed, glueContext, "transformed_df")
glueContext.write_dynamic_frame.from_options(
    frame=glue_processed_frame,
    connection_type="s3",
    connection_options={"path": s3_processed_path},
    format="csv"
)

# --- Run Spark SQL Queries within the Job ---
# Create a temporary view in Spark's memory
df_transformed.createOrReplaceTempView("product_reviews")

# ========================================
# QUERY 1: Average Rating Per Product
# ========================================
df_analytics_result = spark.sql("""
    SELECT 
        product_id_upper, 
        AVG(rating) as average_rating,
        COUNT(*) as review_count
    FROM product_reviews
    GROUP BY product_id_upper
    ORDER BY average_rating DESC
""")

print(f"Writing product analytics results to {s3_analytics_path}product_analytics/")
analytics_result_frame = DynamicFrame.fromDF(df_analytics_result.repartition(1), glueContext, "analytics_df")
glueContext.write_dynamic_frame.from_options(
    frame=analytics_result_frame,
    connection_type="s3",
    connection_options={"path": s3_analytics_path + "product_analytics/"},
    format="csv"
)

# ========================================
# QUERY 2: Date-wise Review Count
# ========================================
# This query calculates the total number of reviews submitted per day
df_date_wise_reviews = spark.sql("""
    SELECT 
        review_date,
        COUNT(*) as review_count
    FROM product_reviews
    WHERE review_date IS NOT NULL
    GROUP BY review_date
    ORDER BY review_date DESC
""")

print(f"Writing date-wise review count to {s3_analytics_path}date_wise_reviews/")
date_wise_frame = DynamicFrame.fromDF(df_date_wise_reviews.repartition(1), glueContext, "date_wise_df")
glueContext.write_dynamic_frame.from_options(
    frame=date_wise_frame,
    connection_type="s3",
    connection_options={"path": s3_analytics_path + "date_wise_reviews/"},
    format="csv"
)

# ========================================
# QUERY 3: Top 5 Most Active Customers
# ========================================
# This query identifies "power users" by finding customers with the most reviews
df_top_customers = spark.sql("""
    SELECT 
        customer_id,
        COUNT(*) as total_reviews,
        AVG(rating) as avg_rating
    FROM product_reviews
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
    ORDER BY total_reviews DESC
    LIMIT 5
""")

print(f"Writing top 5 customers to {s3_analytics_path}top_customers/")
top_customers_frame = DynamicFrame.fromDF(df_top_customers.repartition(1), glueContext, "top_customers_df")
glueContext.write_dynamic_frame.from_options(
    frame=top_customers_frame,
    connection_type="s3",
    connection_options={"path": s3_analytics_path + "top_customers/"},
    format="csv"
)

# ========================================
# QUERY 4: Overall Rating Distribution
# ========================================
# This query shows the count for each star rating (1-star, 2-star, etc.)
df_rating_distribution = spark.sql("""
    SELECT 
        rating,
        COUNT(*) as rating_count,
        ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ()), 2) as percentage
    FROM product_reviews
    WHERE rating IS NOT NULL AND rating > 0
    GROUP BY rating
    ORDER BY rating DESC
""")

print(f"Writing rating distribution to {s3_analytics_path}rating_distribution/")
rating_dist_frame = DynamicFrame.fromDF(df_rating_distribution.repartition(1), glueContext, "rating_dist_df")
glueContext.write_dynamic_frame.from_options(
    frame=rating_dist_frame,
    connection_type="s3",
    connection_options={"path": s3_analytics_path + "rating_distribution/"},
    format="csv"
)

# Commit the job
job.commit()
