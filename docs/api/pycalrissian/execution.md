# Module pycalrissian.execution

## Classes

### CalrissianExecution

```python3
class CalrissianExecution(
    job: pycalrissian.job.CalrissianJob,
    runtime_context: pycalrissian.context.CalrissianContext
)
```

#### Methods

    
#### get_completion_time

```python3
def get_completion_time(
    self
)
```

Returns either the completion time or the last transition time

    
#### get_file_from_volume

```python3
def get_file_from_volume(
    self,
    filenames
)
```

    
#### get_log

```python3
def get_log(
    self
)
```

Returns the job execution log

    
#### get_output

```python3
def get_output(
    self
) -> Dict
```

Returns the job output

    
#### get_start_time

```python3
def get_start_time(
    self
)
```

Returns the start time

    
#### get_status

```python3
def get_status(
    self
)
```

Returns the job status

    
#### get_tool_logs

```python3
def get_tool_logs(
    self
)
```

stages the tool logs from k8s volume

    
#### get_usage_report

```python3
def get_usage_report(
    self
) -> Dict
```

Returns the job usage report

    
#### get_waiting_pods

```python3
def get_waiting_pods(
    self
) -> List[kubernetes.client.models.v1_pod.V1Pod]
```

    
#### is_active

```python3
def is_active(
    self
) -> bool
```

Returns True if the job execution is on-going

    
#### is_complete

```python3
def is_complete(
    self
) -> bool
```

Returns True if the job execution is completed (success or failed)

    
#### is_succeeded

```python3
def is_succeeded(
    self
) -> bool
```

Returns True if the job execution is completed and succeeded

    
#### monitor

```python3
def monitor(
    self,
    interval: int = 5,
    grace_period=120,
    wall_time: Optional[int] = None
) -> None
```

    
#### submit

```python3
def submit(
    self
)
```

Submits the job to the cluster

### JobStatus

```python3
class JobStatus(
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
ACTIVE
```

```python3
FAILED
```

```python3
KILLED
```

```python3
SUCCEEDED
```

```python3
name
```

```python3
value
```