from dagster import schedule

from .jobs import run_scrapy_spider

@schedule(
    cron_schedule="0 2 1 * *",  # Run every month on the 1st at 2am UTC
    job=run_scrapy_spider,
    execution_timezone="UTC"
)
def run_legal_data_schedule():
    return {}

