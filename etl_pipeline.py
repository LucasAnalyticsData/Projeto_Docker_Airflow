from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
import sqlite3
import os
from pathlib import Path
import logging

# Caminhos baseados no seu docker-compose:
# - /opt/airflow/dags  -> bind mount do Windows (apenas leitura do arquivo de entrada)
# - /opt/airflow/logs  -> volume Docker (estável no Windows; usaremos para saída)
DAGS_DIR = Path("/opt/airflow/dags")
DATA_DIR = Path("/opt/airflow/logs/data")  # volume Docker (persistente e sem problemas de lock)
DATA_DIR.mkdir(parents=True, exist_ok=True)

INPUT_CSV = DAGS_DIR / "Tipo_de_transacao.csv"
CARREGADO_CSV = DATA_DIR / "dados_carregados.csv"
TRANSFORMADO_CSV = DATA_DIR / "dados_transformados.csv"
SQLITE_DB = DATA_DIR / "meu_banco.db"

log = logging.getLogger("airflow.task")

def load_file():
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Arquivo de entrada não encontrado: {INPUT_CSV}")
    # Tenta delimitador ';' e faz fallback para ','
    try:
        df = pd.read_csv(INPUT_CSV, encoding="latin-1", delimiter=";")
    except Exception as e:
        log.warning("Falha com ';' (%s). Tentando ',' ...", str(e))
        df = pd.read_csv(INPUT_CSV, encoding="latin-1", delimiter=",")
    df.to_csv(CARREGADO_CSV, index=False, encoding="utf-8")
    log.info("Arquivo carregado com sucesso. Amostra:\n%s", df.head().to_string())

def transform_data():
    if not CARREGADO_CSV.exists():
        raise FileNotFoundError(f"CSV carregado não existe: {CARREGADO_CSV}")
    df = pd.read_csv(CARREGADO_CSV, encoding="utf-8")
    # Exemplo simples de transformação
    if "Tipo" in df.columns:
        df = df.rename(columns={"Tipo": "Categoria"})
    df = df.head(10)
    df.to_csv(TRANSFORMADO_CSV, index=False, encoding="utf-8")
    log.info("Transformação concluída. Amostra:\n%s", df.head().to_string())

def save_to_sqlite():
    if not TRANSFORMADO_CSV.exists():
        raise FileNotFoundError(f"CSV transformado não existe: {TRANSFORMADO_CSV}")
    # Usa o volume Docker para o SQLite (evita problemas de lock no bind mount do Windows)
    conn = sqlite3.connect(SQLITE_DB.as_posix())
    try:
        df = pd.read_csv(TRANSFORMADO_CSV, encoding="utf-8")
        df.to_sql("transacoes", conn, if_exists="replace", index=False)
        log.info("Dados gravados no SQLite em %s", SQLITE_DB)
    finally:
        conn.close()

with DAG(
    dag_id="etl_pipeline_2",
    start_date=datetime(2025, 3, 16),
    schedule=None,          # em Airflow 2.9 prefira 'schedule' em vez de 'schedule_interval'
    catchup=False,
    tags=["exemplo", "etl"],
) as dag:
    load = PythonOperator(task_id="load_file", python_callable=load_file)
    transform = PythonOperator(task_id="transform_data", python_callable=transform_data)
    save = PythonOperator(task_id="save_to_sqlite", python_callable=save_to_sqlite)

    load >> transform >> save
