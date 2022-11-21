import base64
import os
import unittest

import yaml

from pycalrissian.context import CalrissianContext
from pycalrissian.execution import CalrissianExecution
from pycalrissian.job import CalrissianJob

os.environ["KUBECONFIG"] = "/home/mambauser/.kube/kubeconfig-t2-dev.yaml"


class TestCalrissianExecutionLogs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.namespace = "job-namespace-unit-test"

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
                "registry.gitlab.com": {"auth": ""},  # noqa: E501
            }
        }

        session = CalrissianContext(
            namespace=cls.namespace,
            storage_class="openebs-kernel-nfs-scw",
            volume_size="10G",
            image_pull_secrets=secret_config,
        )

        session.initialise()

        cls.session = session

    @classmethod
    def tearDown(cls):
        cls.session.dispose()

    def test_job_tool_logs(self):

        os.environ["CALRISSIAN_IMAGE"] = "terradue/calrissian:0.11.0-logs"

        with open("tests/logs.cwl", "r") as stream:
            cwl = yaml.safe_load(stream)

        params = {"message": ["one", "two", "three"]}

        pod_env_vars = {"A": "1", "B": "2"}

        job = CalrissianJob(
            cwl=cwl,
            params=params,
            runtime_context=self.session,
            cwl_entry_point="main",
            pod_env_vars=pod_env_vars,
            pod_node_selector={
                "k8s.scaleway.com/pool-name": "processing-node-pool-dev"
            },
            debug=False,
            max_cores=4,
            max_ram="4G",
            keep_pods=False,
            backoff_limit=1,
            tool_logs=True,
        )

        execution = CalrissianExecution(job=job, runtime_context=self.session)

        execution.submit()

        execution.monitor(interval=5, grace_period=600)

        print(execution.get_log())

        print(execution.get_usage_report())

        print(execution.get_output())

        execution.get_tool_logs()

        self.assertTrue(execution.is_succeeded())
