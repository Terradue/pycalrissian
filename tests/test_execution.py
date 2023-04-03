import base64
import os
import unittest

import yaml

from pycalrissian.context import CalrissianContext
from pycalrissian.execution import CalrissianExecution
from pycalrissian.job import CalrissianJob

os.environ["KUBECONFIG"] = "/home/mambauser/.kube/kubeconfig-t2-dev.yaml"


class TestCalrissianExecution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.namespace = "job-namespace"

        username = "fabricebrito"
        password = "dckr_pat_cVqA0dOTLkQi6XxDklSPpH91Qic"
        registry = "https://index.docker.io/v1/"

        auth = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode(
            "utf-8"
        )

        secret_config = {
            "auths": {
                registry: {
                    "username": username,
                    "password": password,
                    "auth": auth,
                }
            }
        }

        session = CalrissianContext(
            namespace=cls.namespace,
            storage_class="longhorn",  # "microk8s-hostpath",
            volume_size="10G",
            image_pull_secrets=secret_config,
        )

        session.initialise()

        cls.session = session

    @classmethod
    def tearDown(cls):
        cls.session.dispose()

    def test_simple_job(self):
        with open("tests/simple.cwl", "r") as stream:
            cwl = yaml.safe_load(stream)

        params = {"message": "hello world!"}

        pod_env_vars = {"A": "1", "B": "2"}

        job = CalrissianJob(
            cwl=cwl,
            params=params,
            runtime_context=self.session,
            pod_env_vars=pod_env_vars,
            debug=True,
            max_cores=2,
            max_ram="4G",
            keep_pods=True,
            backoff_limit=1,
        )

        execution = CalrissianExecution(job=job, runtime_context=self.session)

        execution.submit()

        execution.monitor(interval=5)

        print(f"complete {execution.is_complete()}")
        print(f"succeeded {execution.is_succeeded()}")
        print(execution.get_start_time())
        print(execution.get_completion_time())

        self.assertTrue(execution.is_succeeded())

    def test_wrong_docker_pull_job(self):
        """tests the imagepullbackoff state of a pod, the job is killed"""
        with open("tests/wrong_docker_pull.cwl", "r") as stream:
            cwl = yaml.safe_load(stream)

        params = {"message": "hello world!"}

        pod_env_vars = {"A": "1", "B": "2"}

        job = CalrissianJob(
            cwl=cwl,
            params=params,
            runtime_context=self.session,
            pod_env_vars=pod_env_vars,
            debug=True,
            max_cores=2,
            max_ram="4G",
            keep_pods=True,
            backoff_limit=1,
        )

        execution = CalrissianExecution(job=job, runtime_context=self.session)

        execution.submit()

        execution.monitor(interval=5, grace_period=60)

        print(f"killed {execution.killed}")
        self.assertFalse(execution.is_succeeded())

    def test_high_reqs_job(self):
        """tests the high reqs for RAM and cores, the job is killed"""
        with open("tests/high_reqs.cwl", "r") as stream:
            cwl = yaml.safe_load(stream)

        params = {"message": "hello world!"}

        pod_env_vars = {"A": "1", "B": "2"}

        job = CalrissianJob(
            cwl=cwl,
            params=params,
            runtime_context=self.session,
            pod_env_vars=pod_env_vars,
            debug=True,
            max_cores=2,
            max_ram="4G",
            keep_pods=True,
            backoff_limit=1,
        )

        execution = CalrissianExecution(job=job, runtime_context=self.session)

        execution.submit()

        execution.monitor(interval=5, grace_period=60)

        print(f"killed {execution.killed}")
        self.assertFalse(execution.is_succeeded())

    def test_wall_time_reached_job(self):
        """tests wall time reached, the job is killed"""
        with open("tests/sleep.cwl", "r") as stream:
            cwl = yaml.safe_load(stream)

        params = {"message": "hello world!"}

        job = CalrissianJob(
            cwl=cwl,
            params=params,
            runtime_context=self.session,
            debug=True,
            max_cores=2,
            max_ram="4G",
            keep_pods=True,
            backoff_limit=1,
        )

        execution = CalrissianExecution(job=job, runtime_context=self.session)

        execution.submit()

        execution.monitor(interval=15, grace_period=30, wall_time=45)

        print(f"killed {execution.killed}")
        self.assertFalse(execution.is_succeeded())

    def test_wall_time_not_reached_job(self):
        """tests wall time reached, the job is killed"""
        with open("tests/sleep.cwl", "r") as stream:
            cwl = yaml.safe_load(stream)

        params = {"message": "hello world!"}

        job = CalrissianJob(
            cwl=cwl,
            params=params,
            runtime_context=self.session,
            debug=True,
            max_cores=2,
            max_ram="4G",
            keep_pods=True,
            backoff_limit=1,
        )

        execution = CalrissianExecution(job=job, runtime_context=self.session)

        execution.submit()

        execution.monitor(interval=15, grace_period=30, wall_time=180)

        self.assertTrue(execution.is_succeeded())
