import os
import time 
import docker
import docker.errors
import requests

class DockerDeployer:
    def __init__(self):
        self.client = docker.from_env()

        self.network = os.environ.get("DOCKER_NETWORK", "deployml_default")
        self.image = os.environ.get("MODEL_SERVER_IMAGE", "deployml-model-server:latest")

        self.artifacts_volume = os.environ.get("ARTIFACTS_VOLUME", "deplyml_artifacts")

    def start_model_server(
            self,
            deployment_id: str,
            model_path: str,
    ) -> tuple[str,str]:
        container_name = f"deployml-ms-{deployment_id}"
        internal_url = f"http://{container_name}:8000"

        try:
            old = self.client.containers.get(container_name)
            old.remove(force=True)
        except docker.errors.NotFound:
            pass

        self.client.containers.run(
            image=self.image,
            name=container_name,
            detach=True,
            network=self.network,
            environment={"MODEL_PATH": model_path},
            volumes={
                self.artifacts_volume : {"bind": "/artifacts", "mode": "rw"}
            },
            restart_policy={"Name": "always"},
        )
        return container_name, internal_url

    def wait_for_health(self,internal_url: str, timeout_seconds: int = 20) -> bool:
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            try:
                r = requests.get(f"{internal_url}/health", timeout=1.5)
                if r.status_code == 200:
                    return True
            except Exception:
                pass
            time.sleep(0.8)
        return False
    def stop_and_remove(self,container_name: str) -> None:
        try:
            c = self.client.containers.get(container_name)
            c.remove(force=True)
        except docker.errors.NotFound:
            return