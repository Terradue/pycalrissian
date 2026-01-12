import base64
import os
import time
import unittest
import yaml

from loguru import logger
from kubernetes.client.exceptions import ApiException

from pycalrissian.context import CalrissianContext
from pycalrissian.execution import CalrissianExecution
from pycalrissian.job import CalrissianJob


# Ensure kubeconfig is available
os.environ["KUBECONFIG"] = "~/.kube/kubeconfig-t2-dev.yaml"


def wait_for_pvc_bound(api, name, namespace, timeout=300):
    """
    Wait until a PVC exists and reaches Bound phase.
    Handles initial 404 until PVC is created.
    """
    for t in range(timeout):
        try:
            pvc = api.read_namespaced_persistent_volume_claim(
                name=name, namespace=namespace
            )
            phase = pvc.status.phase
            if phase == "Bound":
                logger.success(f"PVC {name} is Bound")
                return True
            if t % 10 == 0:
                logger.info(f"PVC {name} phase: {phase}")
        except ApiException as e:
            if e.status != 404:
                raise
            if t % 10 == 0:
                logger.info(f"PVC {name} not created yet")
        time.sleep(1)

    raise TimeoutError(f"PVC {name} did not reach Bound state in time")


class TestCalrissianExecution(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logger.info(
            "\n"
            "------------------------------------------------------------\n"
            "   Unit test: test_catalog_describe (Calrissian execution)   \n"
            "------------------------------------------------------------\n"
        )

        cls.namespace = "job-namespace-unit-test"
        cls.job_id = "test-catalog-describe"

        # ------------------------------------------------------------------
        # HARD-CODED, VALID imagePullSecret (no env vars)
        # ------------------------------------------------------------------
        DOCKER_USERNAME = ""
        DOCKER_PASSWORD = ""
        DOCKER_REGISTRY = "https://index.docker.io/v1/"

        auth = base64.b64encode(
            f"{DOCKER_USERNAME}:{DOCKER_PASSWORD}".encode("utf-8")
        ).decode("utf-8")

        image_pull_secret = {
            "auths": {
                DOCKER_REGISTRY: {
                    "username": DOCKER_USERNAME,
                    "password": DOCKER_PASSWORD,
                    "auth": auth,
                }
            }
        }

        # ------------------------------------------------------------------
        # Create Calrissian runtime context
        # ------------------------------------------------------------------
        cls.session = CalrissianContext(
            namespace=cls.namespace,
            storage_class="standard",
            volume_size="10G",
            image_pull_secrets={
                "imagePullSecrets": image_pull_secret
            },
            kubeconfig_file=os.environ.get("KUBECONFIG"),
            calling_workspace=None,
            executing_workspace=None,
            job_id=cls.job_id,
        )

        cls.session.initialise()

        # ------------------------------------------------------------------
        # REQUIRED: workspace-config ConfigMap
        # ------------------------------------------------------------------
        cls.session.create_configmap(
            name="workspace-config",
            key="pvcs",
            content="[]",
        )

        logger.info("workspace-config ConfigMap created")

    @classmethod
    def tearDownClass(cls):
        cls.session.dispose()

    def test_describe_catalog(self):
        os.environ["CALRISSIAN_IMAGE"] = "terradue/calrissian:0.11.0-logs"

        with open("tests/describe-catalog.cwl", "r", encoding="utf-8") as f:
            cwl = yaml.safe_load(f)

        params = {
            "reference": "https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2B_10TFK_20210713_0_L2A"
        }

        job = CalrissianJob(
            cwl=cwl,
            params=params,
            runtime_context=self.session,
            cwl_entry_point="main",
            debug=True,
            max_cores=2,
            max_ram="16G",
            keep_pods=True,
            backoff_limit=1,
            tool_logs=True,
            calling_workspace=None,
            executing_workspace=None,
            job_id=self.job_id,
        )

        execution = CalrissianExecution(
            job=job,
            runtime_context=self.session,
        )

        execution.submit()

        # ------------------------------------------------------------------
        # Wait for the correct PVC
        # ------------------------------------------------------------------
        wait_for_pvc_bound(
            api=self.session.core_v1_api,
            name=self.session.calrissian_wdir,
            namespace=self.session.namespace,
        )

        execution.monitor(
            interval=5,
            grace_period=600,
            wall_time=360,
        )

        logger.info("Execution logs:")
        print(execution.get_log())

        logger.info("Usage report:")
        print(execution.get_usage_report())

        logger.info("Execution output:")
        print(execution.get_output())

        self.assertTrue(execution.is_succeeded())
        logger.success("Calrissian execution succeeded")
