# Retail Data Pipeline - Architecture & Design

## 🎯 Objectif

Construire un pipeline de données robuste pour ingérer, transformer et mettre à disposition des données retail provenant d'une API REST dans un environnement analytique SQL compatible avec les outils de Business Intelligence.

## 📋 Contexte

- **Source** : API REST retail (authentification par API key, format JSON)
- **Volume** : 1000 nouveaux enregistrements toutes les 10 minutes (~6000/heure)
- **Fréquence** : Rafraîchissement toutes les heures
- **Destination** : Base de données analytique requêtable en SQL
- **Endpoints disponibles** : Sales, Products, Customers
- **Doublons**: On suppose que l’API ne renvoie pas de doublons pour une même période (hypothèse à valider auprès du fournisseur si possible)
- **Préparation aux besoins futurs** : La table Customers, bien que non utilisée pour l’instant, est intégrée dès maintenant afin d’anticiper de futurs besoins.

## 🏗️ Architecture GCP

### Composants utilisés

| Composant            | Rôle               | Justification                                                                                                                              |
| -------------------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ |
| **BigQuery**         | Data Warehouse     | • Traitement de gros volumes • Requêtable en SQL et optimisé pour l'analytique • Serverless, pas de gestion d'instances                    |
| **Cloud Composer**   | Orchestration      | • Airflow managé, outil de référence pour l'orchestration • Personnalisation complète des workflows                                        |
| **Cloud Run Jobs**   | Connecteur API     | • Cloud Run Jobs utilisé pour des tâches longues en mode batch (contrairement aux Cloud Functions qui traitent des tâches événementielles) |
| **Cloud Storage**    | Stockage fichiers  | • Solution optimale pour le stockage d'objets • Intégration native avec BigQuery • Archivage et audit des fichiers                         |
| **Cloud Monitoring** | Observabilité      | • Alerting sur les ressources Composer • Alerting et visualisation des coûts sur BigQuery                                                  |
| **Secret Manager**   | Gestion des secret | • Stockage sécurisé de l'API key • Rotation automatique des secrets • Intégration native avec Cloud Run                                    |

## ⚙️ Cloud Run Jobs - Connecteurs API

### Fonctionnalités

- **Authentification** : API key stockée dans Secret Manager (sur GCP)
- **Pagination automatique** : Gestion des limites API (max 250 items/page)
- **Génération de fichiers uniques** : `{endpoint}_{YYYYMMDD_HHmm}_{uuid}.json`
- **Retry policy** : 3 tentatives avec exponential backoff
- **Idempotence** : Reprise granulaire par page avec checkpoint (évite le retraitement complet en cas d'échec)
- **Traitement asynchrone** : Pagination non-bloquante pour optimiser les performances
- **Initialisation dynamique** : Récupération de la date de départ depuis BigQuery pour éviter les doublons

### Arguments du Cloud Run Job

--endpoint : Endpoint à traiter (sales/products/customers)
--start_sales_id : Date optionnelle au format YYYY-MM-DD (par défaut : date courante)

### Stratégies par endpoint

- **Sales** : Incrémental via `start_sales_id`
- **Products/Customers** : Full refresh (pas d'API incrémentale)

## 📊 Structure des données

### Organisation des datasets BigQuery

On va organiser nos donnée avec une architecture en médaillon

```
📂 raw/                 # Données brutes de l'API
├── sales_api
├── products_api
└── customers_api

📂 ods/                 # Données nettoyées et exploitables
├── sales_clean
├── products_clean
└── customers_clean

📂 dmt/                 # Tables finales pour la BI (les data analysts auront accès uniquement à cette table)
└── sales_final
```

### Schémas des tables principales

#### Dataset RAW

Contient trois tables (par types de fichier): sales, products et customers
Il faut partitionné ces tables par date d'ingestion (valeur SYS_DATE_CREATE) et stocker le nom du fichier (SYS_FILE_NAME)
Chaque table va être alimenté en append

```sql
-- Un enregistrement = une ligne de vente
CREATE TABLE raw.sales (
    id STRING,
    datetime STRING,
    total_amount STRING,
    customer_id STRING,
    items ARRAY<STRUCT<
        product_sku STRING,
        quantity STRING,
        amount STRING
    >>,
    SYS_DATE_CREATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    SYS_FILE_NAME STRING
) PARTITION BY DATE(SYS_DATE_CREATE);

-- Un enregistrement = un produit
CREATE TABLE raw.customers (
    customer_id STRING,
    emails ARRAY<STRING>,
    phone_numbers ARRAY<STRING>,
    SYS_DATE_CREATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    SYS_FILE_NAME STRING
) PARTITION BY DATE(SYS_DATE_CREATE);

-- Un enregistrement = un client
CREATE TABLE raw.products (
    product_sku STRING,
    description STRING,
    unit_amount STRING,
    supplier STRING,
    SYS_DATE_CREATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    SYS_FILE_NAME STRING
) PARTITION BY DATE(SYS_DATE_CREATE);
```

#### Dataset ODS

Contient trois tables (par types de fichier): sales, products et customers
On va avoir les données qui pourront être exploité par notre dmt et on va transformer la donnée dans cette table.
Aussi il faut s'assurer de récupérer uniquement les données non traité

```sql
-- Mode d'ingestion toujours en append, on ne devra pas stocker deux fois car controléé en amont via l'api
-- Si on a pas le contrôle alors on passe en merge avec
CREATE TABLE ods.sales (
    id INTEGER,
    datetime DATETIME,
    total_amount NUMERIC,
    customer_id STRING,
    items ARRAY<STRUCT<
        product_sku STRING,
        quantity INTEGER,
        amount NUMERIC
    >>,
    SYS_DATE_CREATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    SYS_FILE_NAME STRING
) PARTITION BY DATE(datetime);

-- Mode d'ingestion merge pour les customers, si on trouve une nouvelle information on va l'écraser
-- Remarque: pour l'instant en merge j'écrase mais on peut faire une évolution pour gérer le changement (colonne SCD2)
CREATE TABLE ods.customers (
    customer_id STRING,
    emails ARRAY<STRING>,
    phone_numbers ARRAY<STRING>,
    SYS_DATE_CREATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    SYS_FILE_NAME STRING
);

-- Mode d'ingestion merge pour les products, si on trouve une nouvelle information on va l'écraser
CREATE TABLE ods.products (
    product_sku STRING,
    description STRING,
    unit_amount NUMERIC,
    supplier STRING,
    SYS_DATE_CREATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    SYS_FILE_NAME STRING
);
```

#### Dataset dmt

Contient uniquement notre table finale qui va être exploité par la BI

```sql
-- Mode d'ingestion toujours en append, on ne devra pas stocker deux fois car controléé en amont via l'api
-- Si on a pas le contrôle alors on passe en merge avec
CREATE TABLE dmt.sales_items (
    id STRING,--on veut avoir la clé sur une seule ligne donc concat entre sales.id et product.sku (séparation avec -)
    sales_datetime DATETIME,
    item_amount NUMERIC,
    product_sku STRING,
    item_quantity INTEGER,
    product_description STRING,
    discount_perc NUMERIC,
);

```

### Optimisations BigQuery

- **Ajout du clustering**: Voir selon nos besoin, mais le clustering peut être utile pour améliorer la performance de nos requêtes
- **Ajout des description**: Ajouter les description sur nos tables pour avoir maximumn d'info
- **Ajout de contrainte**: On peut ajouter les primary key et foreign key sur nos tables pour améliorer les jointure

### Architecture des fichiers Cloud Storage

```
📂 gs://<bucket>/
sales/
├── in/                      # Fichiers JSON en attente de traitement
├── processing/              # Fichiers JSON en cours de traitement

├── archive/                 # Fichiers traités avec succès
│   ├── 20250719/
│   └── 20250718/
└── failed/                  # Fichiers en erreur lors du traitement
│   ├── 2024/01/15/10h/
│   └── ...
products/
├── in/
├── archive/
└── failed/
customers/
├── in/
├── archive/
└── failed/
```

## 🔄 Pipeline de données

### Vue d'ensemble du flux

```
API REST → Cloud Run Jobs → Cloud Storage → BigQuery (raw) → BigQuery (ods) → BigQuery (dmt) → Data Analysts
```

### Architecture des DAGs Airflow

#### 1. DAGs d'ingestion (x3)

- `dag_ingest_sales`: déclenché toutes les heures (0 \* \* \* \*)
- `dag_ingest_products`: déclenché une fois par jour (0 0 \* \* \*)
- `dag_ingest_customers`: déclenché une fois par jour (0 0 \* \* \*)

**Remarque** : Il est nécessaire de rafraîchir entièrement les données products et customers à chaque exécution, car l'API ne fournit pas de mécanisme d'incrémentation ou de filtrage (pas de updated_at, pas de pagination différentielle). Cela implique un dump complet à chaque fois, ce qui peut devenir lourd en volume et coûteux en traitement à mesure que les données croissent.

**Workflow par DAG :**

1. **Extract** : Appel API via Cloud Run Job avec gestion de la pagination et sauvegarde des fichiers JSON dans Cloud Storage
2. **File to RAW** : Insertion des données dans BigQuery (mode APPEND) dans le dataset raw (via un script dans airflow déplacer les fichier en erreur)
3. **RAW to ODS** : Transformation de la donnée pour insérer dans le dataset ods (zone silver) avec données nettoyées et exploitables
4. **Archive** : Déplacement des fichiers vers archive/ ou failed/ (en fonction du résultat de la requête)

Remarque: on peut ajouter une étape intermédiaire pour stocker la date de la dernière insertion (si elle a réussi ou non) pour exploiter cette information lors des prochaines exécutions

#### 2. DAG de transformation finale

- `dag_transform_final`

**Déclenchement :** Via Dataset (Asset) Airflow qui est déclenché à la fin du `dag_ingest_sales`

**Workflow :**

1. **Load Final** : Insertion des nouvelles données dans la table `sales_final` dans dmt

   Remarque : on suppose qu'on insère pas les sales qui n'ont pas de produit ou customer référencé dans la table finale

## ⚠️ Gestion des erreurs et qualité des données

### Qualité de données

Pour l'instant, il n'y a pas de gestion de qualité de données, mais plusieurs approches sont possibles :

**Gestion des orphelins** : le plus important pour les data analysts, ce sont les orphelins, on peut créer une table dans le dag `dag_ingest_sales`

**Métriques de qualité de données** : il est possible d'utiliser des outils plus poussés comme **dbt** et/ou **Great Expectations** afin de valider la qualité de nos données directement dans nos dags

### Gestion des échecs d'ingestion

**Processus :**

1. **Échec détecté** → Déplacement du fichier vers `failed/`
2. **Logging** → Enregistrement de l'erreur au sein de la tâche airflow
3. **Notification** → Alerte Airflow vers l'équipe Data Engineering (on peut spécifier une liste de mails en cas d'échec)
4. **Investigation** → Analyse du fichier brut pour debugging
5. **Rejeu** → Possibilité de reprocesser depuis `failed/`

**Évolution** : construire un dashboard de monitoring, pour chaque étape impliquant des tables BigQuery, on ajoute le résultat dans une table airflow qui va être exploitée par un dashboard (un exemple comme un autre), on peut observer la volumétrie

## 🔍 Monitoring et observabilité

- **Volume** : Nombre d'enregistrements ingérés par endpoint
- **Qualité** : Taux d'orphelins, erreurs de format
- **Performance** : Temps d'exécution des DAGs
- **Fiabilité** : Taux de succès des ingestions
- **Alerting** : En cas d'échec d'ingestion → Notification immédiate

## 🏗️ Infrastructure & Déploiement

### Gestion de l'infrastructure

- **Infrastructure as Code** : Terraform pour provisionner et gérer les ressources GCP (Composer, Cloud Run, datasets BigQuery, IAM)
- **Environnements** : Séparation dev/prod avec workspaces Terraform distincts (nombre d'environnements à définir selon les besoins)

## CI/CD Pipeline

- **Versioning**: Code stocké sur Git avec workflow basé sur les Pull Requests
- **CI (Continuous Integration)** : Tests automatiques obligatoires avant merge
- **CD (Continuous Deployement)** : Déploiement automatique après validation PR (DAGs Airflow,images Docker Cloud Run)
- **Outils** : Pipelines natifs du repository (GitHub Actions / GitLab CI)
- **Séparation des repos** : Projets distincts (Airflow, Cloud Run, Terraform) pour une meilleure gouvernance

### Stratégie de déploiement

- **Validation** : Code review obligatoire + tests automatisés
- **Déploiement** : Manuel via approbation
- **Rollback** : Capacité de retour arrière rapide en cas de régression

## Sécurité & Accès

- **Service Accounts** : Dédiés par composant avec principe du moindre privilège (service account pour composer, cloud run job, CD )
- **IAM** : Groupes IAM par profil métier : data analyste, data engineer
- **Secrets** : API keys et credentials dans Secret Manager
- **Gestion des données personnelles**: La solution ne prend pas en compte la data gouvernance

## 🚀 Évolutions & Améliorations

### Amélioration du pipeline de transformation

**dbt** (Data Build Tool) : Migration des transformations SQL vers dbt pour une meilleure gouvernance

- Tests de qualité de données intégrés
- Documentation automatique des modèles
- Lineage des données transparent
- Versioning des transformations

### Optimisation de l'ingestion

**API avec métier** : Collaboration pour faire évoluer l'API source

- Ajout de timestamps updated_at sur Products/Customers
- Endpoint de delta/changes pour éviter les full refresh

### Monitoring avancé

- **Great Expectations** : Validation automatique de la qualité des données (possible de coupler avec dbt)
- **Dashboard de monitoring** : Centralisation des métriques via une table de logs BigQuery alimentée par chaque DAG (volumétrie, temps d'exécution, taux de succès) et exploitée par un dashboard BI
