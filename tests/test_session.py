import base64
import os
import ast
import unittest
from loguru import logger
from pycalrissian.context import CalrissianContext

os.environ["KUBECONFIG"] = "~/.kube/kubeconfig-t2-dev.yaml"


class TestCalrissianExecution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logger.info(f"-----\n------------------------------  unit test for test_session.py   ------------------------------\n\n")
        cls.namespace = "deleted-namespace"

        username = "fabricebrito"
        password = "1f54397c-f15c-4be4-b9ea-4220fb2d80ce"
        email = "fabrice.brito@terradue.com"
        registry = "https://index.docker.io/v1/"

        auth = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode(
            "utf-8"
        )

        secret_config = {
            "auths": {
                registry: {
                    "username": username,
                    "password": password,
                    "email": email,
                    "auth": auth,
                },
                "registry.gitlab.com": {
                    "auth": "Z2l0bGFiK2RlcGxveS10b2tlbi04NzY3OTQ6Vnc3Z1NpSHllaVlwLS0zUnEtc3o="  # noqa: E501
                },
            }
        }

        session = CalrissianContext(
            namespace=cls.namespace,
            storage_class="standard",
            volume_size="1G",
            image_pull_secrets=secret_config,
        )

        session.initialise()

        cls.session = session

    
        
        