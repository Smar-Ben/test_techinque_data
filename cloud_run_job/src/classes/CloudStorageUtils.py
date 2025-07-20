class CloudStorageUtils:
    """
    Utility class for interacting with Google Cloud Storage (GCS).
    Args:
        config (dict): Configuration dictionary containing the GCP project ID.
    Attributes:
        client (google.cloud.storage.Client): Client instance for accessing GCS.
    """

    def __init__(self, config):
        self.config = config

    def upload_data(self, data_json, filename):
        return True
