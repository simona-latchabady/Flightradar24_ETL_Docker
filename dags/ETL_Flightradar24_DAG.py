
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy_operator import DummyOperator
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../ETL_Flightradar24'))


from ETL_Flightradar24 import extraction_transform, load
current_datetime = datetime.now()

# Définition des paramètres du DAG
default_args = {
  'owner': 'OWNER',
  'depends_on_past': False,
  'start_date': datetime(current_datetime.year, current_datetime.month, current_datetime.day),
}

# Définition du DAG
dag = DAG(
  'ETL_Flightradar24_workflow',
  default_args=default_args,
  schedule_interval=timedelta(hours=2),
)

# Tâches du DAG
start_task = DummyOperator(task_id='start', dag=dag)
end_task = DummyOperator(task_id='end', dag=dag)

# Tâches d'extraction et de transformation de données
extract_transform_task = PythonOperator(
  task_id = 'extract_transform_data',
  python_callable = extraction_transform,
  retries = 2,
  retry_delay = timedelta(minutes=30),
  dag=dag,
)

# Tâches de chargement de données
load_task = PythonOperator(
  task_id='load_data',
  python_callable=load,
  retries = 2,
  retry_delay = timedelta(minutes=5),
  dag=dag,
)


# Définir les dépendances entre les tâches
start_task >> extract_transform_task >> load_task >> end_task