# Module pycalrissian.utils

The functions currently only support the copying of file

from pod and into the pod. Support for copying the entire directory is
yet to be added

## Functions

    
### copy_from_volume

```python3
def copy_from_volume(
    context: pycalrissian.context.CalrissianContext,
    volume: Dict,
    volume_mount: Dict,
    source_paths: list,
    destination_path: str
)
```

    
### copy_to_volume

```python3
def copy_to_volume(
    context: pycalrissian.context.CalrissianContext,
    volume: Dict,
    volume_mount: Dict,
    source_paths: list,
    destination_path: str
)
```

## Classes

### HelperPod

```python3
class HelperPod(
    context: pycalrissian.context.CalrissianContext,
    volume: Dict,
    volume_mount: Dict
)
```

#### Methods

    
#### copy_from_volume

```python3
def copy_from_volume(
    self,
    src_path,
    dest_path
)
```

Copy files from a Kubernetes pod's volume to a local destination.

**Parameters:**

| Name | Type | Description | Default |
|---|---|---|---|
| src_path | None | The path of the file or directory to be copied from the pod's volume. | None |
| dest_path | None | The local destination path where the file or directory should be copied to. | None |

    
#### copy_from_volume_using_kubectl

```python3
def copy_from_volume_using_kubectl(
    self,
    src_path,
    dest_path,
    max_attempts=5,
    retry_interval=5
)
```

Copy a file from a Kubernetes pod using `kubectl cp` command.

**Parameters:**

| Name | Type | Description | Default |
|---|---|---|---|
| src_path | None | The source path of the file inside the pod where the volume is mounted. | None |
| dest_path | None | The destination path on the local filesystem where the file<br>should be copied. | None |
| max_attempts | None | The maximum number of copy attempts in case of failure (default is 5). | None |
| retry_interval | None | The time interval (in seconds) to wait before retrying a copy<br>operation (default is 5 seconds). | None |

    
#### copy_to_volume

```python3
def copy_to_volume(
    self,
    src_path,
    dest_path
)
```

This function copies a file inside the pod

**Parameters:**

| Name | Type | Description | Default |
|---|---|---|---|
| api_instance | None | coreV1Api() | None |
| name | None | pod name | None |
| ns | None | pod namespace | None |
| source_file | None | Path of the file to be copied into pod | None |

**Returns:**

| Type | Description |
|---|---|
| None | nothing |

    
#### copy_to_volume_using_kubectl

```python3
def copy_to_volume_using_kubectl(
    self,
    src_path,
    dest_path,
    max_attempts=5,
    retry_interval=5
)
```

Copy a file from a Kubernetes pod using `kubectl cp` command.

**Parameters:**

| Name | Type | Description | Default |
|---|---|---|---|
| src_path | None | The source path of the file inside the pod where the volume is mounted. | None |
| dest_path | None | The destination path on the local filesystem where the file<br>should be copied. | None |
| max_attempts | None | The maximum number of copy attempts in case of failure (default is 5). | None |
| retry_interval | None | The time interval (in seconds) to wait before retrying a copy<br>operation (default is 5 seconds). | None |

    
#### dismiss

```python3
def dismiss(
    self
)
```