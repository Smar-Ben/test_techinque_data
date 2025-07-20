# Retail Data Connector

Ce projet est un connecteur Python permettant de récupérer des données depuis une API REST (mockée) et de les stocker dans Google Cloud Storage. Il est conçu pour être exécuté dans un environnement Cloud Run et supporte plusieurs services métiers.

## 🗂 Structure du projet

project/
├── src/
│ ├── classes/ # Interfaces vers des services externes (API, GCS), mockées pour les tests
│ ├── config/ # Fichiers JSON de configuration (API, services Cloud Run)
│ ├── services/ # Contient les services métiers (ex: retail)
│ └── utils/ # Fonctions utilitaires (ex: argument parser)
├── test/ # Dossier de tests unitaires
└── pyproject.toml # Dépendances gérées avec uv

## 📦 Services disponibles

### `retail`

Le service `retail` est responsable de la synchronisation des données liées au domaine retail. Il utilise 3 endpoints de l’API :

- `/sales`
- `/customers`
- `/products`

Les données sont récupérées depuis l’API (mock) puis stockées dans un bucket GCS (mocké également).

## ⚙️ Arguments en ligne de commande

Le programme accepte les arguments suivants :

| Argument       | Description                                                | Obligatoire |
| -------------- | ---------------------------------------------------------- | ----------- |
| `--service`    | Nom du service à exécuter (ex: `retail`)                   | ✅ Oui      |
| `--endpoint`   | Endpoint spécifique à appeler (`sales`, `customers`, etc.) | ✅ Oui      |
| `--start_date` | Date de départ pour les données (format libre, optionnel)  | ❌ Non      |

## 🚀 Exécution

Le projet utilise [`uv`](https://github.com/astral-sh/uv) pour la gestion des dépendances. Il faut juste installer uv avant 2. Lancer le connecteur.
Pour synchroniser les dépendances:

```bash
uv sync
```

Exemple de commande:

```bash
uv run  src/main.py --service retail --endpoint sales --start_date 2024-07-01
```

## 🧪 Tests

Les tests seront ajoutés dans le dossier test/. Les appels aux API et à GCS sont mockés, ce qui permet une exécution locale sans connexion aux services externes.
