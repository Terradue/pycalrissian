import base64
import os
import unittest

from pycalrissian.context import CalrissianContext

os.environ["KUBECONFIG"] = "/home/mambauser/.kube/microk8s.config"


class TestCalrissianContext(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.namespace = "e2e-namespace"

    def test_e2e(self):

        username = "pippo"
        password = "pippo"
        email = "john.doe@me.com"
        registry = "1ui32139.gra7.container-registry.ovh.net"

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
                }
            }
        }

        session = CalrissianContext(
            namespace=self.namespace,
            storage_class="microk8s-hostpath",
            volume_size="10G",
            image_pull_secrets=secret_config,
        )

        session.initialise()
