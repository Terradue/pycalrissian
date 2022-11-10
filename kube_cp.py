"""
The functions currently only support the copying of file
from pod and into the pod. Support for copying the entire directory is
yet to be added
"""
import tarfile
import time
from tempfile import TemporaryFile

from kubernetes import client, config
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream

config.load_config()
api_instance = client.CoreV1Api()


class KubeCopy:
    def __init__(self, volumes, volume_mounts):

        print(volume_mounts)
        self.volumes = volumes
        self.volume_mounts = volume_mounts
        self.namespace = "calrissian-session"
        self.container_name = "container-kube-cp"
        self.pod_name = "kube-cp"

        metadata = client.V1ObjectMeta(name=self.pod_name, namespace=self.namespace)

        container = client.V1Container(
            image="docker.io/busybox",
            name="busybox",
            volume_mounts=self.volume_mounts,
            command=["sleep"],
            args=["300"],
        )

        pod_spec = client.V1PodSpec(
            containers=[container],
            volumes=self.volumes,
            restart_policy="Never",
            node_selector={"k8s.scaleway.com/pool-name": "default"},
        )

        pod = client.V1Pod(
            api_version="v1", kind="Pod", metadata=metadata, spec=pod_spec
        )

        print(pod.to_dict())  # volume_mounts are ok, volumes missing

        # resp = api_instance.create_namespaced_pod(
        #    body=pod.to_dict(), namespace=self.namespace
        # )

        pod_manifest = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": self.pod_name},
            "spec": {
                "volumes": [
                    {
                        "name": "calrissian-input-data",
                        "persistentVolumeClaim": {"claimName": "calrissian-input-data"},
                    }
                ],
                "containers": [
                    {
                        "image": "busybox",
                        "name": "sleep",
                        "args": ["/bin/sh", "-c", "while true;do date;sleep 5; done"],
                        "volumeMounts": [
                            {
                                "name": "calrissian-input-data",
                                "mountPath": "/calrissian-input",
                            }
                        ],
                    }
                ],
            },
        }
        resp = api_instance.create_namespaced_pod(
            body=pod_manifest, namespace=self.namespace
        )
        while True:
            resp = api_instance.read_namespaced_pod(
                name=self.pod_name, namespace=self.namespace
            )
            if resp.status.phase != "Pending":
                break
            time.sleep(1)
        print("Done.")

    def copy_file_inside_pod(self, src_path, dest_path):
        """
        This function copies a file inside the pod
        :param api_instance: coreV1Api()
        :param name: pod name
        :param ns: pod namespace
        :param source_file: Path of the file to be copied into pod
        :return: nothing
        """
        config.load_config()
        api_instance = client.CoreV1Api()
        # api_instance = get_k8s_client_corev1()
        try:
            exec_command = ["tar", "xvf", "-", "-C", "/"]
            api_response = stream(
                api_instance.connect_get_namespaced_pod_exec,
                self.pod_name,
                self.namespace,
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
            print("Exception when copying file to the pod%s \n" % e)

    def copy_file_from_pod(self, src_path, dest_path):
        """

        :param pod_name:
        :param src_path:
        :param dest_path:
        :param namespace:
        :return:
        """

        config.load_config()
        api_instance = client.CoreV1Api()
        exec_command = ["tar", "cf", "-", src_path]

        with TemporaryFile() as tar_buffer:
            resp = stream(
                api_instance.connect_get_namespaced_pod_exec,
                self.pod_name,
                self.namespace,
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

            with tarfile.open(fileobj=tar_buffer, mode="r:") as tar:
                for member in tar.getmembers():
                    if member.isdir():
                        continue
                    fname = member.name.rsplit("/", 1)[1]
                    tar.makefile(member, dest_path + "/" + fname)


# copy_file_from_pod(pod_name="my-calrissian-session-59fbfbf465-2dd66",
# namespace='calrissian-session', src_path="/tmp/abc.txt", dest_path="./")

# the RWX volume for Calrissian from volume claim

calrissian_base_path = "/calrissian-input"
calrissian_wdir_volume_mount = client.V1VolumeMount(
    mount_path=calrissian_base_path,
    name="calrissian-input-data",
    read_only=False,
)
calrissian_wdir_volume = client.V1Volume(
    name="calrissian-input-data",
    persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
        claim_name="calrissian-input-data",
        read_only=False,
    ),
)
volume_mounts = [
    calrissian_wdir_volume_mount,
]

volumes = [calrissian_wdir_volume]

cp = KubeCopy(volumes=volumes, volume_mounts=volume_mounts)

cp.copy_file_from_pod(src_path="/calrissian-input/bcd.txt", dest_path="./")
