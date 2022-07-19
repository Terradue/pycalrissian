from enum import Enum

from kubernetes.client.rest import ApiException

from pycalrissian.context import CalrissianContext
from pycalrissian.job import CalrissianJob, ContainerNames


class JobStatus(Enum):
    ACTIVE = "active"
    FAILED = "failed"
    SUCCEEDED = "succeeded"


class JobExecution(object):
    def __init__(self, job: CalrissianJob, runtime_context: CalrissianContext) -> None:
        self.job = job
        self.runtime_context = runtime_context
        self.namespaced_job = None

    def submit(self):
        """Submits the job to the cluster"""
        response = self.runtime_context.batch_v1_api.create_namespaced_job(
            self.runtime_context.namespace, self.job.to_k8s_job()
        )
        self.namespaced_job_name = self.job.job_name
        self.namespaced_job = response

    def get_status(self):
        """Returns the job status"""
        try:
            response = self.runtime_context.batch_v1_api.read_namespaced_job_status(
                name=self.namespaced_job_name,
                namespace=self.runtime_context.namespace,
                pretty=True,
            )
            print(response.status)
            if response.status.active is None and response.status.start_time is None:
                return JobStatus.ACTIVE
            if response.status.active:
                return JobStatus.ACTIVE
            if response.status.succeeded:
                return JobStatus.SUCCEEDED
            if response.status.failed:
                return JobStatus.FAILED
        except ApiException as e:
            print("Exception when calling get status: %s\n" % e)
            raise e

    def is_complete(self):
        """Returns True if the job execution is completed (success or failed)"""
        if self.get_status() in [JobStatus.SUCCEEDED, JobStatus.FAILED]:
            return True
        else:
            return False

    def is_succeeded(self):
        """Returns True if the job execution is completed and succeeded"""
        if self.get_status() in [JobStatus.SUCCEEDED]:
            return True
        else:
            return False

    def is_active(self):
        """Returns True if the job execution is on-going"""
        if self.get_status() in [JobStatus.ACTIVE]:
            return True
        else:
            return False

    def get_output(self):
        """Returns the job output"""
        if self.is_succeeded:
            return self._get_container_log(ContainerNames.SIDECAR_OUTPUT)

    def get_log(self):
        """Returns the job execution log"""
        if self.is_complete:
            return self._get_container_log(ContainerNames.CALRISSIAN)

    def get_usage_report(self):
        """Returns the job usage report"""
        if self.is_complete:
            return self._get_container_log(ContainerNames.SIDECAR_USAGE)

    def _get_container_log(self, container):

        print(f"container: {container}")

        try:

            pod_label_selector = f"job-name={self.job.job_name}"
            pods_list = self.runtime_context.core_v1_api.list_namespaced_pod(
                namespace=self.runtime_context.namespace,
                label_selector=pod_label_selector,
                timeout_seconds=10,
            )
            pod_name = pods_list.items[0].metadata.name
            print(f"podname: {pod_name}")

            return self.runtime_context.core_v1_api.read_namespaced_pod_log(
                name=pod_name,
                namespace=self.runtime_context.namespace,
                _return_http_data_only=True,
                _preload_content=False,
                container=container.value,
            ).data.decode("utf-8")

        except ApiException as e:
            print("Exception when calling get status: %s\n" % e)
            raise e

    def get_start_time(self):

        try:
            response = self.runtime_context.batch_v1_api.read_namespaced_job_status(
                name=self.namespaced_job_name,
                namespace=self.runtime_context.namespace,
                pretty=True,
            )
            if response.status.start_time is not None:
                return response.status.start_time
        except ApiException as e:
            print("Exception when calling get status: %s\n" % e)
            raise e

    def get_completion_time(self):

        try:
            response = self.runtime_context.batch_v1_api.read_namespaced_job_status(
                name=self.namespaced_job_name,
                namespace=self.runtime_context.namespace,
                pretty=True,
            )
            if response.status.completion_time is not None:
                return response.status.completion_time
            elif (
                response.status.conditions is not None
                and "last_transition_time" in response.status.conditions[0].keys()
            ):
                return response.status.conditions[0]["'last_transition_time'"]
        except ApiException as e:
            print("Exception when calling get status: %s\n" % e)
            raise e
