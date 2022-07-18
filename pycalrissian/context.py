import os
from typing import Dict, TextIO

from kubernetes import client, config
from kubernetes.client import Configuration
from kubernetes.client.rest import ApiException


class CalrissianContext(object):
    def __init__(
        self,
        namespace,
        pod_env_vars: Dict = None,
        pod_node_selector: Dict = None,
        max_ram: int = 8,
        max_cores: int = 16,
        security_context: Dict = None,
        storage_class: str = None,
        debug=False,
        no_read_only=False,
        kubeconfig_file: TextIO = None,
    ):

        self.kubeconfig_file = kubeconfig_file

        self.api_client = self._get_api_client(self.kubeconfig_file)

        self.core_v1_api = self._get_core_v1_api()

        self.batch_v1_api = self._get_batch_v1_api()  # BatchV1Api

        self.rbac_authorization_v1_api = self._get_rbac_authorization_v1_api()

        self.namespace = namespace
        self.pod_env_vars = pod_env_vars

    def initialise(self):

        pass

    def discard(self):
        pass

    def get_tmp_dir(self):
        """Returns the tmp directory path"""

    def get_output_dir(self):
        """Returns the output directory path"""

    @staticmethod
    def _get_api_client(kubeconfig_file: TextIO = None):

        proxy_url = os.getenv("HTTP_PROXY", None)
        kubeconfig = os.getenv("KUBECONFIG", None)

        if proxy_url:
            api_config = Configuration(host=proxy_url)
            api_config.proxy = proxy_url
            api_client = client.ApiClient(api_config)

        elif kubeconfig:
            # this is needed because kubernetes-python does not consider
            # the KUBECONFIG env variable
            config.load_kube_config(config_file=kubeconfig)
            api_client = client.ApiClient()
        elif kubeconfig_file:
            config.load_kube_config(config_file=kubeconfig)
            api_client = client.ApiClient()
        else:
            # if nothing is specified, kubernetes-python will use the file
            # in ~/.kube/config
            config.load_kube_config()
            api_client = client.ApiClient()

        return api_client

    def _get_core_v1_api(self) -> client.CoreV1Api:

        return client.CoreV1Api(api_client=self.api_client)

    def _get_batch_v1_api(self) -> client.BatchV1Api:

        return client.BatchV1Api(api_client=self.api_client)

    def _get_rbac_authorization_v1_api(self) -> client.RbacAuthorizationApi:

        return client.RbacAuthorizationV1Api(self.api_client)

    def is_object_created(self, read_method, **kwargs):

        read_methods = {}

        read_methods["read_namespace"] = self.core_v1_api.read_namespace
        # https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/RbacAuthorizationV1Api.md#read_namespaced_role
        read_methods["read_namespaced_role"] = self.rbac_authorization_v1_api.read_namespaced_role
        # https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/RbacAuthorizationV1Api.md#replace_namespaced_role_binding
        read_methods[
            "read_namespaced_role_binding"
        ] = self.rbac_authorization_v1_api.read_namespaced_role_binding

        read_methods["read_namespaced_config_map"] = self.core_v1_api.read_namespaced_config_map

        read_methods[
            "read_namespaced_persistent_volume_claim"
        ] = self.core_v1_api.read_namespaced_persistent_volume_claim

        created = False

        try:

            if read_method in [
                "read_namespaced_config_map",
                "read_namespaced_role",
                "read_namespaced_role_binding",
                "read_namespaced_persistent_volume_claim",
            ]:
                read_methods[read_method](namespace=self.namespace, **kwargs)
                created = True
            else:
                read_methods[read_method](self.namespace)
                created = True
        except ApiException as e:
            if e.status == 404:
                created = False

        return created

    def is_namespace_created(self, **kwargs) -> bool:

        return self.is_object_created("read_namespace", **kwargs)

    def is_role_binding_created(self, **kwargs) -> bool:

        return self.is_object_created("read_namespaced_role_binding", **kwargs)

    def is_role_created(self, **kwargs) -> bool:

        return self.is_object_created("read_namespaced_role", **kwargs)

    def is_config_map_created(self, **kwargs) -> bool:

        return self.is_object_created("read_namespaced_config_map", **kwargs)

    def is_pvc_created(self, **kwargs) -> bool:

        return self.is_object_created("read_namespaced_persistent_volume_claim", **kwargs)

    def create_namespace(self, job_labels: dict = None) -> client.V1Namespace:

        if self.is_namespace_created():

            return self.core_v1_api.read_namespace(name=self.namespace)

        else:

            try:
                body = client.V1Namespace(
                    metadata=client.V1ObjectMeta(name=self.namespace, labels=job_labels)
                )
                response = self.core_v1_api.create_namespace(body=body, async_req=False)
                return response
            except ApiException as e:
                raise e

    def create_role(
        self,
        name: str,
        verbs: list,
        resources: list = ["pods", "pods/log"],
        api_groups: list = ["*"],
    ):

        if self.is_role_created(name=name):

            return self.rbac_authorization_v1_api.read_namespaced_role(
                name=name, namespace=self.namespace
            )

        else:
            metadata = client.V1ObjectMeta(name=name, namespace=self.namespace)

            rule = client.V1PolicyRule(
                api_groups=api_groups,
                resources=resources,
                verbs=verbs,
            )

            body = client.V1Role(metadata=metadata, rules=[rule])

            try:
                response = self.rbac_authorization_v1_api.create_namespaced_role(
                    self.namespace, body, pretty=True
                )
                return response

            except ApiException as e:
                raise e

    def create_role_binding(self, name: str, role: str):

        if self.is_role_binding_created(name=name):

            return self.rbac_authorization_v1_api.read_namespaced_role_binding(
                name=name, namespace=self.namespace
            )

        else:

            metadata = client.V1ObjectMeta(name=name, namespace=self.namespace)

            role_ref = client.V1RoleRef(api_group="", kind="Role", name=role)

            subject = client.models.V1Subject(
                api_group="",
                kind="ServiceAccount",
                name="default",
                namespace=self.namespace,
            )

            body = client.V1RoleBinding(metadata=metadata, role_ref=role_ref, subjects=[subject])

            try:
                response = self.rbac_authorization_v1_api.create_namespaced_role_binding(
                    self.namespace, body, pretty=True
                )
                return response
            except ApiException as e:

                raise e

    def create_pvc(
        self,
        pvc_definition,
    ):

        if self.is_pvc_created(name=pvc_definition.name):

            return self.core_v1_api.read_namespaced_persistent_volume_claim(
                name=pvc_definition.name, namespace=self.namespace
            )

        else:

            metadata = client.V1ObjectMeta(name=pvc_definition.name, namespace=self.namespace)

            spec = client.V1PersistentVolumeClaimSpec(
                access_modes=pvc_definition.access_modes,
                resources=client.V1ResourceRequirements(requests={"storage": pvc_definition.size}),
            )

            spec.storage_class_name = pvc_definition.storage_class

            body = client.V1PersistentVolumeClaim(metadata=metadata, spec=spec)

            try:
                response = self.core_v1_api.create_namespaced_persistent_volume_claim(
                    self.namespace, body, pretty=True
                )
                return response
            except ApiException as e:

                raise e

    def dispose(self) -> client.V1Status:
        try:

            response = self.core_v1_api.delete_namespace(
                name=self.namespace, pretty=True, grace_period_seconds=0
            )
            return response

        except ApiException as e:
            raise e

    def create_configmap(
        self,
        configmap_definition,
    ):

        if self.is_config_map_created(name=configmap_definition.name):

            return self.core_v1_api.read_namespaced_config_map(
                namespace=self.namespace, name=configmap_definition.name
            )

        else:

            metadata = client.V1ObjectMeta(
                annotations=configmap_definition.annotations,
                deletion_grace_period_seconds=30,
                labels=configmap_definition.labels,
                name=configmap_definition.name,
                namespace=self.namespace,
            )

            data = {}
            data[configmap_definition.key] = configmap_definition.content

            config_map = client.V1ConfigMap(
                api_version="v1",
                kind="ConfigMap",
                data=data,
                metadata=metadata,
            )

            try:
                response = self.core_v1_api.create_namespaced_config_map(
                    namespace=self.namespace,
                    body=config_map,
                    pretty=True,
                )
                return response

            except ApiException as e:
                raise e

    def create_roles(self):

        roles = {}

        roles["pod-manager-role"] = {
            "verbs": ["create", "patch", "delete", "list", "watch"],
            "role_binding": "pod-manager-default-binding",
        }

        roles["log-reader-role"] = {
            "verbs": ["get", "list"],
            "role_binding": "log-reader-default-binding",
        }

        for role, value in roles.items():

            self.create_role(
                name=role,
                verbs=value["verbs"],
                resources=["pods", "pods/log"],
                api_groups=["*"],
            )
            self.create_role_binding(name=value["role_binding"], role=role)
