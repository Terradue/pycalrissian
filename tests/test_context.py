import base64
import json
import os
import unittest

import yaml
from kubernetes.client.models.v1_config_map import V1ConfigMap
from kubernetes.client.models.v1_persistent_volume_claim import V1PersistentVolumeClaim
from kubernetes.client.models.v1_role import V1Role
from kubernetes.client.models.v1_role_binding import V1RoleBinding
from kubernetes.client.models.v1_secret import V1Secret
from loguru import logger
from pycalrissian.context import CalrissianContext

os.environ["KUBECONFIG"] = "~/.kube/config"


class TestCalrissianContext(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.namespace = "dummy-namespace2"

    def test_env(self):
        logger.info(
            f"-----\n------------------------------  unit test for test_env from test_context.py   ------------------------------\n\n"
        )
        self.assertIsNotNone(os.getenv("KUBECONFIG", None))

    def test_core_v1_api(self):
        logger.info(
            f"-----\n------------------------------  unit test for test_core_v1_api from test_context.py   ------------------------------\n\n"
        )
        session = CalrissianContext(
            namespace=self.namespace, storage_class="dummy", volume_size="1G",
            calling_workspace=None,
            executing_workspace=None,
            job_id="test_rbac_authorization_v1_api"
        )

        self.assertIsNotNone(session.core_v1_api)

    def test_rbac_authorization_v1_api(self):
        logger.info(
            f"-----\n------------------------------  unit test for test_rbac_authorization_v1_api from test_context.py   ------------------------------\n\n"
        )
        session = CalrissianContext(
            namespace=self.namespace, storage_class="dummy", volume_size="1G",
            calling_workspace=None,
            executing_workspace=None,
            job_id="test_rbac_authorization_v1_api"
        )

        self.assertIsNotNone(session.rbac_authorization_v1_api)

    def test_create_namespace(self):
        logger.info(
            f"-----\n------------------------------  unit test for test_create_namespace from test_context.py   ------------------------------\n\n" 
        )
        session = CalrissianContext(
            namespace=self.namespace, storage_class="dummy", volume_size="1G", calling_workspace=None, executing_workspace=None , job_id="test-job"
        )

        # if session.is_namespace_created():
        #     session.core_v1_api.delete_namespace(
        #         name=self.namespace, pretty=True
        #     )
        response = session.create_namespace()

        self.assertIsNotNone(response)

    def test_create_role_1(self):
        logger.info(
            f"-----\n------------------------------  unit test for test_create_role_1 from test_context.py   ------------------------------\n\n"
        )
        session = CalrissianContext(
            namespace=self.namespace, storage_class="dummy", volume_size="1G", calling_workspace=None, executing_workspace=None , job_id="test_create_role_1"
        )

        if not session.is_namespace_created():
            session.create_namespace()

        roles = {}

        roles["pod-manager-role"] = {
            "verbs": ["create", "patch", "delete", "list", "watch"],
            "role_binding": "pod-manager-default-binding",
        }

        role_name = "pod-manager-role"

        response = session.create_role(
            name=role_name,
            verbs=roles[role_name]["verbs"],
            resources=["pods", "pods/log"],
            api_groups=["*"],
        )

        self.assertIsInstance(response, V1Role)

    def test_create_role_binding_1(self):
        logger.info(
            f"-----\n------------------------------  unit test for test_create_role_binding_1 from test_context.py   ------------------------------\n\n"
        )
        session = CalrissianContext(
            namespace=self.namespace, storage_class="dummy", volume_size="1G", calling_workspace=None, executing_workspace=None , job_id="test_create_role_binding_1"
        )

        if not session.is_namespace_created():
            session.create_namespace()

        roles = {}

        roles["pod-manager-role"] = {
            "verbs": ["create", "patch", "delete", "list", "watch"],
            "role_binding": "pod-manager-default-binding",
        }

        role_name = "pod-manager-role"

        response = session.create_role(
            name=role_name,
            verbs=roles["pod-manager-role"]["verbs"],
            resources=["pods", "pods/log"],
            api_groups=["*"],
        )

        response = session.create_role_binding(
            name=roles[role_name]["role_binding"], role=role_name
        )

        self.assertIsInstance(response, V1RoleBinding)

    def test_create_volume(self):
        logger.info(
            f"-----\n------------------------------  unit test for test_create_volume from test_context.py   ------------------------------\n\n"
        )
        session = CalrissianContext(
            namespace=self.namespace,
            storage_class="standard",
            volume_size="1G",
            calling_workspace=None,
            executing_workspace=None,
            job_id="test_create_volume"
        )

        if not session.is_namespace_created():
            session.create_namespace()

        response = session.create_pvc(
            name="calrissian-wdir",
            size=session.volume_size,
            storage_class=session.storage_class,
            access_modes=["ReadWriteMany"],
        )

        self.assertIsInstance(response, V1PersistentVolumeClaim)

    def test_configmap_from_dict_as_yaml(self):
        logger.info(
            f"-----\n------------------------------  unit test for test_configmap_from_dict_as_yaml from test_context.py   ------------------------------\n\n"
        )
        session = CalrissianContext(
            namespace=self.namespace,
            storage_class="standard",
            volume_size="1G",
            calling_workspace=None,
            executing_workspace=None,
            job_id="test_configmap_from_dict_as_yaml"
        )

        if not session.is_namespace_created():
            session.create_namespace()

        data = {}

        data["cwlVersion"] = "v1.0"
        data["$graph"] = [
            {"class": "Workflow", "id": "my_id"},
            {"class": "CommandLineTool", "id": "my_id"},
        ]
        data["key3"] = "value3"

        response = session.create_configmap(
            name="cm-id-yml-cwl",
            key="from_dict_as_yaml",
            content=yaml.dump(data),
        )

        self.assertIsInstance(response, V1ConfigMap)

    def test_configmap_from_dict_as_json(self):
        logger.info(
            f"-----\n------------------------------  unit test for test_configmap_from_dict_as_json from test_context.py   ------------------------------\n\n"
        )
        session = CalrissianContext(
            namespace=self.namespace,
            storage_class="standard",
            volume_size="1G",
            calling_workspace=None,
            executing_workspace=None,
            job_id="test_configmap_from_dict_as_json"
        )

        if not session.is_namespace_created():
            session.create_namespace()

        data = {}

        data["key1"] = "value1"
        data["key2"] = "value2"
        data["key3"] = "value3"

        response = session.create_configmap(
            name="cm-id-json",
            key="from_dict",
            content=json.dumps(data, indent=4),
        )

        self.assertIsInstance(response, V1ConfigMap)

    def test_secret_creation(self):
        logger.info(
            f"-----\n------------------------------  unit test for test_secret_creation from test_context.py   ------------------------------\n\n"
        )
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
            storage_class="standard",
            volume_size="1G",
            image_pull_secrets={"imagePullSecrets": secret_config},
            calling_workspace=None,
            executing_workspace=None,
            job_id="test_secret_creation"
        )

        if not session.is_namespace_created():
            session.create_namespace()

        response = session.create_image_pull_secret(name="container-rg")

        self.assertIsInstance(response, V1Secret)


# # if __name__ == "__main__":
# #     import nose2

# #     nose2.main()
