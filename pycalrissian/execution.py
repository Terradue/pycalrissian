from enum import Enum

from kubernetes.client.models.v1_job import V1Job
from kubernetes.client.rest import ApiException

from pycalrissian.context import CalrissianContext


class JobStatus(Enum):
    ACTIVE = "active"
    FAILED = "failed"
    SUCCEEDED = "succeeded"


class JobExecution(object):
    def __init__(self, job: V1Job, runtime_context: CalrissianContext) -> None:
        self.job = job
        self.runtime_context = runtime_context
        self.namespaced_job = None

    def submit(self):
        """Submits the job to the cluster"""
        response = self.runtime_context.batch_v1_api.create_namespaced_job(
            self.runtime_context.namespace, self.job
        )
        self.namespaced_job_name = ""
        self.namespaced_job = response

    def get_status(self):
        """Returns the job status"""
        try:
            response = self.runtime_context.batch_v1_api.read_namespaced_job_status(
                name=self.namespaced_job_name,
                namespace=self.runtime_context.namespace,
                pretty=True,
            )

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
            return self.get_container_log("sidecar-container-output")

    def get_log(self):
        """Returns the job execution log"""
        if self.is_succeeded:
            return self.get_container_log("calrissian")

    def get_usage_report(self):
        """Returns the job usage report"""
        if self.is_succeeded:
            return self.get_container_log("sidecar-container-usage")

    def get_container_log(self, container):

        if self.is_succeeded:
            try:
                response = self.runtime_context.batch_v1_api.read_namespaced_job_status(
                    name=self.namespaced_job_name,
                    namespace=self.runtime_context.namespace,
                    pretty=True,
                )
                controller_uid = response.metadata.labels["controller-uid"]

                pod_label_selector = "controller-uid=" + controller_uid
                pods_list = self.runtime_context.core_v1_api.list_namespaced_pod(
                    namespace=self.runtime_context.namespace,
                    label_selector=pod_label_selector,
                    timeout_seconds=10,
                )
                pod_name = pods_list.items[0].metadata.name

                return self.runtime_context.core_v1_api.read_namespaced_pod_log(
                    name=pod_name,
                    namespace=self.runtime_context.namespace,
                    _return_http_data_only=True,
                    _preload_content=False,
                    container=container,
                ).data.decode("utf-8")

            except ApiException as e:
                print("Exception when calling get status: %s\n" % e)
                raise e
