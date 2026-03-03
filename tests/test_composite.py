import base64
import os
import unittest
import yaml
import time
from loguru import logger
from kubernetes.client.exceptions import ApiException
from pycalrissian.context import CalrissianContext
from pycalrissian.execution import CalrissianExecution
from pycalrissian.job import CalrissianJob

# Ensure correct kubeconfig
os.environ["KUBECONFIG"] = "~/.kube/kubeconfig-t2-dev.yaml"


def wait_for_pvc_bound(api, name, namespace, timeout=300):
    """Wait until PVC exists and is Bound."""
    for t in range(timeout):
        try:
            pvc = api.read_namespaced_persistent_volume_claim(name=name, namespace=namespace)
            if pvc.status.phase == "Bound":
                logger.success(f"PVC {name} is Bound")
                return True
            if t % 10 == 0:
                logger.info(f"PVC {name} phase: {pvc.status.phase}")
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
        cls.namespace = "job-namespace-unit-test6"
        cls.job_id = "test-composite-job1"

        # -------------------------------
        # Hard-coded image pull secret
        # -------------------------------
        DOCKER_USERNAME = ""
        DOCKER_PASSWORD = ""
        DOCKER_REGISTRY = "https://index.docker.io/v1/"

        auth = base64.b64encode(f"{DOCKER_USERNAME}:{DOCKER_PASSWORD}".encode()).decode()
        image_pull_secret = {
            "auths": {
                DOCKER_REGISTRY: {
                    "username": DOCKER_USERNAME,
                    "password": DOCKER_PASSWORD,
                    "auth": auth,
                }
            }
        }

        # -------------------------------
        # Calrissian runtime context
        # -------------------------------
        cls.session = CalrissianContext(
            namespace=cls.namespace,
            storage_class="standard",
            volume_size="10G",
            image_pull_secrets={"imagePullSecrets": image_pull_secret},
            kubeconfig_file=os.environ.get("KUBECONFIG"),
            calling_workspace="",
            executing_workspace="",
            job_id=cls.job_id,
        )
        cls.session.initialise()

        # -------------------------------
        # Workspace config (required)
        # -------------------------------
        cls.session.create_configmap(
            name="workspace-config",
            key="pvcs",
            content="[]",
        )
        logger.info("workspace-config ConfigMap created")

    @classmethod
    def tearDownClass(cls):
        cls.session.dispose()

    #@unittest.skipIf(os.getenv("CI_TEST_SKIP") == "1", "Test is skipped via env variable")
    def test_s2_composite_job(self):
        logger.info("----- Running unit test: test_s2_composite_job -----\n")

        # Public image (pull secret is included for future private images)
        os.environ["CALRISSIAN_IMAGE"] = "public.ecr.aws/eodh/eodhp-calrissian:0.1.9"

        # Load CWL workflow
        with open("tests/app-s2-composites.0.1.0.cwl", "r") as stream:
            cwl = yaml.safe_load(stream)

        # Job parameters
        params = {
            "post_stac_item": "https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2B_53HPA_20210723_0_L2A",
            "pre_stac_item": "https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2B_53HPA_20210703_0_L2A",
            "aoi": "136.659,-35.96,136.923,-35.791",
        }

        pod_env_vars = {"A": "1", "B": "2"}

        # Create job
        job = CalrissianJob(
            cwl=cwl,
            params=params,
            runtime_context=self.session,
            cwl_entry_point="dnbr",
            pod_env_vars=pod_env_vars,
            debug=False,
            max_cores=6,
            max_ram="16G",
            keep_pods=False,
            backoff_limit=1,
            tool_logs=True,
            calling_workspace="",
            executing_workspace="",
            job_id=self.job_id,
        )

        execution = CalrissianExecution(job=job, runtime_context=self.session)
        execution.submit()

        # Wait for PVC
        wait_for_pvc_bound(
            api=self.session.core_v1_api,
            name=self.session.calrissian_wdir,
            namespace=self.session.namespace,
        )

        # Monitor job
        execution.monitor(interval=5, grace_period=600, wall_time=360)

        # Print outputs
        print(execution.get_log())
        print(execution.get_usage_report())
        print(execution.get_output())

        # Assert success
        self.assertTrue(execution.is_succeeded())
        logger.success("Calrissian execution succeeded")
