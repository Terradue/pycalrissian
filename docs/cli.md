# Command-line tool: calrissian-runner

`calrissian-runner` (or `calrissian-tool`) is a command-line tool to submit CWL documents to a Kubernetes cluster that relies on a calrissian job.

`calrissian-runner` creates the required kubernetes resources to execute and monitor a calrissian job:

- a namespace
- an optional resource quota for that namespace
- a role for managing pods
- a role for reading pod logs
- role bindings for the roles above
- a persistant volume claim
- a secret for pulling container images
- patch the namespace service account
- a few config maps

## Usage

```
calrissian-runner --help
Usage: calrissian-runner [OPTIONS] CWL [PARAMS]...

  Execute a Calrissian job from a CWL description

Options:
  --max-ram TEXT                Maximum amount of RAM to use, e.g 1048576,
                                512Mi or 2G. Follows k8s resource conventions.
                                If not set, the value is taken from the CWL
                                resource requirements.
  --max-cores TEXT              Maximum number of CPU cores to use. If not
                                set, the value is taken from the CWL resource
                                requirements.
  --volume-size TEXT            Size of the RWX volume for CWL temporary and
                                output files. If not set, the value is taken
                                from the CWL resource requirements.
  --pod-labels PATH             YAML file of labels to add to pods submitted
  --pod-env-vars PATH           YAML file with pod env vars
  --pod-node-selectors PATH     YAML file of node selectors to select the
                                nodes where the pods will be scheduled
  --pod-serviceaccount TEXT     Service Account to use for pods management
                                (not implemented yet)
  --security-context PATH       Security context to use for running the pods
  --usage-report TEXT           Output JSON file name to record resource usage
  --stdout TEXT                 Output file name to tee standard output (CWL
                                output object)
  --stderr TEXT                 Output file name to tee standard error to
                                (includes tool logs)
  --tool-logs                   If set, the tool logs are retrieved
  --keep-resources              If set, the kubernetes resources are not
                                deleted.
  --debug                       If set, the logs contain the debug information
  --no-read-only                If set, does not set root directory in the pod
                                as read-only
  --storage-class TEXT          ReadWriteMany storage class to use for the job
                                [required]
  --secret-config TEXT          Image pull secrets file (e.g.
                                ~/.docker/config.json)  [required]
  --monitor-interval INTEGER    Job execution monitoring interval in seconds.
                                [default: 15]
  --namespace-labels PATH       A YAML file with the namespace labels
  --namespace-annotations PATH  A YAML file with the namespace annotations
  --namespace-quota PATH        A YAML file with the namespace resource quota
  --copy-results                If set, copies the results to the current
                                directory (experimental)
  --help                        Show this message and exit.
```

## Options

### --max-ram

Maximum amount of RAM to use, e.g 1048576, 512Mi or 2G. Follows k8s resource conventions.
Clarissian will allocate tool pods within this RAM limit putting the remaining pods in a queue.
If not set, this value is derived from the CWL `ResourceRequirement`, example:

```yaml
$graph:
- class Workflow
  ...
  requirements:
    ResourceRequirement:
      coresMax: 2
      ramMax: 2028
```

or

```yaml
$graph:
- class CommandLineTool
  ...
  requirements:
    ResourceRequirement:
      coresMax: 2
      ramMax: 2028
```

**--max-cores**

Maximum number of CPU cores to use. Clarissian will allocate tool pods within this number of cores limit putting the remaining pods in a queue.
If not set, this value is derived from the CWL `ResourceRequirement`

**--volume-size**

Size of the ReadWriteMay volume for CWL temporary and output files.
If not set, this value is derived from the CWL `ResourceRequirement`

**--pod-labels**

A YAML file of labels to add to the pods spawned by `calrissian`.

Example:

```
calrissian-runner --pod-labels pod-labels.yaml ...
```

Where the file `pod-labels.yaml` contains:

```
pod-label-1: value_1
pod-label-2: value_2
```

**--pod-env-vars**

A YAML file of environment variables to add to the pods spawned by `calrissian`.

Example:

```
calrissian-runner --pod-env-vars pod-env-vars.yaml ...
```

Where the file `pod-env-vars.yaml` contains:

```
env_var_1: "value_1"
env_var_2: "value_2"
```

**--pod-node-selector**

YAML file of node selectors to select the nodes where the pods will be scheduled by calrissian.

Example:

```
calrissian-runner --pod-node-selector pod-node-selector.yaml ...
```

Where the file `pod-node-selector` contains:

```
"k8s.scaleway.com/pool-name": default
```

**--pod-serviceaccount**

Not implemented. Service Account to use for pods management.

**--security-context**

A YAML file with the security context to use for running the pods.

**--usage-report**

Output JSON file name to record resource usage.

**--stdout**

Output file name to tee standard output (CWL output object)

**--stderr**

Output file name to tee standard error to (calrissian job stderr).

**--tool-logs**

If set, the tool logs are retrieved as local files named after the spawned pod name.

**--keep-resources**

If set, the kubernetes resources are not deleted. This is useful for debugging purposes.

**--debug**

If set, the standard error (calrissian job stderr) contains the debug information.

**--no-read-only**

If set, does not set the calrissian spawned pods root directory as read-only.

**--storage-class** [required]

ReadWriteMany storage class to use for the calrissina job volume.

**--secret-config** [required]

Image pull secrets file (e.g. ~/.docker/config.json) including the container repositories to pull the container images from.

**--monitor-interval**

Job execution monitoring interval in seconds. Defaults to 15 seconds.

**--namespace-labels**

A YAML file with the namespace labels.

Example:

```
calrissiantool --namespace-labels ns-labels.yaml ...
```

Where the file `ns-labels.yaml` contains:

```yaml
ns_label_1: value_1
ns_label_2: value_2
```

**--namespace-annotations**

A YAML file with the namespace annotations.

Example:

```
calrissiantool --namespace-annotations ns-annotations.yaml ...
```

Where the file `ns-annotations.yaml` contains:

```yaml
ns_annotation_1: value_1
ns_annotation_2: value_2
```

**--namespace-quota**

A YAML file with the namespace resource quota.

Example:

```
calrissiantool --namespace-quota resource-quota.yaml ...
```

Where the file `resource-quota.yaml` contains:

```yaml
requests.cpu: 32000m
requests.memory: 48G
```

**--pod-env-vars**

A YAML file with environment variables for the pods spwaned by `calrissian`

Example:

```
calrissiantool --pod-env-vars pod-env-vars.yaml ...
```

Where the file `pod-env-vars.yaml` contains:

```yaml
env_var_1: "value_1"
env_var_2: "value_2"
```

## Examples

```
export KUBECONFIG=~/.kube/kubeconfig.yaml

calrissian-runner \
    --max-ram 8G \
    --max-cores 2 \
    --volume-size 10Gi \
    --storage-class "openebs-nfs-test" \
    --secret-config ~/.docker/config.json \
    --monitor-interval 15 \
    --stdout out.json \
    --stderr log.err \
    --usage-report report.json \
    --debug \
    --keep-resources \
    "https://raw.githubusercontent.com/EOEPCA/app-snuggs/main/app-package.cwl#snuggs"
    params-snuggs.yml
```

Where `params-snuggs.yml` is a YAML file with:

```
input_reference:
- "https://earth-search.aws.element84.com/v0/collections/sentinel-s2-l2a-cogs/items/S2B_53HPA_20210723_0_L2A"
s_expression:
- "blue:(* B01 B01)"
```

```
calrissian-runner \
  --storage-class "openebs-nfs-test" \
  --secret-config ~/.docker/config.json \
  --stdout out.json \
  --stderr log.err \
  --debug \
  --usage-report report.json \
  --namespace-quota tests/resource_quota.yaml \
  --namespace-labels tests/ns-labels.yaml \
  --namespace-annotations tests/ns-annotations.yaml \
  --pod-env-vars tests/pod-env-vars.yaml  \
  --pod-node-selectors tests/pod-node-selectors.yaml \
  --volume-size 10G \
  "https://github.com/Terradue/ogc-eo-application-package-hands-on/releases/download/1.1.7/app-water-bodies.1.1.7.cwl#water_bodies" \
  tests/params.yml
```
