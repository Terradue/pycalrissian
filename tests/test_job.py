import base64
import os
import unittest
from time import sleep
from kubernetes.client.models.v1_job import V1Job
from ruamel import yaml
from loguru import logger
from pycalrissian.context import CalrissianContext
from pycalrissian.job import CalrissianJob

os.environ["KUBECONFIG"] = "~/.kube/config"


class TestCalrissianJob(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.namespace = "job-namespace4"

        username = "pippo"
        password = "pippo"
        email = "john.doe@me.com"
        registry = "1ui32139.gra7.container-registry.ovh.net"

        auth = base64.b64encode(f"{username}:{password}".encode()).decode()

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
            image_pull_secrets={"imagePullSecrets": secret_config},
            calling_workspace=None,
            executing_workspace=None,
            job_id="test-calrissian-job",
        )

        session.initialise()

        cls.session = session

    @classmethod
    def tearDown(cls):
        cls.session.dispose()

    @unittest.skipIf(os.getenv("CI_TEST_SKIP") == "1", "Test is skipped via env variable")
    def test_job(self):
        # TODO check why this fails with namespace is being terminated
        logger.info(
            f"-----\n------------------------------  unit test for test_job from test_execution.py   ------------------------------\n\n"
        )
        sleep(60)
        self.session.initialise()
        self.session.create_configmap(
            name="workspace-config",
            key="pvcs",
            content="[]",
        )
        logger.info("workspace-config ConfigMap created")
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
            calling_workspace=None,
            executing_workspace=None,
            job_id="test-calrissian-job",
        )

        job.to_yaml("job.yml")
        self.assertIsInstance(job.to_k8s_job(), V1Job)
    @unittest.skipIf(os.getenv("CI_TEST_SKIP") == "1", "Test is skipped via env variable")
    def test_calrissian_image(self):
        logger.info(
            f"-----\n------------------------------  unit test for test_calrissian_image from test_job.py   ------------------------------\n\n"
        )
        sleep(60)
        self.session.initialise()
        self.session.create_configmap(
            name="workspace-config",
            key="pvcs",
            content="[]",
        )
        logger.info("workspace-config ConfigMap created")
        os.environ["CALRISSIAN_IMAGE"] = "public.ecr.aws/eodh/eodhp-calrissian:0.1.9"

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
            calling_workspace=None,
            executing_workspace=None,
            job_id="test-calrissian-job",
        )

        self.assertEqual(
            job.to_k8s_job().spec.template.spec.containers[0].image,
            os.environ["CALRISSIAN_IMAGE"],
        )