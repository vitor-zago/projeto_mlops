from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import io
import pandas as pd


def extract(**kw):
    df = pd.read_csv("/opt/airflow/data/dataset_pericias_papiloscopicas_1.csv")
    kw["ti"].xcom_push(key="raw", value=df.to_json())


def clean(**kw):
    raw = kw["ti"].xcom_pull(task_ids="extract", key="raw")
    df = pd.read_json(io.StringIO(raw))

    colunas_texto = ["Tipo_Pericia", "Tipo_Local", "Delegacia", "Tecnica_Utilizada"]
    for coluna in colunas_texto:
        df[coluna] = (
            df[coluna].str.lower().str.strip()
            .str.replace("_", " ", regex=False)
            .replace(r'\s+', ' ', regex=True)
        )

    colunas_numericas = ["Qtd_Objetos", "Qtd_Fotos", "Qtd_Fitas"]
    for coluna in colunas_numericas:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")
        df.loc[(df[coluna] < 0) | (df[coluna] >= 999999), coluna] = pd.NA

    df["Horario_Exame"] = pd.to_datetime(df["Horario_Exame"], errors="coerce")

    mapa_booleano = {
        "true": True, "1": True, "sim": True, "verdadeiro": True,
        "false": False, "0": False, "nao": False, "não": False, "falso": False,
    }
    for coluna in ["Violencia_Domestica", "Vitima_Idosa"]:
        df[coluna] = df[coluna].str.strip().str.lower().map(mapa_booleano)

    kw["ti"].xcom_push(key="clean", value=df.to_json())


def load(**kw):
    clean_data = kw["ti"].xcom_pull(task_ids="clean", key="clean")
    df = pd.read_json(io.StringIO(clean_data))
    df.to_csv("/opt/airflow/data/pericias_papiloscopicas_tratadas.csv", index=False)


with DAG(
    "ingestao_pericia_papiloscopica",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
) as dag:
    t1 = PythonOperator(task_id="extract", python_callable=extract)
    t2 = PythonOperator(task_id="clean", python_callable=clean)
    t3 = PythonOperator(task_id="load", python_callable=load)
    t1 >> t2 >> t3