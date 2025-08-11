from dagster import job, op
import subprocess
from datetime import date, timedelta

@op
def run_legal_data_spider():
    today = date.today()
    first_day_prev_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
    last_day_prev_month = today.replace(day=1) - timedelta(days=1)

    start_date = first_day_prev_month.strftime("%d-%m-%Y")
    end_date = last_day_prev_month.strftime("%d-%m-%Y")

    subprocess.run(["scrapy", "crawl", "get_legal_data", "-a", f"start_date={start_date}", "-a", f"end_date={end_date}"], check=True)

@job
def legal_data_job():
    run_legal_data_spider()