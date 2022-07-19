import json
import os
import uuid
from enum import Enum
from typing import Dict, List

import yaml
from kubernetes import client
from kubernetes.client.models.v1_container import V1Container

from pycalrissian.context import CalrissianContext


class ContainerNames(Enum):
    CALRISSIAN = "calrissian"
    SIDECAR_USAGE = "sidecar-container-usage"
    SIDECAR_OUTPUT = "sidecar-container-output"


class CalrissianJob(object):
    def __init__(
        self,
        cwl: Dict,
        params: Dict,
        runtime_context: CalrissianContext,
        pod_env_vars: Dict = None,
        pod_node_selector: Dict = None,
        max_ram: str = "8G",
        max_cores: str = "16",
        security_context: Dict = None,
        service_account: str = None,
        storage_class: str = None,
        debug: bool = False,
        no_read_only: bool = False,
    ):

        self.cwl = cwl
        self.params = params
        self.runtime_context = runtime_context
        self.pod_env_vars = pod_env_vars
        self.pod_node_selector = pod_node_selector
        self.max_ram = max_ram
        self.max_cores = max_cores
        self.security_context = security_context
        self.service_account = service_account
        self.storage_class = storage_class  # check this, is it needed?
        self.debug = debug
        self.no_read_only = no_read_only

        self.job_name = str(
            self.shorten_namespace(
                f"job-{uuid.uuid4()}-{uuid.uuid5(uuid.NAMESPACE_DNS, 'terradue.com')}"
            )
        )

        self._create_cwl_cm()
        self._create_params_cm()
        self._create_pod_env_vars_cm()
        self.calrissian_base_path = "/calrissian"

    def _create_cwl_cm(self):
        """Create configMap with CWL"""
        self.runtime_context.create_configmap(
            name="cwl-workflow", key="cwl-workflow", content=yaml.dump(self.cwl)
        )

    def _create_params_cm(self):
        """Create configMap with params"""
        self.runtime_context.create_configmap(
            name="params", key="params", content=yaml.dump(self.params)
        )

    def _create_pod_env_vars_cm(self):
        """Create configMap with pod environment variables"""
        self.runtime_context.create_configmap(
            name="pod-env-vars",
            key="pod-env-vars",
            content=json.dumps(self.pod_env_vars),
        )

    def _create_pod_node_selector_cm(self):
        """Create configMap with pod node selector"""
        self.runtime_context.create_configmap(
            name="pod-node-selector",
            key="pod-node-selector",
            content=json.dumps(self.pod_node_selector),
        )

    def to_dict(self):
        """Serialize to a dictionary"""
        return self.to_k8s_job().to_dict()

    def to_yaml(self, file_path):
        """Serialize to YAML file"""

        class Dumper(yaml.Dumper):
            def increase_indent(self, flow=False, *args, **kwargs):
                return super().increase_indent(flow=flow, indentless=False)

        with open(file_path, "w") as outfile:
            yaml.dump(
                self.runtime_context.api_client.sanitize_for_serialization(
                    self.to_k8s_job()
                ),
                outfile,
                Dumper=Dumper,
                default_flow_style=False,
            )

    def to_k8s_job(self):
        """Cast to kubernetes Job"""

        # the CWL workflow
        workflow_volume = client.V1Volume(
            name="volume-cwl-workflow",
            config_map=client.V1ConfigMapVolumeSource(
                name="cwl-workflow",
                optional=False,
                items=[
                    client.V1KeyToPath(
                        key="cwl-workflow", path="workflow.cwl", mode=0o644
                    )
                ],
                default_mode=0o644,
            ),
        )
        workflow_volume_mount = client.V1VolumeMount(
            mount_path="/workflow-input",
            name="volume-cwl-workflow",
            #            sub_path="cwl-workflow",
        )

        # the parameters
        params_volume = client.V1Volume(
            name="volume-params",
            config_map=client.V1ConfigMapVolumeSource(
                name="params",
                optional=False,
                items=[client.V1KeyToPath(key="params", path="params.yml", mode=0o644)],
                default_mode=0o644,
            ),
        )
        params_volume_mount = client.V1VolumeMount(
            mount_path="/workflow-params",
            name="volume-params",
            #            sub_path="params",
        )

        # the RWX volume for Calrissian from volume claim
        calrissian_wdir_volume = client.V1Volume(
            name="volume-calrissian-wdir",
            persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                claim_name="calrissian-wdir",
                read_only=False,
            ),
        )
        calrissian_wdir_volume_mount = client.V1VolumeMount(
            mount_path=self.calrissian_base_path,
            name="volume-calrissian-wdir",
            read_only=False,
        )

        volumes = [workflow_volume, params_volume, calrissian_wdir_volume]
        volume_mounts = [
            workflow_volume_mount,
            params_volume_mount,
            calrissian_wdir_volume_mount,
        ]

        if self.pod_env_vars:
            pod_env_vars_volume = client.V1Volume(
                name="volume-pod-env-vars",
                config_map=client.V1ConfigMapVolumeSource(
                    name="pod-env-vars",
                    optional=False,
                    items=[
                        client.V1KeyToPath(
                            key="pod-env-vars", path="pod_env_vars.json", mode=0o644
                        )
                    ],
                    default_mode=0o644,
                ),
            )
            pod_env_vars_volume_mount = client.V1VolumeMount(
                mount_path="/pod-env-vars",
                name="volume-pod-env-vars",
                #               sub_path="pod-env-vars",
            )

            volumes.append(pod_env_vars_volume)

            volume_mounts.append(pod_env_vars_volume_mount)

        if self.pod_node_selector:
            pod_node_selector_volume = client.V1Volume(
                name="volume-pod-node-selector",
                config_map=client.V1ConfigMapVolumeSource(
                    name="pod-node-selector",
                    optional=False,
                    items=[
                        client.V1KeyToPath(
                            key="pod-node-selector",
                            path="pod_node_selector.yml",
                            mode=0o644,
                        )
                    ],
                    default_mode=0o644,
                ),
            )
            pod_node_selector_volume_mount = client.V1VolumeMount(
                mount_path="/pod-node-selector",
                name="volume-pod-node-selector",
                #                sub_path="pod-node-selector",
            )

            volumes.append(pod_node_selector_volume)

            volume_mounts.append(pod_node_selector_volume_mount)

        pod_spec = self.create_pod_template(
            name="calrissian_pod",
            containers=[
                self._get_calrissian_container(volume_mounts=volume_mounts),
                self._get_side_car_container(
                    ContainerNames.SIDECAR_OUTPUT,
                    volume_mounts=[calrissian_wdir_volume_mount],
                ),
                self._get_side_car_container(
                    ContainerNames.SIDECAR_USAGE,
                    volume_mounts=[calrissian_wdir_volume_mount],
                ),
            ],
            volumes=volumes,
        )

        return self.create_job(
            name=self.job_name,
            pod_template=pod_spec,
            namespace=self.runtime_context.namespace,
            backoff_limit=2,
        )

    @staticmethod
    def create_container(
        image, name, args, command, volume_mounts, env, pull_policy="Always"
    ):

        container = client.V1Container(
            image=image,
            name=name,
            image_pull_policy=pull_policy,
            args=args,
            command=command,
            volume_mounts=volume_mounts,
            env=env,
        )

        return container

    @staticmethod
    def create_pod_template(name, containers, volumes, node_selector=None):
        """Creates the pod template with the three containers"""
        pod_template = client.V1PodTemplateSpec(
            spec=client.V1PodSpec(
                restart_policy="Never",
                containers=containers,
                volumes=volumes,
                node_selector=node_selector,
            ),
            metadata=client.V1ObjectMeta(name=name, labels={"pod_name": name}),
        )

        return pod_template

    @staticmethod
    def create_job(name, pod_template, namespace, backoff_limit=4):
        metadata = client.V1ObjectMeta(
            name=name, labels={"job_name": name}, namespace=namespace
        )

        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=metadata,
            spec=client.V1JobSpec(backoff_limit=backoff_limit, template=pod_template),
        )

        return job

    def _get_calrissian_args(self) -> List:

        args = []

        args.extend(
            ["--stdout", os.path.join(self.calrissian_base_path, "output.json")]
        )

        args.extend(["--stderr", os.path.join(self.calrissian_base_path, "stderr.log")])

        args.extend(
            ["--usage-report", os.path.join(self.calrissian_base_path, "usage.json")]
        )

        args.extend(
            ["--max-ram", f"{self.max_ram}", "--max-cores", f"{self.max_cores}"]
        )

        args.extend(["--tmp-outdir-prefix", f"{self.calrissian_base_path}/"])

        args.extend(["--outdir", f"{self.calrissian_base_path}/"])

        if self.pod_node_selector:
            args.extend(
                [
                    "--pod-nodeselectors",
                    os.path.join("/pod-node-selector", "pod_nodeselectors.yml"),
                ]
            )

        if self.pod_env_vars:
            args.extend(
                ["--pod-env-vars", os.path.join("/pod_env_vars", "pod_env_vars.json")]
            )

        if self.debug:
            args.append("--debug")

        if self.no_read_only:
            args.append("--no-read-only")

        args.extend(["/workflow-input/workflow.cwl", "/workflow-params/params.yml"])

        return args

    def _get_calrissian_container(self, volume_mounts: List) -> V1Container:
        """Creates the Calrissian container definition"""
        # set the env var using the metadata
        env = client.V1EnvVar(
            name="CALRISSIAN_POD_NAME",
            value_from=client.V1EnvVarSource(
                field_ref=client.V1ObjectFieldSelector(field_path="metadata.name")
            ),
        )

        container = self.create_container(
            name=ContainerNames.CALRISSIAN.value,
            image="terradue/calrissian:0.11.0-sprint1",  # overide as env var?
            command=["calrissian"],
            args=self._get_calrissian_args(),
            env=[env],
            volume_mounts=volume_mounts,
        )

        return container

    def _get_side_car_container(self, name, volume_mounts):
        """Creates the sidecar containers definition"""
        if name not in [ContainerNames.SIDECAR_USAGE, ContainerNames.SIDECAR_OUTPUT]:
            raise ValueError

        args = {}

        args[ContainerNames.SIDECAR_USAGE] = [
            "while [ -z $(kubectl get pods $HOSTNAME -o jsonpath='{{.status.containerStatuses[0].state.terminated}}') ]; do sleep 5; done; [ -f {0} ] && cat {0}".format(  # noqa: E501
                os.path.join(self.calrissian_base_path, "usage.json")
            )
        ]
        args[ContainerNames.SIDECAR_OUTPUT] = [
            "while [ -z $(kubectl get pods $HOSTNAME -o jsonpath='{{.status.containerStatuses[0].state.terminated}}') ]; do sleep 5; done; [ -f {0} ] && cat {0}".format(  # noqa: E501
                os.path.join(self.calrissian_base_path, "output.json")
            )
        ]

        container = self.create_container(
            name=name.value,
            image="bitnami/kubectl",  # overide as env var?
            command=["sh", "-c"],
            args=args[name],
            env=[],
            volume_mounts=volume_mounts,
        )

        return container

    @staticmethod
    def sanitize_k8_parameters(value: str) -> str:
        value = value.replace("_", "-").lower()
        while value.endswith("-"):
            value = value[:-1]
        return value

    @staticmethod
    def shorten_namespace(value: str) -> str:

        while len(value) > 63:
            value = value[:-1]
            while value.endswith("-"):
                value = value[:-1]
        return value
