# Extraction and Storage of Legal Data using Scrapy Framework

This tool is set up to extract relevant legal information from https://www.workplacerelations.ie and store them in MongoDB and an object storage using minIO.

## Requirements
- Tested on Python 3.10.11
- Install all requirements using `pip install -r requirements.txt`
- Create a MinIO docker container (or any other compatible object storage) and set up credentials in `scrapy_tool/settings.py`
- MongoDB (local or cloud) is required to store the data. Set up connection details in `scrapy_tool/settings.py`

## Usage

Navigate to the project directory and run the spider using `scrapy crawl get_legal_data`

The scraper will take 2 parameters to specify the published date range for the documents in the format `DD-MM-YYYY` as is compatible with the website's date format:

- `start_date`: e.g. "01-01-2023"
- `end_date`: e.g. "31-12-2023"

Example: `scrapy crawl get_legal_data -a start_date=01-01-2023 -a end_date=31-12-2023`

## Output

### In MongoDB

The following fields are stored in MongoDB:

- `identifier`: Unique identifier for each legal document
- `description`: Description of the legal document
- `publish_date`: Date the legal document was published
- `partition_date`: Partition date set to the first day of the month
- `link_to_doc`: URL of the legal document (can either lead to a PDF or another HTML page)
- `storage_key`: Object storage key for the legal document
- `storage_bucket`: Object storage bucket for the legal document

### In Object Storage

The legal documents are stored in the object storage in the specified bucket in the format `identifier.pdf` or `identifier.html` where `identifier` is the unique identifier for each legal document.

## Future Improvements
- Apply orchestration using Dagster to automatically trigger the scraper on a monthly basis to extract new data each month.
    
    - Recently set up local dagster orchesration framework (untested yet).