import requests


class APIRetrieval:
    """
    Simple client pour récupérer des données d'une API REST avec pagination
    Inclut des données mockées pour les tests
    """

    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.api_key = api_key

    def get_page_data(self, endpoint, sales_date, limit):
        """
        Récupère les données d'une page spécifique
        Mode MOCK -On simule le retour juste on appelle _call_api
        """

        return self._get_mock_data(endpoint)

    def _get_mock_data(self, endpoint):
        """
        Retourne des données mockées selon l'endpoint
        """
        mock_data = {
            "sales": {
                "items": [
                    {
                        "id": 764,
                        "datetime": "2024-07-18 13:23:28",
                        "total_amount": 130.4,
                        "items": [
                            {
                                "product_sku": "SKU23456787654",
                                "quantity": 2,
                                "amount": 65.2,
                            }
                        ],
                        "customer_id": "CS3456789",
                    },
                    {
                        "id": 765,
                        "datetime": "2024-07-18 14:15:33",
                        "total_amount": 89.99,
                        "items": [
                            {
                                "product_sku": "SKU98765432101",
                                "quantity": 1,
                                "amount": 89.99,
                            }
                        ],
                        "customer_id": "CS9876543",
                    },
                ],
                "total_items": 2,
            },
            "products": {
                "items": [
                    {
                        "product_sku": "SKU23456787654",
                        "description": "Produit de test A",
                        "unit_amount": 32.6,
                        "supplier": "MyLittlePony",
                    },
                    {
                        "product_sku": "SKU98765432101",
                        "description": "Produit de test B",
                        "unit_amount": 89.99,
                        "supplier": "SupplierTest",
                    },
                ],
                "total_items": 2,
            },
            "customers": {
                "items": [
                    {
                        "customer_id": "CS3456789",
                        "emails": ["client1@test.com", "client1.alt@test.com"],
                        "phone_numbers": ["+33630896746", "06.89.56.90.45"],
                    },
                    {
                        "customer_id": "CS9876543",
                        "emails": ["client2@example.org"],
                        "phone_numbers": ["+33612345678"],
                    },
                ],
                "total_items": 2,
            },
        }

        data = mock_data.get(endpoint, [])
        return data

    def _call_api(self, endpoint, params):
        """
        Fait un appel API avec retry simple
        (Non utilisé en mode mock, gardé pour la vraie implémentation)
        """
        url = f"{self.base_url}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self._get_secret_manager}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            raise e

    def _get_secret_manager():
        """On récupére l'api key du secret manager"""
        return "key"
