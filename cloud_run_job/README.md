# Retail Data Connector

Ce projet est un connecteur Python permettant de récupérer des données depuis une API REST (mockée) et de les stocker dans Google Cloud Storage. Il est conçu pour être exécuté dans un environnement Cloud Run et supporte plusieurs services métiers.

## 🗂 Structure du projet

```
project/
├── src/
│ ├── classes/ # Interfaces vers des services externes (API, GCS), mockées pour les tests
│ ├── config/ # Fichiers JSON de configuration (API, services Cloud Run)
│ ├── services/ # Contient les services métiers (ex: retail)
│ └── utils/ # Fonctions utilitaires (ex: argument parser)
├── test/ # Dossier de tests unitaires
└── pyproject.toml # Dépendances gérées avec uv
```

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

## 🧠 Améliorations

Le code actuel peut être significativement optimisé. Voici les pistes d'amélioration identifiées :

- **Appels API asynchrones** :  
  Actuellement, les appels API sont faits de manière séquentielle. Avec plus de **6000 enregistrements par heure** et environ **250 entrées par réponse**, une approche asynchrone permettrait de **réduire le temps de traitement** et **d'augmenter les performances**.

- **Gestion de la pagination** :  
  La pagination peut être prise en compte en calculant le nombre total de pages via la formule ceil(total_items / limit), en tenant compte de la limite maximale de 250 items par page imposée par l'API. Le mécanisme d'accès aux pages suivantes n'est pas spécifié dans la documentation Swagger et nécessite une investigation supplémentaire (offset, numéro de page, ou système de curseurs).
- **Stratégie de reprise sur échec** :
  Implémenter un système de checkpoint granulaire par page pour reprendre le traitement exactement où il s'est arrêté en cas d'échec, évitant ainsi le retraitement complet des données déjà récupérées.

- **Création d’un Dockerfile** :  
   Pour faciliter le **déploiement** et l’**exécution reproductible** du job, il serait pertinent de créer un `Dockerfile` afin de déployer le cloud run jobs
