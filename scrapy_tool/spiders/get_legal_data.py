import scrapy
import re
import boto3
import traceback
from datetime import datetime
from scrapy.utils.project import get_project_settings


settings = get_project_settings()
class LegalDataSpider(scrapy.Spider):
    name = "get_legal_data"

    # The date will be assigned as the execution date of the code/pipeline in order to consistently connect the pipeline components
    def __init__(self, start_date=None, end_date=None, *args, **kwargs):
        super(LegalDataSpider, self).__init__(*args, **kwargs)
        self.start_date = start_date
        self.end_date = end_date
        self.domain = "https://www.workplacerelations.ie"

        if self.start_date is None or self.end_date is None:
            raise ValueError("start_date and end_date not provided")
        
        # Check date format and start_date is before end_date
        try:
            datetime.strptime(self.start_date, "%d-%m-%Y")
            datetime.strptime(self.end_date, "%d-%m-%Y")
            if datetime.strptime(self.start_date, "%d-%m-%Y") > datetime.strptime(self.end_date, "%d-%m-%Y"):
                raise ValueError

        except ValueError:
            raise ValueError("Incorrect data format (should be DD-MM-YYYY) or start_date is after end_date")

        self.base_urls = [
            f"https://www.workplacerelations.ie/en/search/?decisions=1&body=1&from={self.start_date}&to={self.end_date}",
            f"https://www.workplacerelations.ie/en/search/?decisions=1&body=2&from={self.start_date}&to={self.end_date}",
            f"https://www.workplacerelations.ie/en/search/?decisions=1&body=3&from={self.start_date}&to={self.end_date}",
            f"https://www.workplacerelations.ie/en/search/?decisions=1&body=15376&from={self.start_date}&to={self.end_date}"
        ]

        self.s3 = boto3.client(
            "s3",
            endpoint_url = settings.get("OBJECT_DB_ENDPOINT"),
            aws_access_key_id = settings.get("OBJECT_DB_CREDENTIALS"),
            aws_secret_access_key = settings.get("OBJECT_DB_PASSWORD"),
        )
        self.bucket_name = settings.get("BUCKET_NAME")
        # Create bucket if not exists
        try:
            self.s3.create_bucket(Bucket=self.bucket_name)
        except self.s3.exceptions.BucketAlreadyOwnedByYou:
            pass
    
    def start_requests(self):
        for base_url in self.base_urls:
            yield scrapy.Request(base_url, callback=self.parse)

    def parse(self, response):
        pages = 0
        hits = response.xpath("//div[contains(@class, 'searchhead')]/text()[normalize-space()]").get()

        if hits:
            try:
                hits = max(map(int, re.findall(r'\d+', hits)))
                pages = (hits // 10) + 1
                print("\nNumber of Hits Found for URL " + str(response.url) + ": " + str(hits))
                print("Number of Pages Found for URL " + str(response.url) + ": " + str(pages))
            except:
                print("\nNo hits found for URL " + str(response.url))

        if pages >= 1:
            for page in range(1, pages + 1):
                page_url = f"{response.url}&pageNumber={page}"
                print("\nRequesting URL " + str(page_url))
                yield scrapy.Request(page_url, callback=self.parse_page)
    
    def parse_page(self, response):
        try:
            items = response.xpath("//div[contains(@class, 'search-list')]//li[contains(@class, 'each-item')]").getall()
            if items:
                for item in items:
                    item = scrapy.Selector(text=item)
                    identifier = item.xpath(".//h2[@class='title']/a/@title").get()
                    if not identifier:
                        raise Exception("Identifier not found")
                    data = {
                        "identifier": identifier,
                        "description": item.xpath(".//p[@class='description']/text()[normalize-space()]").get(),
                        "publish_date": item.xpath(".//span[@class='date']/text()[normalize-space()]").get(),
                    }

                    # convert to monthly partionns
                    data["partition_date"] = datetime.strptime(data["publish_date"], "%d/%m/%Y").replace(day=1)
                    link_to_doc = item.xpath(".//a[contains(@class, 'btn-primary')]/@href").get()
                    
                    if not link_to_doc:
                        raise Exception("Link to document not found")
                    
                    if self.domain not in link_to_doc:
                        link_to_doc = self.domain + link_to_doc

                    if link_to_doc:
                        yield scrapy.Request(
                            link_to_doc,
                            callback=self.save_document,
                            meta = {
                                "metadata": data,
                                "link_to_doc": link_to_doc
                            }
                        )

            else:
                print("\nNo items found for URL " + str(response.url))
        except Exception as e:
            print("\nError while extracting data from URL " + str(response.url) + ": " + str(e))
            traceback.print_exc()
    
    def save_document(self, response):
        metadata = response.meta["metadata"]
        link_to_doc = response.meta["link_to_doc"]

        content_type = response.headers.get("Content-Type", b"").decode("utf-8").lower()
        if "pdf" in content_type:
            ext = ".pdf"
        else:
            ext = ".html"

        file_key = f"{metadata['identifier'].replace(' ', '_')}{ext}"

        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=file_key,
            Body=response.body,
            ContentType = content_type
        )

        yield {
            **metadata,
            "link_to_doc": link_to_doc,
            "storage_key": file_key,
            "storage_bucket": self.bucket_name,
        }