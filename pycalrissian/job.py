import json
import os
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
        max_ram: int = 8,
        max_cores: int = 16,
        security_context: Dict = None,
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
        self.storage_class = storage_class  # check this, is it needed?
        self.debug = debug
        self.no_read_only = no_read_only

        self.job_name = "job-name"  # TODO

        self._create_cwl_cm()
        self._create_params_cm()
        self._create_pod_env_vars_cm()

    def _create_cwl_cm(self):
        """Create configMap with CWL"""
        self.runtime_context.create_configmap(
            name="cwl-workflow", key="cwl-workflow", content=yaml.dump(self.cwl)
        )

    def _create_params_cm(self):
        """Create configMap with params"""
        self.runtime_context.create_configmap(
            name="parameters", key="parameters", content=yaml.dump(self.params)
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

        with open(file_path, "w") as outfile:
            yaml.dump(self.to_k8s_job().to_dict(), outfile, default_flow_style=False)

    def to_k8s_job(self):
        """Cast to kubernetes Job"""

        workflow_volume_mount = client.V1VolumeMount(
            mount_path=os.path.join("/workflow/workflow.cwl"),
            name="cwl-workflow",
        )

        params_volume_mount = client.V1VolumeMount(
            mount_path=os.path.join("/workflow/params.yml"),
            name="parameters",
        )

        calrissian_wdir_volume_mount = client.V1VolumeMount(
            mount_path=os.path.join("/calrissian"),
            name="calrissian-wdir",
        )

        workflow_volume = client.V1Volume(
            name="cwl-workflow",
            config_map=client.V1ConfigMapVolumeSource(
                name="cwl-volume",
                optional=False,
                items=[client.V1KeyToPath(key="cwl-workflow", path="workflow.cwl")],
            ),
        )

        params_volume = client.V1Volume(
            name="params",
            config_map=client.V1ConfigMapVolumeSource(
                name="params-volume",
                optional=False,
                items=[client.V1KeyToPath(key="parameters", path="params.yml")],
            ),
        )

        # from volume claim
        calrissian_wdir_volume = client.V1Volume(
            name="calrissian-wdir",
            persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                claim_name="calrissian-wdir"
            ),
        )

        volumes = [workflow_volume, params_volume, calrissian_wdir_volume]

        volume_mounts = [
            workflow_volume_mount,
            params_volume_mount,
            calrissian_wdir_volume_mount,
        ]

        pod_spec = self.create_pod_template(
            name="calrissian_pod",
            containers=[
                self._get_calrissian_container(volume_mounts=volume_mounts),
                self._get_side_car_container(
                    ContainerNames.SIDECAR_OUTPUT, volume_mounts=[workflow_volume_mount]
                ),
                self._get_side_car_container(
                    ContainerNames.SIDECAR_USAGE, volume_mounts=[workflow_volume_mount]
                ),
            ],
            volumes=volumes,
        )

        return self.create_job(name=self.job_name, pod_template=pod_spec)

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
    def create_job(name, pod_template, backoff_limit=4):
        metadata = client.V1ObjectMeta(name=name, labels={"job_name": name})

        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=metadata,
            spec=client.V1JobSpec(backoff_limit=backoff_limit, template=pod_template),
        )

        return job

    def _get_calrissian_args(self) -> List:

        args = []

        args.extend(["--stdout", "path_to_stdout"])

        args.extend(["--stderr", "path_to_stderr"])

        args.extend(["--usage-report", "path_to_usage_report"])

        args.extend(["--max-ram", self.max_ram, "--max-cores", self.max_cores])

        args.extend(["--tmp-outdir-prefix", "tmp_outdir_prefix"])

        args.extend(["--outdir", "outdir"])

        if self.pod_node_selector:
            args.extend(["--pod-nodeselectors", "{{pod_nodeselectors_path}}"])

        if self.pod_env_vars:
            args.extend(["--pod-env-vars", "pod_env_vars_path"])

        if self.debug:
            args.append("--debug")

        if self.no_read_only:
            args.append("--no-read-only")

        args.extend(["/workflow/workflow.cwl", "/workflow/params.yml"])

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
            name=ContainerNames.CALRISSIAN,
            image="terradue/calrissian:0.11.0-sprint1",
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
            "while [ -z $(kubectl get pods $HOSTNAME -o jsonpath='{.status.containerStatuses[0].state.terminated}') ]; do sleep 5; done; [ -f {{usage_report}} ] && cat {{usage_report}}"  # noqa: E501
        ]
        args[ContainerNames.SIDECAR_OUTPUT] = [
            "while [ -z $(kubectl get pods $HOSTNAME -o jsonpath='{.status.containerStatuses[0].state.terminated}') ]; do sleep 5; done; [ -f {{stdout}} ] && cat {{stdout}}"  # noqa: E501
        ]

        container = self.create_container(
            name=name,
            image="bitnami/kubectl",
            command=["sh", "-c"],
            args=args[name],
            env=[],
            volume_mounts=volume_mounts,
        )

        return container
