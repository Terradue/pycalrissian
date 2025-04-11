"""
The functions currently only support the copying of file
from pod and into the pod. Support for copying the entire directory is
yet to be added
"""
import os
import subprocess
import sys
import tarfile
import time
import uuid
from pathlib import Path
from tempfile import TemporaryFile
from typing import Dict

from kubernetes.client.rest import ApiException
from kubernetes.stream import stream
from pycalrissian.context import CalrissianContext


class HelperPod:
    def __init__(
        self,
        context: CalrissianContext,
        volume: Dict,
        volume_mount: Dict,
    ):
        self.context = context
        self.volume = volume
        self.volume_mount = volume_mount
        self.container_name = "container-kube-cp"
        self.pod_name = f"kube-cp-{self._get_uid()}"

        self._create_pod()

    @staticmethod
    def _get_uid():
        return str(uuid.uuid4())[-6:]

    def _create_pod(self):
        pod_manifest = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": self.pod_name},
            "spec": {
                "volumes": [self.volume],
                "containers": [
                    {
                        "image": "busybox",
                        "name": self.container_name,
                        "args": [
                            "/bin/sh",
                            "-c",
                            "while true;do date;sleep 5; done",
                        ],
                        "volumeMounts": [self.volume_mount],
                        "resources": {
                            "requests": {
                                "cpu": "100m",
                                "memory": "100Mi",
                            }
                        },
                    }
                ],
            },
        }
        resp = self.context.core_v1_api.create_namespaced_pod(
            body=pod_manifest,
            namespace=self.context.namespace,
        )
        while True:
            resp = self.context.core_v1_api.read_namespaced_pod(
                name=self.pod_name,
                namespace=self.context.namespace,
            )
            if resp.status.phase != "Pending":
                break
            time.sleep(1)

    def dismiss(self):
        try:
            self.context.core_v1_api.delete_namespaced_pod(
                self.pod_name,
                self.context.namespace,
            )
        except ApiException as e:
            print(
                f"Exception when calling CoreV1Api->delete_namespaced_pod: {e}\n",
                file=sys.stderr,
            )

    def copy_to_volume(self, src_path, dest_path):
        """
        This function copies a file inside the pod

        :param api_instance: coreV1Api()
        :param name: pod name
        :param ns: pod namespace
        :param source_file: Path of the file to be copied into pod
        :return: nothing
        """
        try:
            exec_command = [
                "tar",
                "xvf",
                "-",
                "-C",
                "/",
                "--absolute-names",
            ]
            api_response = stream(
                self.context.core_v1_api.connect_get_namespaced_pod_exec,
                self.pod_name,
                self.context.namespace,
                command=exec_command,
                stderr=True,
                stdin=True,
                stdout=True,
                tty=False,
                _preload_content=False,
            )

            with TemporaryFile() as tar_buffer:
                with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
                    tar.add(src_path, dest_path)

                tar_buffer.seek(0)
                commands = []
                commands.append(tar_buffer.read())

                while api_response.is_open():
                    api_response.update(timeout=1)
                    if api_response.peek_stdout():
                        print("STDOUT: %s" % api_response.read_stdout())
                    if api_response.peek_stderr():
                        print("STDERR: %s" % api_response.read_stderr())
                    if commands:
                        c = commands.pop(0)
                        api_response.write_stdin(c.decode())
                    else:
                        break
                api_response.close()
        except ApiException as e:
            print(
                "Exception when copying file to the pod%s \n" % e,
                file=sys.stderr,
            )

    def copy_from_volume(self, src_path, dest_path):
        """
        Copy files from a Kubernetes pod's volume to a local destination.

        :param src_path:
            The path of the file or directory to be copied from the pod's volume.
        :param dest_path:
            The local destination path where the file or directory should be copied to.
        """
        try:
            exec_command = [
                "tar",
                "cf",
                "-",
                src_path,
            ]

            with TemporaryFile() as tar_buffer:
                resp = stream(
                    self.context.core_v1_api.connect_get_namespaced_pod_exec,
                    self.pod_name,
                    self.context.namespace,
                    command=exec_command,
                    stderr=True,
                    stdin=True,
                    stdout=True,
                    tty=False,
                    _preload_content=False,
                )

                while resp.is_open():
                    resp.update(timeout=1)
                    if resp.peek_stdout():
                        out = resp.read_stdout()
                        # print("STDOUT: %s" % len(out))
                        tar_buffer.write(out.encode("utf-8"))
                    if resp.peek_stderr():
                        print("STDERR: %s" % resp.read_stderr())
                resp.close()

                tar_buffer.flush()
                tar_buffer.seek(0)

                with tarfile.open(
                    fileobj=tar_buffer,
                    mode="r:",
                ) as tar:
                    for member in tar.getmembers():
                        if member.isdir():
                            continue
                        fname = member.name.rsplit("/", 1)[1]
                        tar.makefile(
                            member,
                            dest_path + "/" + fname,
                        )
        except ApiException as e:
            if e.status != 404:
                # kubernetes.stream does not support connection to cluster via proxy
                # we are going to try to copy files using kubectl
                self.copy_from_volume_using_kubectl(src_path, dest_path)

    def copy_to_volume_using_kubectl(
        self,
        src_path,
        dest_path,
        max_attempts=5,
        retry_interval=5,
    ):
        """
        Copy a file from a Kubernetes pod using `kubectl cp` command.

        :param src_path:
            The source path of the file inside the pod where the volume is mounted.
        :param dest_path:
            The destination path on the local filesystem where the file
            should be copied.
        :param max_attempts:
            The maximum number of copy attempts in case of failure (default is 5).
        :param retry_interval:
            The time interval (in seconds) to wait before retrying a copy
            operation (default is 5 seconds).
        """
        filename = Path(src_path).name
        dest = os.path.join(dest_path, filename)
        exec_command = [
            "kubectl",
            "cp",
            src_path,
            f"{self.context.namespace}/{self.pod_name}:{dest_path}",
        ]

        for attempt in range(max_attempts):
            try:
                subprocess.check_call(exec_command)
                print(
                    f"File {filename} copied successfully to {dest}.",
                    file=sys.stderr,
                )
                break  # Exit loop on success
            except subprocess.CalledProcessError as e:
                print(
                    f"Error copying file (attempt {attempt + 1}/{max_attempts}): {e}",
                    file=sys.stderr,
                )

                if attempt < max_attempts - 1:
                    print(f"Retrying in {retry_interval} seconds...")
                    time.sleep(retry_interval)
                else:
                    print(
                        "Max retry attempts reached. Copy operation failed.",
                        file=sys.stderr,
                    )
                    break

    def copy_from_volume_using_kubectl(
        self,
        src_path,
        dest_path,
        max_attempts=5,
        retry_interval=5,
    ):
        """
        Copy a file from a Kubernetes pod using `kubectl cp` command.

        :param src_path:
            The source path of the file inside the pod where the volume is mounted.
        :param dest_path:
            The destination path on the local filesystem where the file
            should be copied.
        :param max_attempts:
            The maximum number of copy attempts in case of failure (default is 5).
        :param retry_interval:
            The time interval (in seconds) to wait before retrying a copy
            operation (default is 5 seconds).
        """
        filename = Path(src_path).name
        dest = os.path.join(dest_path, filename)
        exec_command = [
            "kubectl",
            "cp",
            f"{self.context.namespace}/{self.pod_name}:{src_path}",
            dest,
        ]

        for attempt in range(max_attempts):
            try:
                subprocess.check_call(exec_command)
                print(
                    f"File {filename} copied successfully to {dest}.",
                    file=sys.stderr,
                )
                break  # Exit loop on success
            except subprocess.CalledProcessError as e:
                print(
                    f"Error copying file (attempt {attempt + 1}/{max_attempts}): {e}",
                    file=sys.stderr,
                )

                if attempt < max_attempts - 1:
                    print(f"Retrying in {retry_interval} seconds...")
                    time.sleep(retry_interval)
                else:
                    print(
                        "Max retry attempts reached. Copy operation failed.",
                        file=sys.stderr,
                    )
                    break


def copy_to_volume(
    context: CalrissianContext,
    volume: Dict,
    volume_mount: Dict,
    source_paths: list,
    destination_path: str,
):
    helper_pod = HelperPod(
        context=context,
        volume=volume,
        volume_mount=volume_mount,
    )

    try:
        for source_path in source_paths:
            print(f"copy {source_path} to {destination_path}")
            """
            helper_pod.copy_to_volume(
                src_path=source_path,
                dest_path=os.path.join(
                    destination_path,
                    os.path.basename(source_path),
                ),
            )
            """
            helper_pod.copy_to_volume_using_kubectl(
                src_path=source_path, dest_path=destination_path
            )
    finally:
        helper_pod.dismiss()


def copy_from_volume(
    context: CalrissianContext,
    volume: Dict,
    volume_mount: Dict,
    source_paths: list,
    destination_path: str,
):
    helper_pod = HelperPod(
        context=context,
        volume=volume,
        volume_mount=volume_mount,
    )

    try:
        old_out_fd = os.dup(sys.stdout.fileno())
        old_out = sys.stdout
        os.dup2(sys.stderr.fileno(), 1)
        for source_path in source_paths:
            print(
                f"copy {source_path} to {destination_path}",
                file=sys.stderr,
            )
            helper_pod.copy_from_volume(
                src_path=source_path,
                dest_path=destination_path,
            )
    finally:
        sys.stdout.flush()
        os.dup2(old_out_fd, old_out.fileno())
        sys.stdout = old_out
        helper_pod.dismiss()
