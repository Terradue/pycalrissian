# Module pycalrissian.job

## Classes

### CalrissianJob

```python3
class CalrissianJob(
    cwl: Dict,
    params: Dict,
    runtime_context: pycalrissian.context.CalrissianContext,
    cwl_entry_point: str = None,
    pod_env_vars: Dict = None,
    pod_node_selector: Dict = None,
    max_ram: str = '8G',
    max_cores: str = '16',
    security_context: Dict = None,
    service_account: str = None,
    storage_class: str = None,
    debug: bool = False,
    no_read_only: bool = False,
    keep_pods: bool = False,
    backoff_limit: int = 2,
    tool_logs: bool = False
)
```

#### Static methods

    
#### create_container

```python3
def create_container(
    image,
    name,
    args,
    command,
    volume_mounts,
    env,
    pull_policy='Always'
)
```

    
#### create_job

```python3
def create_job(
    name,
    pod_template,
    namespace,
    backoff_limit=4
)
```

    
#### create_pod_template

```python3
def create_pod_template(
    name,
    containers,
    volumes,
    security_context,
    node_selector=None
)
```

Creates the pod template with the three containers

    
#### shorten_namespace

```python3
def shorten_namespace(
    value: str
) -> str
```

#### Methods

    
#### to_dict

```python3
def to_dict(
    self
)
```

Serialize to a dictionary

    
#### to_k8s_job

```python3
def to_k8s_job(
    self
)
```

Cast to kubernetes Job

    
#### to_yaml

```python3
def to_yaml(
    self,
    file_path
)
```

Serialize to YAML file

### ContainerNames

```python3
class ContainerNames(
    *args,
    **kwds
)
```

Create a collection of name/value pairs.

Example enumeration:

>>> class Color(Enum):
...     RED = 1
...     BLUE = 2
...     GREEN = 3

Access them by:

- attribute access:

  >>> Color.RED
  <Color.RED: 1>

- value lookup:

  >>> Color(1)
  <Color.RED: 1>

- name lookup:

  >>> Color['RED']
  <Color.RED: 1>

Enumerations can be iterated over, and know how many members they have:

>>> len(Color)
3

>>> list(Color)
[<Color.RED: 1>, <Color.BLUE: 2>, <Color.GREEN: 3>]

Methods can be added to enumerations, and members can have their own
attributes -- see the documentation for details.

#### Ancestors (in MRO)

* enum.Enum

#### Class variables

```python3
CALRISSIAN
```

```python3
name
```

```python3
value
```