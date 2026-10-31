"""Run on the host after: python -m pip install mlflow==3.5.0"""
import os
import tempfile
from pathlib import Path
import mlflow

mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
mlflow.set_experiment("compose-smoke-test")
with mlflow.start_run():
    mlflow.log_param("deployment", "docker-compose")
    mlflow.log_metric("test_metric", 1.0)
    with tempfile.TemporaryDirectory() as directory:
        artifact = Path(directory) / "hello.txt"
        artifact.write_text("MLflow artifact upload works!\n")
        mlflow.log_artifact(str(artifact))
print("Success: run metadata and artifact uploaded")
