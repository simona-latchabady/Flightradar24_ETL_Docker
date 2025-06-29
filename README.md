# ✈️ ETL Flightradar24 Project

[![Airflow](https://img.shields.io/badge/Orchestration-Airflow-blue)](https://airflow.apache.org/)
[![Docker](https://img.shields.io/badge/Container-Docker-blue)](https://www.docker.com/)
[![Status](https://img.shields.io/badge/Status-Prototype-orange)]()
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 📌 Description

Ce projet met en place un pipeline **ETL (Extract, Transform, Load)** pour automatiser la **collecte, le traitement et le stockage de données de trafic aérien en temps réel** à partir de **FlightRadar24**.
Il est orchestré avec **Apache Airflow** et exécuté dans un environnement **Docker Compose** pour garantir une configuration reproductible.

---

## ⚙️ Fonctionnalités principales

* **🔍 Extraction :** Données de vols récupérées via le module Python `FlightRadar24` (*non officiel*).
* **⚙️ Transformation :** Nettoyage, enrichissement et calculs avec **Pandas** et **PySpark**.
* **💾 Chargement :** Données exportées au format CSV et résultats synthétiques sauvegardés dans des fichiers `.txt`.
* **🗂️ Organisation :** Arborescence automatique des fichiers par date et par zone aérienne.
* **⏲️ Orchestration :** Pipeline automatisé et planifié toutes les 2 heures avec **Apache Airflow**.
* **📑 Logs :** Génération de logs détaillés pour chaque exécution.

---

## 🧱 Architecture technique

* **Python 3.8+**
* **Apache Airflow 2.7+**
* **Docker & Docker Compose**
* **PostgreSQL** pour la base de métadonnées Airflow.
* **PySpark** pour le traitement distribué et les agrégations.

---

## 🗂️ Structure du projet

```
📦 ETL_Flightradar24_Project
 ┣ 📂 dags/                → Contient le DAG Airflow
 ┣ 📂 ETL_Flightradar24/   → Module Python : extraction, transformation, chargement
 ┣ 📂 logs/                → Logs d'exécution Airflow
 ┣ 📂 Flights/             → Données de vol extraites (CSV)
 ┣ 📂 Results/             → Résultats agrégés (.txt)
 ┣ 📄 docker-compose.yml   → Configuration Docker
 ┣ 📄 requirements.txt     → Dépendances Python
 ┗ 📄 README.md            → Ce fichier
```

---

## 🚀 Lancement

1️⃣ **Cloner le dépôt**

```bash
git clone https://github.com/ton_user/ETL_Flightradar24_Project.git
cd ETL_Flightradar24_Project
```

2️⃣ **Configurer `.env` si nécessaire**

3️⃣ **Démarrer les conteneurs**

```bash
docker-compose up --build
```

4️⃣ **Accéder à l'interface Airflow**

* [http://localhost:8080](http://localhost:8080)
  *(Nom d’utilisateur / mot de passe par défaut : airflow / airflow)*

5️⃣ **Activer le DAG**

* `ETL_Flightradar24_workflow`
* Démarrer manuellement pour lancer un run ou attendre la planification automatique.

---

## 📊 DAG Workflow

Le diagramme montre la séquence `start → extract_transform_data → load_data → end` :

![DAG Workflow](docs/dag_diagram.png)

---

## ⚠️ Limitations et recommandations

* **Attention !** Le module `FlightRadar24` utilisé est basé sur le scraping du site, **non officiel**, et peut échouer si l’URL change ou si Cloudflare bloque les requêtes.
* Pour un usage en production, il est **fortement recommandé** d’utiliser l’API officielle Flightradar24 (*abonnement requis*) ou une alternative fiable (ex. : OpenSky Network, ADS-B Exchange).
* La version gratuite de l’API officielle peut ne pas suffire pour un volume élevé de requêtes.

---

## 🧩 Dépendances principales

* `apache-airflow`
* `pandas`
* `pyspark`
* `FlightRadar24` *(module Python non officiel)*
* `docker` / `docker-compose`

---

## 📜 Licence

Ce projet est sous licence **MIT**.
Utilisation à des fins éducatives uniquement — vérifiez les conditions d’utilisation de l’API Flightradar24.

---

**🚀 Bon vol et bon ETL !**
