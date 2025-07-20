from services.base_service import BaseService
from classes.APIRetrieval import APIRetrieval
from classes.CloudStorageUtils import CloudStorageUtils
import json
import os
import uuid
from datetime import datetime
import logging


class ServiceRetail(BaseService):
    """
    Service in charge of retrieving retail data from API and storing it to cloud storage
    """

    def __init__(self):
        name = "retail"
        super().__init__(name)
        self.config = None
        self.url = ""
        self.api_client = None
        self.storage_client = None
        self.logger = logging.getLogger("retail_logger")
        self.logger.setLevel(logging.INFO)

    def _load_api_config(self, service):
        """Load API configuration from config/service_api.json"""
        config_path = os.path.join("src","config", "service_api.json")
        try:
            with open(config_path, "r") as f:
                content = json.load(f)
            return content.get(service)
        except FileNotFoundError:
            raise FileNotFoundError(f"API configuration file not found: {config_path}")

    def _setup_clients(self):
        """Initialize API and Cloud Storage clients"""
        # Initialize API client (will be mocked)
        self.api_client = APIRetrieval(self.url, "mock_api_key")

        # Initialize Cloud Storage client (will be mocked)
        self.storage_client = CloudStorageUtils(self.config)

    def _retrieve_and_store_data(self, endpoint, sales_date=None):
        """
        Retrieve data from API endpoint and store to cloud storage
        Args:
            endpoint: API endpoint ('sales', 'products', 'customers')
        """
        limit = 250  # Max selon l'API
        page = 0
        # On peut utiliser des routines
        while True:
            self.logger.info(f"Processing batch for endpoint {endpoint} (page: {page})")

            try:
                # Call API for current batch
                response = self.api_client.get_page_data(endpoint, sales_date, limit)

                # Extract items and metadata from response
                items = response.get("items", [])
                total_items = response.get("total_items", 0)

                # Check if we have data
                if not items or len(items) == 0:
                    self.logger.info(
                        f"No more data for {endpoint}, stopping pagination"
                    )
                    break

                self.logger.info(
                    f"Retrieved {len(items)} records from {endpoint} (total: {total_items})"
                )

                # Generate filename: {service}_{endpoint}_{YYYYMMDD_HHmm}_{uuid}.json
                timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                unique_id = str(uuid.uuid4())
                filename = f"retail_{endpoint}_{timestamp}_{unique_id}.json"

                # Convert data to JSON string for storage
                data_json = json.dumps(items, indent=2)

                # Store data to cloud storage (mocked)
                success = self.storage_client.upload_data(data_json, filename)

                if success:
                    self.logger.info(
                        f"Successfully stored {endpoint} batch data to {filename}"
                    )
                else:
                    self.logger.error(
                        f"Failed to store {endpoint} batch data to {filename}"
                    )
                    break

                # On a pas d'info sur comment on fait la pagination
                page += 1
                if len(items) < 250:
                    break

            except Exception as e:
                self.logger.error(f"Error processing {endpoint} batch: {str(e)}")
                raise

    def execute(self, config):
        """
        Main function for the service.
        Retrieves data from all API endpoints and stores them to cloud storage
        Args:
            config: Dict from cmd line args
        Return:
            None
        """
        self.config = config
        self.url = self._load_api_config(config.get("service"))

        # Setup API and storage clients
        self._setup_clients()

        self._retrieve_and_store_data(config.get("endpoint"), config.get("start_date"))

        self.logger.info("Retail data synchronization completed")
