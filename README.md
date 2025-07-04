# pycalrissian

_pycalrissian_ is a Python client library for running Common Workflow Language (CWL) descriptions on Kubernetes using [Calrissian](https://github.com/Duke-GCB/calrissian).

It provides simple objects and methods to:

* prepare a Kubernetes namespace ready to run Calrissian kubernetes jobs.
* create a Calrissian Kubernetes job in that namespace based on a CWL description and its parameters
* submit and monitor the job execution and retrieve usage, logs and outputs

Refer to the [documentation](https://terradue.github.io/pycalrissian/) to get started.

## Development

Use the Visual Studio Code Remote Container configuration.

Requirements:

* in your local `$HOME` you must have a `.kube` folder as it is mounted on the development container to access the kubernetes cluster

**Kubernetes resources for development and testing**

We suggest using microk8s and set the kubeconfig with:

```
microk8s config > ~/.kube/config
```


### Configure cluster with GPU:
Please follow the [instructions](https://minikube.sigs.k8s.io/docs/tutorials/nvidia/) to install NVIDIA plugins on your cluster.

Your GPU node must have appropriate labels so that the pod can be scheduled using a `nodeSelector`. For example:

```bash
kubectl label node <your-node-name> gpu=true
kubectl label node <your-node-name> accelerator=nvidia
```


> ✅ To test GPU functionality, you can run the unit tests:
>
> ```bash
> hatch shell
> nose2
> ```