
```
sudo snap install microk8s --classic
```

```
sudo usermod -a -G microk8s fbrito
sudo chown -f -R fbrito ~/.kube
```

```
newgrp microk8s
```

```
microk8s enable dashboard dns registry istio hostpath-storage rbac
```

List the storage class:

```
microk8s kubectl get storageclass
```

```
NAME                          PROVISIONER            RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
microk8s-hostpath (default)   microk8s.io/hostpath   Delete          WaitForFirstConsumer   false                  13m
```

## kubeconfig

```
cd $HOME
mkdir -p .kube
cd .kube
microk8s config > microk8s.config
```
