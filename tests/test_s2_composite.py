import base64
import os
import unittest

import yaml

from pycalrissian.context import CalrissianContext
from pycalrissian.execution import CalrissianExecution
from pycalrissian.job import CalrissianJob

os.environ["KUBECONFIG"] = "~/.kube/kubeconfig-t2-dev.yaml"


class TestCalrissianExecution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.namespace = "job-namespace-unit-test"

        username = ""
        password = ""
        email = ""
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
                "registry.gitlab.com": {"auth": "="},  # noqa: E501
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
        
    @unittest.skipIf(os.getenv("CI_TEST_SKIP") == "1", "Test is skipped via env variable")
    def test_s2_composite_job(self):

        os.environ["CALRISSIAN_IMAGE"] = "terradue/calrissian:0.11.0-logs"

        with open("tests/app-s2-composites.0.1.0.cwl", "r") as stream:
            cwl = yaml.safe_load(stream)

        params = {
            "post_stac_item": "https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2B_53HPA_20210723_0_L2A",  # noqa: E501
            "pre_stac_item": "https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2B_53HPA_20210703_0_L2A",  # noqa: E501
            "aoi": "136.659,-35.96,136.923,-35.791",
        }

        pod_env_vars = {"A": "1", "B": "2"}

        job = CalrissianJob(
            cwl=cwl,
            params=params,
            runtime_context=self.session,
            cwl_entry_point="dnbr",
            pod_env_vars=pod_env_vars,
            # pod_node_selector={
            #     "k8s.scaleway.com/pool-name": "processing-node-pool-dev"
            # },
            debug=False,
            max_cores=6,
            max_ram="16G",
            keep_pods=False,
            backoff_limit=1,
            tool_logs=True,
        )

        execution = CalrissianExecution(job=job, runtime_context=self.session)

        execution.submit()

        execution.monitor(interval=5, grace_period=600, wall_time=360)

        print(execution.get_log())

        print(execution.get_usage_report())

        print(execution.get_output())

        self.assertTrue(execution.is_succeeded())
