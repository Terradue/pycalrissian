import base64
import os
import ast
import unittest
from unittest import mock
from loguru import logger
from kubernetes.client.models.v1_job import V1Job
from ruamel import yaml
import time
from pycalrissian.context import CalrissianContext
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

class TestCalrissianJob(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logger.info(
            f"-----\n------------------------------  unit test for test_job.py   ------------------------------\n\n"
        )
        cls.namespace = "job-namespace"

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
            namespace=cls.namespace,
            storage_class="standard",  # "microk8s-hostpath",
            volume_size="10G",
            image_pull_secrets=secret_config,
        )

        session.initialise()

        cls.session = session

    

    @unittest.skipIf(os.getenv("CI_TEST_SKIP") == "1", "Test is skipped via env variable")
    def test_job_instance(self):
        logger.info(
            f"-----\n------------------------------  test_job_instance   ------------------------------\n\n"
        )
        document = "tests/simple.cwl"
        with open(document) as doc_handle:
            yaml_obj = yaml.YAML()
            cwl = yaml_obj.load(doc_handle)

        params = {"message": "hello world!"}

        pod_env_vars = {"C": "1", "B": "2"}

        job = CalrissianJob(
            cwl=cwl,
            params=params,
            runtime_context=self.session,
            pod_env_vars=pod_env_vars,
            # pod_node_selector={
            #     "k8s.scaleway.com/pool-name": "processing-node-pool-dev"
            # },
            debug=True,
            max_cores=2,
            max_ram="4G",
            keep_pods=True,
        )

        job.to_yaml("job.yml")
        self.assertIsInstance(job.to_k8s_job(), V1Job)
    @unittest.skipIf(os.getenv("CI_TEST_SKIP") == "1", "Test is skipped via env variable")
    def test_image_refrence(self):
        logger.info(
            f"-----\n------------------------------  test_image_refrence   ------------------------------\n\n"
        )
        os.environ["IMAGE"] = "terradue/calrissian:0.12.0"

        document = "tests/simple.cwl"

        with open(document) as doc_handle:
            yaml_obj = yaml.YAML()
            cwl = yaml_obj.load(doc_handle)

        params = {"message": "hello world!"}

        job = CalrissianJob(
            cwl=cwl,
            params=params,
            runtime_context=self.session,
            pod_env_vars={},
            pod_node_selector={},
            debug=True,
            max_cores=2,
            max_ram="4G",
            keep_pods=True,
        )

        self.assertEqual(
            job.to_k8s_job().spec.template.spec.containers[0].image,
            os.environ["IMAGE"],
        )

    
    @mock.patch("pycalrissian.context.CalrissianContext.from_existing_namespace")
    def test_job_with_specific_service_account(
        self,
        mock_from_existing_namespace
    ):

        mock_context = mock.Mock()
        mock_context.namespace=self.namespace
        mock_context.storage_class = "dummy-storage-class"
        mock_context.service_account = "dummy-service-account"
        mock_context.volume_size = "1G"
        mock_from_existing_namespace.return_value = mock_context

        os.environ["IMAGE"] = "terradue/calrissian:0.12.0"

        document = "tests/simple.cwl"

        with open(document) as doc_handle:
            yaml_obj = yaml.YAML()
            cwl = yaml_obj.load(doc_handle)

        params = {"message": "hello world!"}

        job = CalrissianJob(
            cwl=cwl,
            params=params,
            runtime_context=mock_context,
            pod_env_vars={},
            pod_node_selector={},
            debug=True,
            max_cores=2,
            max_ram="4G",
            keep_pods=True,
        )
        
        self.assertEqual(job.to_k8s_job().metadata.namespace, self.namespace)

        job_service_account = job.to_k8s_job().spec.template.spec.service_account_name

        self.assertEqual(job_service_account, mock_context.service_account)
