import base64
import os
import unittest
from time import sleep
import yaml
from loguru import logger
from pycalrissian.context import CalrissianContext
from pycalrissian.execution import CalrissianExecution
from pycalrissian.job import CalrissianJob

os.environ["KUBECONFIG"] = "~/.kube/config"


class TestCalrissianExecutionLogs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.namespace = "job-namespace-unit-test-log"
        cls.job_id = "test-logs-job"
        username = "fabricebrito"
        password = ""
        email = "fabrice.brito@terradue.com"
        registry = "https://index.docker.io/v1/"

        auth = base64.b64encode(f"{username}:{password}".encode()).decode()

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
            storage_class="standard",
            volume_size="10G",
            image_pull_secrets={"imagePullSecrets": secret_config},
            calling_workspace=None,
            executing_workspace=None,
            job_id=cls.job_id,
            
        )

        session.initialise()
        session.create_configmap(
            name="workspace-config",
            key="pvcs",
            content="[]",
        )
        logger.info("workspace-config ConfigMap created")
        cls.session = session

    @classmethod
    def tearDown(cls):
        cls.session.dispose()
        
    @unittest.skipIf(os.getenv("CI_TEST_SKIP") == "1", "Test is skipped via env variable")
    def test_job_tool_logs(self):
        logger.info(
            f"-----\n------------------------------  unit test for test_job_tool_logs from test_logs.py   ------------------------------\n\n"
        )
        sleep(30)
        os.environ["CALRISSIAN_IMAGE"] = "public.ecr.aws/eodh/eodhp-calrissian:0.1.9"

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
            debug=False,
            max_cores=4,
            max_ram="4G",
            keep_pods=False,
            backoff_limit=1,
            tool_logs=True,
            calling_workspace=None,
            executing_workspace=None,
            job_id=self.job_id,
        )

        execution = CalrissianExecution(job=job, runtime_context=self.session)

        execution.submit()

        execution.monitor(interval=5, grace_period=60, wall_time=20)

        print(execution.get_log())

        print(execution.get_usage_report())

        print(execution.get_output())

        execution.get_tool_logs()

        self.assertTrue(execution.is_succeeded())
