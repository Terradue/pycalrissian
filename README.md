# pycalrissian


## Development

Use the Visual Studio Code Remote Container configuration

Requirements:

* in your local `$HOME` you must have a `.kube` folder as it is mounted on the development container to access the kubernetes cluster

## Kubernetes

We suggest using microk8s and set the kubeconfig with:

```
microk8s config > ~/.kube/config
```
