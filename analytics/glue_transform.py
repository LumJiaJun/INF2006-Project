import sys

from awsglue.utils import getResolvedOptions
from pyspark.sql import SparkSession
from pyspark.sql import functions as functions


arguments = getResolvedOptions(sys.argv, ["RAW_LISTINGS_URI", "PROCESSED_LISTINGS_URI"])
spark = SparkSession.builder.appName("airbnb-listings-transform").getOrCreate()

raw = (
    spark.read.option("header", "true")
    .option("multiLine", "true")
    .option("quote", '"')
    .option("escape", '"')
    .csv(arguments["RAW_LISTINGS_URI"])
)

listings = raw.select(
    functions.col("neighbourhood"),
    functions.col("property_type"),
    functions.col("room_type"),
    functions.col("city"),
    functions.col("price").cast("double").alias("price"),
    functions.col("accommodates").cast("integer").alias("accommodates"),
    functions.col("bedrooms").cast("double").alias("bedrooms"),
    functions.col("minimum_nights").cast("integer").alias("minimum_nights"),
    functions.col("review_scores_rating").cast("double").alias("review_scores_rating"),
    (functions.col("instant_bookable") == "t").alias("instant_bookable"),
    (functions.col("host_is_superhost") == "t").alias("host_is_superhost"),
)

valid = listings.filter(
    functions.col("city").isNotNull()
    & functions.col("neighbourhood").isNotNull()
    & functions.col("property_type").isNotNull()
    & functions.col("room_type").isNotNull()
    & (functions.col("price") > 0)
    & (functions.col("accommodates") > 0)
    & (functions.col("minimum_nights") > 0)
)

city_thresholds = valid.groupBy("city").agg(
    # A per-city boundary avoids letting extreme luxury prices dominate typical-market summaries.
    functions.expr("percentile_approx(price, 0.99, 10000)").alias("maximum_supported_price")
)
processed = (
    valid.join(city_thresholds, "city")
    .filter(functions.col("price") <= functions.col("maximum_supported_price"))
    .drop("maximum_supported_price")
)

(
    processed.write.mode("overwrite")
    .partitionBy("city")
    .parquet(arguments["PROCESSED_LISTINGS_URI"])
)
