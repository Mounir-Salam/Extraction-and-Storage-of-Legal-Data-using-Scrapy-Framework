from dagster import repository
from .jobs import legal_data_job
from .schedules import run_legal_data_schedule

@repository
def legal_data_repo():
    return [legal_data_job, run_legal_data_schedule]