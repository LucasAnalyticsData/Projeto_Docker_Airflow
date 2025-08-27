# -----------------------------------------------------------------------------
# Dockerfile — Airflow 2.9.1 (python3.11) + libs de Engenharia de Dados
# Instala pacotes como usuário 'airflow' e usa constraints oficiais
# -----------------------------------------------------------------------------
FROM apache/airflow:2.9.1-python3.11

LABEL org.opencontainers.image.title="Airflow Custom" \
      org.opencontainers.image.description="Airflow 2.9.1 com libs de dados" \
      maintainer="Lucas"

# Pacotes de sistema mínimos (somente o necessário)
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential curl git unzip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Volta para o usuário airflow (regra da imagem oficial p/ pip)
USER airflow

# Constraints do Airflow (evitam 'dependency hell')
ARG AIRFLOW_VERSION=2.9.1
ARG PYTHON_VERSION=3.11
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

# Copia requirements e instala com constraints (sem forçar upgrade de pip)
COPY --chown=airflow:root requirements.txt /opt/airflow/requirements.txt
RUN pip install --no-cache-dir --constraint "${CONSTRAINT_URL}" -r /opt/airflow/requirements.txt

WORKDIR /opt/airflow

