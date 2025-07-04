import base64
import os
import unittest
from loguru import logger
import time
import yaml

from pycalrissian.context import CalrissianContext
from pycalrissian.execution import CalrissianExecution
from pycalrissian.job import CalrissianJob

os.environ["KUBECONFIG"] = "~/.kube/kubeconfig-t2-dev.yaml"


def wait_for_pvc_bound(api, name, namespace, timeout=500):
    for t in range(timeout):
        pvc = api.read_namespaced_persistent_volume_claim(name=name, namespace=namespace)
        phase = pvc.status.phase
        if t % 10 == 0 and phase!="Bound": 
            logger.warning(f"PVC phase: {phase}")
        if phase == "Bound":
            logger.success(f"PVC phase: {phase}")
            return True
        time.sleep(1)
    raise TimeoutError("PVC did not reach 'Bound' state in time")

class TestCalrissianExecution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logger.info(
            f"-----\n------------------------------  unit test for GPU   ------------------------------\n\n"
        )
        cls.namespace = "job-namespace-3"

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
                    }
            }
        }

        session = CalrissianContext(
            namespace=cls.namespace,
            storage_class="standard",
            volume_size="10G",
            #kubeconfig_file= os.environ.get("KUBECONFIG", "~/.kube/kubeconfig-t2-dev.yaml"),
            image_pull_secrets=secret_config,
        )

        session.initialise()

        cls.session = session

    @classmethod
    def tearDown(cls):
        cls.session.dispose()
        
    @unittest.skipIf(os.getenv("CI_TEST_SKIP") == "1", "Test is skipped via env variable")
    def test_describe_catalog_with_gpu(self):
        logger.info(f"-----\n------------------------------  test_describe_catalog_with_gpu must succeed  ------------------------------\n\n")
        os.environ["CALRISSIAN_IMAGE"] = "ghcr.io/duke-gcb/calrissian/calrissian:0.18.1"

        with open("tests/gpu-test-cuda.cwl", "r") as stream:
            cwl = yaml.safe_load(stream)

        params = {
            "reference": "https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2B_10TFK_20210713_0_L2A"
        }

        gpu_class= {'accelerator': 'nvidia'}
        job = CalrissianJob(
            cwl=cwl,
            params=params,
            runtime_context=self.session,
            cwl_entry_point="main",
            #pod_env_vars=pod_env_vars,
            pod_node_selector={
                "kubernetes.io/hostname": "minikube",
            },  
            debug=True,
            max_cores=2,
            max_ram="8G",
            keep_pods=True,
            backoff_limit=1,
            tool_logs=True,
            max_gpus='1',
            gpu_class=gpu_class
        )
        job.to_yaml("job.yml")
        execution = CalrissianExecution(job=job, runtime_context=self.session)
    
        execution.submit()
        wait_for_pvc_bound(self.session.core_v1_api, "calrissian-wdir", self.session.namespace)
        execution.monitor(interval=15, grace_period=1600, wall_time=1360)
        
        print(execution.get_log())

        print(execution.get_usage_report())

        print(execution.get_output())
        print(execution.get_start_time())
        if execution.is_succeeded() == True:
            logger.success(f"Execution was succeed")
        # print(f"succeeded {execution.is_succeeded()}")
        self.assertTrue(execution.is_succeeded())
