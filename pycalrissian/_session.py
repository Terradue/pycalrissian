import base64
import json
import logging
from time import sleep

from kubernetes import client, config
from kubernetes.client.rest import ApiException
from kubernetes.config.config_exception import ConfigException

logging.basicConfig(level=logging.INFO)


class CalrissianSession:
    def __init__(self, namespace, storage_class):

        self.namespace = namespace
        self.storage_class = storage_class

        self.pvcs = [
            "calrissian-tmp",
            "calrissian-input",
            "calrissian-output",
        ]

        try:
            config.load_incluster_config()  # raises if not in cluster
        except ConfigException:
            config.load_kube_config()  # for local debug/test purposes

        self.api_client = client.ApiClient()

    def create(self):

        self._create_namespace()

    def dispose(self):

        pass

    def _delete_quota(self, quota_name):

        try:
            response = self.client.CoreV1Api().delete_namespaced_resource_quota(
                namespace=self.namespace, name=quota_name
            )
            print(response)
        except ApiException as e:
            if e.status == 404:
                pass
            else:
                raise e

    def _set_quota(self, resources):

        quota_name = "user-quota"

        self.delete_quota(quota_name)

        resource_quota = client.V1ResourceQuota(spec=client.V1ResourceQuotaSpec(hard=resources))
        resource_quota.metadata = client.V1ObjectMeta(namespace=self.namespace, name=quota_name)

        try:
            response = self.client.CoreV1Api().create_namespaced_resource_quota(
                self.namespace, resource_quota
            )
            return response
        except ApiException as e:
            if e.status == 409:
                pass
            else:
                raise e

    def _dispose_pvc(self):

        pvcs = client.CoreV1Api().list_namespaced_persistent_volume_claim(
            namespace=self.namespace, watch=False
        )

        for pvc in pvcs.items:

            if pvc.metadata.name in self.pvcs:

                try:
                    response = client.CoreV1Api().delete_namespaced_persistent_volume_claim(
                        name=pvc.metadata.name,
                        namespace=self.namespace,
                        body=client.V1DeleteOptions(),
                    )
                    print(response)
                except ApiException as e:
                    if e.status == 404:
                        pass
                    else:
                        raise e

    def _create_role(
        self,
        client,
        name: str,
        verbs: list,
        resources: list = ["pods", "pods/log"],
        api_groups: list = ["*"],
    ):

        metadata = self.client.V1ObjectMeta(name=name, namespace=self.namespace)

        rule = client.V1PolicyRule(
            api_groups=api_groups,
            resources=resources,
            verbs=verbs,
        )

        body = client.V1Role(metadata=metadata, rules=[rule])

        try:
            response = client.RbacAuthorizationV1Api(self.api_client).create_namespaced_role(
                self.namespace, body, pretty=True
            )
            return response

        except ApiException as e:
            if e.status == 409:
                pass
            else:
                raise e

    def _create_role_binding(self, name: str, role: str):

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
            response = client.RbacAuthorizationV1Api(self.api_client).create_namespaced_role_binding(
                self.namespace, body, pretty=True
            )
            return response
        except ApiException as e:
            if e.status == 409:
                pass
            else:
                raise e

    def _create_pvc(self, size):

        if size is None:
            size = "25Gi"

        pvcs_definition = []

        for pvc in self.pvcs:
            pvcs_definition.append(
                {
                    "name": pvc,
                    "size": size,
                    "storage_class": self.storage_class,
                    "access_modes": ["ReadWriteMany"],
                }
            )

        for pvc in pvcs_definition:

            metadata = client.V1ObjectMeta(name=pvc["name"], namespace=self.namespace)

            spec = client.V1PersistentVolumeClaimSpec(
                access_modes=pvc["access_modes"],
                resources=client.V1ResourceRequirements(requests={"storage": pvc["size"]}),
            )

            spec.storage_class_name = pvc["storage_class"]

            body = client.V1PersistentVolumeClaim(metadata=metadata, spec=spec)

            try:
                response = client.CoreV1Api(self.api_client).create_namespaced_persistent_volume_claim(
                    self.namespace, body, pretty=True
                )

            except ApiException as e:
                if e.status == 409:
                    pass
                else:
                    raise e

            created = False

            while not created:
                try:
                    response = client.CoreV1Api(self.api_client).read_namespaced_persistent_volume_claim(
                        name=pvc["name"], namespace=self.namespace
                    )
                    print(response)
                    created = True
                except ApiException as e:
                    if e.status == 404:
                        sleep(3)

    def _create_namespace(self, client):

        try:
            body = client.V1Namespace(metadata=client.V1ObjectMeta(name=self.namespace))
            response = client.CoreV1Api(self.api_client).create_namespace(body=body, async_req=False)
            return response
        except ApiException as e:
            if e.status == 409:
                pass
            else:
                raise e

    def _get_configmap(
        self,
        name: str,
    ):

        try:
            return self.client.CoreV1Api(self.api_client).read_namespaced_config_map(
                namespace=self.namespace, name=name
            )
        except ApiException as e:
            if e.status == 404:
                return None
            else:
                raise e

    def _create_secret(self, secret_name: str, cred_payload):

        self._delete_secret(namespace=self.namespace, secret_name=secret_name)

        data = {".dockerconfigjson": base64.b64encode(json.dumps(cred_payload).encode()).decode()}

        try:
            metadata = {"name": secret_name, "namespace": self.namespace}

            secret = client.V1Secret(
                api_version="v1",
                data=data,
                kind="Secret",
                metadata=metadata,
                type="kubernetes.io/dockerconfigjson",
            )

            client.CoreV1Api(self.api_client).create_namespaced_secret(
                namespace=self.namespace, body=secret
            )

        except ApiException as e:
            if e.status == 409:
                pass
            else:
                raise e

    def _delete_secret(self, secret_name):

        try:
            response = client.CoreV1Api(self.api_client).delete_namespaced_secret(
                namespace=self.namespace, name=secret_name
            )
            print(response)
        except ApiException as e:
            if e.status == 404:
                pass
            else:
                raise e

    def _patch_service_account(self, secret_name):
        # adds a secret to the namespace default service account

        service_account_body = client.CoreV1Api(self.api_client).read_namespaced_service_account(
            name="default", namespace=self.namespace
        )

        if service_account_body.secrets is None:
            service_account_body.secrets = []

        if service_account_body.image_pull_secrets is None:
            service_account_body.image_pull_secrets = []

        service_account_body.secrets.append({"name": secret_name})
        service_account_body.image_pull_secrets.append({"name": secret_name})

        try:
            client.CoreV1Api(self.api_client).patch_namespaced_service_account(
                name="default",
                namespace=self.namespace,
                body=service_account_body,
                pretty=True,
            )
        except ApiException as e:
            raise e
