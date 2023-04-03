# Command-line tool: calrissiantool

`calrissiantool` is a command-line tool to submit CWL documents to a Kubernetes cluster that relies on a calrissian job.

`calrissiantool` creates the required kubernetes resources to execute and monitor a calrissian job.

## Usage

```
Usage: calrissiantool [OPTIONS] CWL [PARAMS]...

  Execute a Calrissian job from a CWL description

Options:
  --max-ram TEXT             Maximum amount of RAM to use, e.g 1048576, 512Mi
                             or 2G. Follows k8s resource conventions
  --max-cores TEXT           Maximum number of CPU cores to use
  --volume-size TEXT         Size of the RWX volume for CWL temporary and
                             output files
  --pod-labels TEXT          YAML file of labels to add to pods submitted
  --pod-nodeselectors TEXT   YAML file of node selectors to select the nodes
                             where the pods will be scheduled
  --pod-serviceaccount TEXT  Service Account to use for pods management
  --usage-report TEXT        Output JSON file name to record resource usage
  --stdout TEXT              Output file name to tee standard output (CWL
                             output object)
  --stderr TEXT              Output file name to tee standard error to
                             (includes tool logs)
  --tool-logs                Retrieve the tool logs
  --keep-resources           Keep kubernetes resources. Defaults to False
  --debug                    Sets the debug mode
  --storage-class TEXT       ReadWriteMany storage class to use for the job
  --secret-config TEXT       Image pull secrets file  [required]
  --monitor-interval TEXT    Job execution monitoring interval in seconds
  --help                     Show this message and exit.
```

## Options

**--max-ram**

Maximum amount of RAM to use, e.g 1048576, 512Mi or 2G. Follows k8s resource conventions.
Clarissian will allocate tool pods within this RAM limit putting the remaining pods in a queue.

**--max-cores**

Maximum number of CPU cores to use. Clarissian will allocate tool pods within this number of cores limit putting the remaining pods in a queue.

**--volume-size**

Size of the ReadWriteMay volume for CWL temporary and output files

**--pod-labels**

YAML file of labels to add to pods submitted

## Examples

```
export KUBECONFIG=~/.kube/kubeconfig.yaml

calrissiantool \
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
