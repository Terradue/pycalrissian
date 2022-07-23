import json
import time
from enum import Enum
from typing import Dict

from kubernetes.client.rest import ApiException
from loguru import logger

from pycalrissian.context import CalrissianContext
from pycalrissian.job import CalrissianJob, ContainerNames


class JobStatus(Enum):
    ACTIVE = "active"
    FAILED = "failed"
    SUCCEEDED = "succeeded"


class CalrissianExecution:
    def __init__(self, job: CalrissianJob, runtime_context: CalrissianContext) -> None:
        self.job = job
        self.runtime_context = runtime_context
        self.namespaced_job = None

    def submit(self):
        """Submits the job to the cluster"""
        logger.info(f"submit job {self.job.job_name}")
        response = self.runtime_context.batch_v1_api.create_namespaced_job(
            self.runtime_context.namespace, self.job.to_k8s_job()
        )
        self.namespaced_job_name = self.job.job_name
        self.namespaced_job = response
        logger.info(f"job {self.job.job_name} submitted")

    def get_status(self):
        """Returns the job status"""
        try:
            response = self.runtime_context.batch_v1_api.read_namespaced_job_status(
                name=self.namespaced_job_name,
                namespace=self.runtime_context.namespace,
                pretty=True,
            )
            if response.status.active is None and response.status.start_time is None:
                return JobStatus.ACTIVE
            if response.status.active:
                return JobStatus.ACTIVE
            if response.status.succeeded:
                return JobStatus.SUCCEEDED
            if response.status.failed:
                return JobStatus.FAILED
            return None
        except ApiException as e:
            logger.error(f"Exception when calling get status: {e}\n")
            raise e

    def is_complete(self) -> bool:
        """Returns True if the job execution is completed (success or failed)"""
        return self.get_status() in [JobStatus.SUCCEEDED, JobStatus.FAILED]

    def is_succeeded(self) -> bool:
        """Returns True if the job execution is completed and succeeded"""
        return self.get_status() in [JobStatus.SUCCEEDED]

    def is_active(self) -> bool:
        """Returns True if the job execution is on-going"""
        return self.get_status() in [JobStatus.ACTIVE]

    def get_output(self) -> Dict:
        """Returns the job output"""
        if self.is_succeeded:
            return json.loads(self._get_container_log(ContainerNames.SIDECAR_OUTPUT))
        return None

    def get_log(self):
        """Returns the job execution log"""
        if self.is_complete:
            return self._get_container_log(ContainerNames.CALRISSIAN)
        return None

    def get_usage_report(self) -> Dict:
        """Returns the job usage report"""
        if self.is_complete:
            return json.loads(self._get_container_log(ContainerNames.SIDECAR_USAGE))
        return None

    def _get_container_log(self, container):

        try:

            pod_label_selector = f"job-name={self.job.job_name}"
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
                container=container.value,
            ).data.decode("utf-8")

        except ApiException as e:
            logger.error(f"Exception when calling get status: {e}\n")
            raise e

    def get_start_time(self):
        """Returns the start time"""
        try:
            response = self.runtime_context.batch_v1_api.read_namespaced_job_status(
                name=self.namespaced_job_name,
                namespace=self.runtime_context.namespace,
                pretty=True,
            )
            if response.status.start_time is not None:
                return response.status.start_time
            return None
        except ApiException as e:
            logger.error(f"Exception when calling get status: {e}\n")
            raise e

    def get_completion_time(self):
        """Returns either the completion time or the last transition time"""
        try:
            response = self.runtime_context.batch_v1_api.read_namespaced_job_status(
                name=self.namespaced_job_name,
                namespace=self.runtime_context.namespace,
                pretty=True,
            )
            if response.status.completion_time is not None:
                return response.status.completion_time
            if response.status.conditions is not None:
                return response.status.conditions[0].last_transition_time
            return None
        except ApiException as e:
            logger.error(f"Exception when calling get status: {e}\n")
            raise e

    def monitor(self, interval: int = 5) -> None:

        if self.is_active():

            while self.is_active():
                logger.info(f"job {self.job.job_name} is active")
                time.sleep(interval)

            if self.is_complete():
                logger.info("execution is complete")
            if self.is_succeeded():
                logger.info("the outcome is: success!")

        else:
            logger.warning("job is not submitted")
