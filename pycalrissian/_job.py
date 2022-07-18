import logging

from kubernetes import client

logging.basicConfig(level=logging.INFO)


class CalrissianJob:
    def __init__(self, session):

        self.namespace = session.namespace
        self.api_client = session.api_client
        self.batch_api = client.BatchV1Api()

    def execute(self):

        job = None
        self.batch_api.create_namespaced_job(self.namespace, job)

    def create_container(self, image, name, pull_policy, args):

        container = self.api_client.V1Container(
            image=image,
            name=name,
            image_pull_policy=pull_policy,
            args=[args],
            command=["python3", "-u", "./shuffler.py"],
        )

        logging.info(
            f"Created container with name: {container.name}, "
            f"image: {container.image} and args: {container.args}"
        )

        return container

    def create_pod_template(self, pod_name, container):
        pod_template = client.V1PodTemplateSpec(
            spec=client.V1PodSpec(restart_policy="Never", containers=[container]),
            metadata=client.V1ObjectMeta(name=pod_name, labels={"pod_name": pod_name}),
        )

        return pod_template

    def create_job(self, job_name, pod_template):
        metadata = client.V1ObjectMeta(name=job_name, labels={"job_name": job_name})

        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=metadata,
            spec=client.V1JobSpec(backoff_limit=0, template=pod_template),
        )

        return job
