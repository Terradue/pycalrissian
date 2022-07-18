import json
import os
from typing import Dict

import yaml
from kubernetes import client

from pycalrissian.context import CalrissianContext


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

        volume_mounts = [
            workflow_volume_mount,
            params_volume_mount,
            calrissian_wdir_volume_mount,
        ]

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

        # set the env var using the metadata
        env = client.V1EnvVar(
            name="CALRISSIAN_POD_NAME",
            value_from=client.V1EnvVarSource(
                field_ref=client.V1ObjectFieldSelector(field_path="metadata.name")
            ),
        )

        container_1 = self.create_container(
            name="calrissian",
            image="terradue/calrissian:0.11.0-sprint1",
            command=["calrissian"],
            args=[
                "--stdout",
                "path to stdout",
                "--stderr",
                "path to stderr",
                "--usage-report",
                "path to usage_report",
                "--max-ram",
                "max_ram",
                "--max-cores",
                "{{max_cores}}",
                "--tmp-outdir-prefix",
                "{{tmp_outdir_prefix}}",
                "--pod-env-vars",
                "{{pod_env_vars_path}}",
                "--pod-nodeselectors",
                "{{pod_nodeselectors_path}}",
                "--debug",
                "--no-read-only",
                "--outdir",
                "{{outdir}}",
                "/workflow/workflow.cwl",
                "/workflow/params.yml",
            ],
            env=[env],
            volume_mounts=volume_mounts,
        )

        container_2 = self.create_container(
            name="sidecar-container-usage",
            image="bitnami/kubectl",
            command=["sh", "-c"],
            args=[
                "while [ -z $(kubectl get pods $HOSTNAME -o jsonpath='{.status.containerStatuses[0].state.terminated}') ]; do sleep 5; done; [ -f {{usage_report}} ] && cat {{usage_report}}"  # noqa: E501
            ],
            env=[],
            volume_mounts=[calrissian_wdir_volume_mount],
        )

        container_3 = self.create_container(
            name="sidecar-container-output",
            image="bitnami/kubectl",
            command=["sh", "-c"],
            args=[
                "while [ -z $(kubectl get pods $HOSTNAME -o jsonpath='{.status.containerStatuses[0].state.terminated}') ]; do sleep 5; done; [ -f {{stdout}} ] && cat {{stdout}}"  # noqa: E501
            ],
            env=[],
            volume_mounts=[calrissian_wdir_volume_mount],
        )

        pod_spec = self.create_pod_template(
            name="calrissian_pod",
            containers=[container_1, container_2, container_3],
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
    def create_pod_template(name, containers, volumes):
        pod_template = client.V1PodTemplateSpec(
            spec=client.V1PodSpec(
                restart_policy="Never", containers=containers, volumes=volumes
            ),
            metadata=client.V1ObjectMeta(name=name, labels={"pod_name": name}),
        )

        return pod_template

    @staticmethod
    def create_job(name, pod_template):
        metadata = client.V1ObjectMeta(name=name, labels={"job_name": name})

        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=metadata,
            spec=client.V1JobSpec(backoff_limit=0, template=pod_template),
        )

        return job
