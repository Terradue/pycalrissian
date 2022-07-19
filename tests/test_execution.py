import base64
import os
import time
import unittest

import yaml

from pycalrissian.context import CalrissianContext
from pycalrissian.execution import JobExecution
from pycalrissian.job import CalrissianJob

os.environ["KUBECONFIG"] = "/home/mambauser/.kube/kubeconfig-t2-dev.yaml"


class TestCalrissianExecution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.namespace = "job-namespace"

    def test_job(self):

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
            storage_class="longhorn",  # "microk8s-hostpath",
            volume_size="10G",
            image_pull_secrets=secret_config,
        )

        session.initialise()

        with open("tests/simple.cwl", "r") as stream:

            cwl = yaml.safe_load(stream)

        params = {"message": "hello world!"}

        pod_env_vars = {"A": "1", "B": "2"}

        job = CalrissianJob(
            cwl=cwl,
            params=params,
            runtime_context=session,
            pod_env_vars=pod_env_vars,
            debug=True,
            max_cores=2,
            max_ram="4G",
        )

        execution = JobExecution(job=job, runtime_context=session)

        execution.submit()

        print(f"active: {execution.is_active()}")
        while execution.is_active():
            print("active")
            time.sleep(5)

        print(f"complete {execution.is_complete()}")
        print(f"succeeded {execution.is_succeeded()}")

        execution.get_log()
