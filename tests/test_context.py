import os
import unittest

from kubernetes.client.models.v1_persistent_volume_claim import V1PersistentVolumeClaim
from kubernetes.client.models.v1_role import V1Role
from kubernetes.client.models.v1_role_binding import V1RoleBinding
from pycalrissian.context import CalrissianContext

os.environ["KUBECONFIG"] = "/home/mambauser/.kube/microk8s.config"


class TestCalrissianContext(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.namespace = "dummy-namespace"

    def test_env(self):

        self.assertIsNotNone(os.getenv("KUBECONFIG", None))

    def test_core_v1_api(self):

        session = CalrissianContext(namespace=self.namespace)

        self.assertIsNotNone(session.core_v1_api)

    def test_rbac_authorization_v1_api(self):

        session = CalrissianContext(namespace=self.namespace)

        self.assertIsNotNone(session.rbac_authorization_v1_api)

    def test_create_namespace(self):

        session = CalrissianContext(namespace=self.namespace)

        # if session.is_namespace_created():
        #     session.core_v1_api.delete_namespace(
        #         name=self.namespace, pretty=True
        #     )
        response = session.create_namespace()

        self.assertIsNotNone(response)

    def test_create_role_1(self):

        session = CalrissianContext(namespace=self.namespace)

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

        session = CalrissianContext(namespace=self.namespace)

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

        response = session.create_role_binding(name=roles[role_name]["role_binding"], role=role_name)

        self.assertIsInstance(response, V1RoleBinding)

    def test_create_roles(self):

        session = CalrissianContext(namespace=self.namespace)

        if not session.is_namespace_created():
            session.create_namespace()

        session.create_roles()

    def test_create_volume(self):

        session = CalrissianContext(namespace=self.namespace)

        if not session.is_namespace_created():
            session.create_namespace()

        response = session.create_pvc(
            name="calrissian-wdir",
            size="10G",
            storage_class="microk8s-hostpath",
            access_modes=["ReadWriteMany"],
        )

        self.assertIsInstance(response, V1PersistentVolumeClaim)


#     def test_configmap_from_dict_as_yaml(self):

#         ns_configmap = "ns-config-map-1"

#         session = CalrissianContext(namespace=ns_configmap)

#         if not session.is_namespace_created():
#             session.create_namespace()

#         data = {}

#         data["cwlVersion"] = "v1.0"
#         data["$graph"] = [
#             {"class": "Workflow", "id": "my_id"},
#             {"class": "CommandLineTool", "id": "my_id"},
#         ]
#         data["key3"] = "value3"

#         cm_definition = ConfigMapDescription(
#             name="cm-id-yml-cwl", key="from_dict_as_yaml", content=yaml.dump(data)
#         )

#         response = session.create_configmap(cm_definition)

#         self.assertTrue(isinstance(response, V1ConfigMap))

#     def test_configmap_from_dict_as_json(self):

#         ns_configmap = "ns-config-map-1"

#         session = KubernetesSession(namespace=ns_configmap)

#         if not session.is_namespace_created():
#             session.create_namespace()

#         data = {}

#         data["key1"] = "value1"
#         data["key2"] = "value2"
#         data["key3"] = "value3"

#         cm_definition = ConfigMapDescription(
#             name="cm-id-json", key="from_dict", content=json.dumps(data, indent=4)
#         )

#         response = session.create_configmap(cm_definition)

#         self.assertTrue(isinstance(response, V1ConfigMap))


# # if __name__ == "__main__":
# #     import nose2

# #     nose2.main()
