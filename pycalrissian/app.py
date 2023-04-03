import inspect
import json
import uuid
from collections import defaultdict
from datetime import datetime
from urllib.parse import urlparse

import attr
import click
import cwl_utils
import requests
import yaml
from cwl_utils.parser import load_document_by_yaml
from loguru import logger

from pycalrissian.context import CalrissianContext
from pycalrissian.execution import CalrissianExecution
from pycalrissian.job import CalrissianJob


# useful class for hints in CWL
@attr.s
class ResourceRequirement:
    """ResourceRequirement data class"""

    coresMin = attr.ib(default=None)
    coresMax = attr.ib(default=None)
    ramMin = attr.ib(default=None)
    ramMax = attr.ib(default=None)
    tmpdirMin = attr.ib(default=None)
    tmpdirMax = attr.ib(default=None)
    outdirMin = attr.ib(default=None)
    outdirMax = attr.ib(default=None)

    @classmethod
    def from_dict(cls, env):
        """Create a new instance from a dictionary of values."""
        return cls(
            **{k: v for k, v in env.items() if k in inspect.signature(cls).parameters}
        )


class Helper:
    def __init__(self, context, **kwargs) -> None:
        # get the click context and the kwargs
        self.context = context
        self.kwargs = kwargs

        # set the values from the arguments or the defaults
        self.storage_class = kwargs.get("storage_class", "default")

        # job resources
        self.max_ram = kwargs.get("max_ram", None)
        self.max_cores = kwargs.get("max_cores", None)
        self.volume_size = kwargs.get("volume_size", "10Gi")

        self.debug = kwargs.get("debug", False)
        self.no_read_only = kwargs.get("no_read_only", False)
        self.monitor_interval = kwargs.get("monitor_interval", 15)

        self.pod_service_account = kwargs.get("pod_service_account", None)
        self.usage_report = kwargs.get("usage_report", None)
        self.stdout = kwargs.get("stdout", None)
        self.stderr = kwargs.get("stderr", None)
        self.secret_config = kwargs.get("secret_config", None)
        self.cwl = kwargs.get("cwl")

        # namespace
        self.ns_resource_quota = kwargs.get("namespace_quota", None)
        self.ns_labels = kwargs.get("namespace_labels", None)
        self.ns_annotations = kwargs.get("namespace_annotations", None)

        # pods
        self.pod_env_vars = kwargs.get("pod_env_vars", None)
        self.pod_labels = kwargs.get("pod_labels", None)  # not implemented
        self.pod_node_selector = kwargs.get("pod_node_selector", None)
        self.security_context = kwargs.get("security_context", None)

        # flags
        self.tool_logs = kwargs.get("tool_logs", False)
        self.keep_resources = kwargs.get("keep_resources", False)

        logger.info(f"Processing {self.cwl}")
        if not kwargs["params"]:
            raise ValueError("No parameters provided")
        if kwargs["params"][0].startswith("--"):
            self.params = defaultdict(list)

            for extra_params in [
                {item.split("=")[0].replace("--", ""): item.split("=")[1]}
                for item in kwargs["params"]
            ]:  # you can list as many input dicts as you want here
                for key, value in extra_params.items():
                    self.params[key].append(value)
            self.params = dict(self.params)

        else:
            # opening a file
            with open(kwargs["params"][0], encoding="utf-8", mode="r") as stream:
                try:
                    # Converts yaml document to python object
                    self.params = yaml.safe_load(stream)
                    logger.info(f"Parameters provided in file {kwargs['params'][0]}")
                except yaml.YAMLError as exc:
                    logger.info(f"an error occured: {exc}")
        for key, value in self.params.items():
            logger.info(f"Parameter id {key}: {value}")

    @staticmethod
    def shorten_namespace(value: str) -> str:
        """shortens the namespace to 63 characters"""
        while len(value) > 63:
            value = value[:-1]
            while value.endswith("-"):
                value = value[:-1]
        return value

    def get_namespace_name(self):
        """creates or returns the namespace"""
        return self.shorten_namespace(
            f"calrissian-{str(datetime.now().timestamp()).replace('.', '')}"
            f"-{uuid.uuid4()}"
        )

    def get_resource_quota(self):
        """returns the namespace resource quota"""
        if self.ns_resource_quota:
            with open(self.ns_resource_quota) as stream:
                content = yaml.load(stream, Loader=yaml.SafeLoader)

            return content

    def get_namespace_labels(self):
        """return the namespace labels"""
        if self.ns_labels:
            with open(self.ns_labels) as stream:
                content = yaml.load(stream, Loader=yaml.SafeLoader)

            return content

    def get_namespace_annotations(self):
        """return the namespace annotations"""
        if self.ns_annotations:
            with open(self.ns_annotations) as stream:
                content = yaml.load(stream, Loader=yaml.SafeLoader)

            return content

    def get_pod_service_account(self):
        if self.pod_service_account:
            logger.warning("pod service account is not implemented")
            raise NotImplementedError

    def get_security_context(self):
        """return the security context"""
        if self.security_context:
            with open(self.security_context) as stream:
                content = yaml.load(stream, Loader=yaml.SafeLoader)

            return content

    def get_secret_config(self):
        with open(self.secret_config) as f:
            data = json.load(f)
        return data

    def get_volume_size(self):
        if self.volume_size:
            return self.volume_size
        else:
            resources = self.eval_resources()
            volume_size = max(
                max(resources["tmpdirMin"] or [0]), max(resources["tmpdirMax"] or [0])
            ) + max(
                max(resources["outdirMin"] or [0]), max(resources["outdirMax"] or [0])
            )

            return f"{volume_size}Mi"

    def get_monitoring_interval(self):
        return int(self.monitor_interval)

    def get_cwl(self):
        """read the cwl file with a YAML reader from a url or a local file"""
        cwl_file = self.cwl
        scheme = urlparse(cwl_file).scheme

        if scheme in ["http", "https"]:
            r = requests.get(cwl_file, stream=True)
            if r.status_code == 404:
                raise requests.RequestException("404 Not Found!")
            r.raw.decode_content = True
            content = yaml.safe_load(r.raw)
        else:
            with open(cwl_file) as fp:
                content = yaml.load(fp, Loader=yaml.SafeLoader)

        return content

    def get_cwl_entry_point(self):
        """returns the entry point of the cwl file"""
        if len(self.cwl.split("#")) == 2:
            entry_point = self.cwl.split("#")[1]
            logger.info(f"CWL entry point: {entry_point}")
        else:
            entry_point = "main"
            logger.warning("No entry point provided, using main")
        return entry_point

    def get_max_cores(self):
        """return the max cores"""
        if self.max_cores:
            return int(self.max_cores)
        else:
            resources = self.eval_resources()

            max_cores = max(
                max(resources["coresMin"] or [0]), max(resources["coresMax"] or [0])
            )
            logger.info(f"max cores: {max_cores}")
            return max_cores

    def get_max_ram(self):
        """return the max ram"""
        if self.max_ram:
            return self.max_ram
        else:
            resources = self.eval_resources()
            max_ram = max(
                max(resources["ramMin"] or [0]), max(resources["ramMax"] or [0])
            )
            logger.info(f"max ram: {max_ram}Mi")
            return f"{max_ram}Mi"

    def get_pod_env_vars(self):
        """return the pod env vars"""
        if self.pod_env_vars:
            with open(self.pod_env_vars) as fp:
                content = yaml.load(fp, Loader=yaml.SafeLoader)

            return content
        return None

    def get_pod_node_selector(self):
        """return the pod node selector"""
        if self.pod_node_selector:
            with open(self.pod_node_selector) as fp:
                content = yaml.load(fp, Loader=yaml.SafeLoader)

            return content

    def get_pod_labels(self):
        """return the pod labels"""
        if self.pod_labels:
            with open(self.pod_labels) as fp:
                content = yaml.load(fp, Loader=yaml.SafeLoader)

            return content

    def get_tool_logs(self):
        """return the tool logs flag, if true, the tool logs will be retrieved"""
        return self.tool_logs

    def handle_outputs(self, execution):
        """handle the outputs of the execution"""
        output = None

        try:
            output = execution.get_output()
        except json.decoder.JSONDecodeError:
            logger.error("Failed to retrieve the execution output")

        if self.stdout:
            try:
                json.dump(output, open(self.stdout, "w"))
                logger.info(f"Output retrieved and saved to {self.stdout}")
            except json.decoder.JSONDecodeError:
                logger.error("Failed to retrieve the execution output")

        if self.stderr:
            log = execution.get_log()
            with open(self.stderr, "w") as f:
                f.write(log)
            logger.info(f"Log retrieved and saved to {self.stderr}")

        if self.usage_report:
            usage_report = execution.get_usage_report()
            try:
                json.dump(usage_report, open(self.usage_report, "w"))
                logger.info(f"Usage report retrieved and saved to {self.usage_report}")
            except json.decoder.JSONDecodeError:
                logger.error("Failed to retrieve the usage report")

        if self.get_tool_logs():
            execution.get_tool_logs()

        return output

    def get_processing_parameters(self):
        return self.params

    @staticmethod
    def get_resource_requirement(elem):
        """Gets the ResourceRequirement out of a CommandLineTool or Workflow

        Args:
            elem (CommandLineTool or Workflow): CommandLineTool or Workflow

        Returns:
            cwl_utils.parser.cwl_v1_2.ResourceRequirement or ResourceRequirement
        """
        resource_requirement = [
            requirement
            for requirement in elem.requirements
            if isinstance(
                requirement,
                (
                    cwl_utils.parser.cwl_v1_0.ResourceRequirement,
                    cwl_utils.parser.cwl_v1_1.ResourceRequirement,
                    cwl_utils.parser.cwl_v1_2.ResourceRequirement,
                ),
            )
        ]

        if len(resource_requirement) == 1:
            return resource_requirement[0]

        # look for hints
        if elem.hints is not None:
            resource_requirement = [
                ResourceRequirement.from_dict(hint)
                for hint in elem.hints
                if hint["class"] == "ResourceRequirement"
            ]

        if len(resource_requirement) == 1:
            return resource_requirement[0]

    def eval_resources(self):
        """Evaluates the resource requirements of the cwl file"""
        cwl = load_document_by_yaml(self.get_cwl(), "io://")

        def get_object_by_id(cwl, id):
            ids = [elem.id.split("#")[-1] for elem in cwl]
            return cwl[ids.index(id)]

        resources = {
            "coresMin": [],
            "coresMax": [],
            "ramMin": [],
            "ramMax": [],
            "tmpdirMin": [],
            "tmpdirMax": [],
            "outdirMin": [],
            "outdirMax": [],
        }

        for elem in cwl:
            if isinstance(
                elem,
                (
                    cwl_utils.parser.cwl_v1_0.Workflow,
                    cwl_utils.parser.cwl_v1_1.Workflow,
                    cwl_utils.parser.cwl_v1_2.Workflow,
                ),
            ):
                if resource_requirement := self.get_resource_requirement(elem):
                    for resource_type in [
                        "coresMin",
                        "coresMax",
                        "ramMin",
                        "ramMax",
                        "tmpdirMin",
                        "tmpdirMax",
                        "outdirMin",
                        "outdirMax",
                    ]:
                        if getattr(resource_requirement, resource_type):
                            resources[resource_type].append(
                                getattr(resource_requirement, resource_type)
                            )
                for step in elem.steps:
                    if resource_requirement := self.get_resource_requirement(
                        get_object_by_id(cwl, step.run[1:])
                    ):
                        multiplier = 2 if step.scatter else 1
                        for resource_type in [
                            "coresMin",
                            "coresMax",
                            "ramMin",
                            "ramMax",
                            "tmpdirMin",
                            "tmpdirMax",
                            "outdirMin",
                            "outdirMax",
                        ]:
                            if getattr(resource_requirement, resource_type):
                                resources[resource_type].append(
                                    getattr(resource_requirement, resource_type)
                                    * multiplier
                                )
        return resources


@click.command(
    short_help="Calrissian tool",
    help="Execute a Calrissian job from a CWL description",
    context_settings=dict(
        ignore_unknown_options=True,
        # allow_extra_args=True,
    ),
)
@click.option(
    "--max-ram",
    "max_ram",
    help="Maximum amount of RAM to use, e.g 1048576, 512Mi or 2G."
    " Follows k8s resource conventions",
    required=False,
)
@click.option(
    "--max-cores",
    "max_cores",
    help="Maximum number of CPU cores to use",
    required=False,
)
@click.option(
    "--volume-size",
    "volume_size",
    help="Size of the RWX volume for CWL temporary and output files",
    required=False,
)
@click.option(
    "--pod-labels",
    "pod_labels",
    help="YAML file of labels to add to pods submitted",
    required=False,
    type=click.Path(exists=True),
)
@click.option(
    "--pod-env-vars",
    "pod_env_vars",
    help="YAML file with pod env vars",
    required=False,
    type=click.Path(exists=True),
)
@click.option(
    "--pod-node-selectors",
    "pod_node_selector",
    help="YAML file of node selectors to select "
    "the nodes where the pods will be scheduled",
    required=False,
    type=click.Path(exists=True),
)
@click.option(
    "--pod-serviceaccount",
    "pod_service_account",
    help="Service Account to use for pods management (not implemented yet)",
    required=False,
)
@click.option(
    "--security-context",
    "security_context",
    help="Security context to use fror running the pods",
    required=False,
)
@click.option(
    "--usage-report",
    "usage_report",
    help="Output JSON file name to record resource usage",
    required=False,
)
@click.option(
    "--stdout",
    "stdout",
    help="Output file name to tee standard output (CWL output object)",
    required=False,
)
@click.option(
    "--stderr",
    "stderr",
    help="Output file name to tee standard error to (includes tool logs)",
    required=False,
)
@click.option(
    "--tool-logs",
    "tool_logs",
    help="If set, the tool logs are retrieved",
    is_flag=True,
    required=False,
)
@click.option(
    "--keep-resources",
    "keep_resources",
    help="Keep kubernetes resources. Defaults to False",
    is_flag=True,
    required=False,
)
@click.option(
    "--debug",
    "debug",
    help="Sets the debug mode",
    is_flag=True,
    required=False,
)
@click.option(
    "--no-read-only",
    "no_read_only",
    help="Do not set root directory in the pod as read-only",
    is_flag=True,
    required=False,
)
@click.option(
    "--storage-class",
    "storage_class",
    help="ReadWriteMany storage class to use for the job",
    required=False,
)
@click.option(
    "--secret-config",
    "secret_config",
    help="Image pull secrets file",
    required=True,
)
@click.option(
    "--monitor-interval",
    "monitor_interval",
    help="Job execution monitoring interval in seconds",
    required=False,
)
@click.option(
    "--namespace-labels",
    "namespace_labels",
    help="A YAML file with the namespace labels",
    required=False,
    type=click.Path(exists=True),
)
@click.option(
    "--namespace-annotations",
    "namespace_annotations",
    help="A YAML file with the namespace annotations",
    required=False,
    type=click.Path(exists=True),
)
@click.option(
    "--namespace-quota",
    "namespace_quota",
    help="A YAML file with the namespace resource quota",
    required=False,
    type=click.Path(exists=True),
)
@click.argument("cwl", nargs=1)
@click.argument("params", required=False, nargs=-1)
@click.pass_context
def main(ctx, **kwargs):
    helper = Helper(ctx, **kwargs)

    if helper.get_pod_service_account():
        raise NotImplementedError("Service account is not implemented yet")

    namespace = helper.get_namespace_name()
    logger.info(f"namespace: {namespace}")
    session = CalrissianContext(
        namespace=namespace,
        storage_class=helper.storage_class,
        volume_size=helper.get_volume_size(),
        image_pull_secrets=helper.get_secret_config(),
        resource_quota=helper.get_resource_quota(),
        labels=helper.get_namespace_labels(),
        annotations=helper.get_namespace_annotations(),
    )

    session.initialise()

    processing_parameters = helper.get_processing_parameters()

    job = CalrissianJob(
        cwl=helper.get_cwl(),
        params=processing_parameters,
        runtime_context=session,
        cwl_entry_point=helper.get_cwl_entry_point(),
        max_cores=helper.get_max_cores(),
        max_ram=helper.get_max_ram(),
        pod_env_vars=helper.get_pod_env_vars(),
        pod_node_selector=helper.get_pod_node_selector(),
        debug=helper.debug,
        no_read_only=helper.no_read_only,
        tool_logs=helper.get_tool_logs(),
        security_context=helper.get_security_context(),
        service_account=helper.get_pod_service_account(),
    )

    execution = CalrissianExecution(job=job, runtime_context=session)

    execution.submit()

    execution.monitor(interval=helper.get_monitoring_interval())

    if execution.is_complete():
        logger.info("execution complete")

    if execution.is_succeeded():
        logger.info("execution successful")
        exit_value = 0
    else:
        logger.info("execution failed")
        exit_value = 1

    logger.info("handle outputs execution logs")

    output = helper.handle_outputs(execution)

    # clean-up
    if not helper.keep_resources:
        logger.info("clean-up kubernetes resources")
        session.dispose()

    print(json.dumps(output, indent=2))
    return exit_value


if __name__ == "__main__":
    main()