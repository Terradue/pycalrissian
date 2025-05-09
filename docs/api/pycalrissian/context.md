# Module pycalrissian.context

## Classes

### CalrissianContext

```python3
class CalrissianContext(
    namespace: str,
    storage_class: str,
    volume_size: str,
    resource_quota: Dict = None,
    image_pull_secrets: Dict = None,
    kubeconfig_file: <class 'TextIO'> = None,
    labels: Dict = None,
    annotations: Dict = None
)
```

Creates a kubernetes namespace to run calrissian jobs

#### Static methods

    
#### retry

```python3
def retry(
    fun,
    max_tries=10,
    interval=5,
    **kwargs
)
```

#### Methods

    
#### create_additional_image_pull_secret

```python3
def create_additional_image_pull_secret(
    self,
    secrets_list
)
```

    
#### create_configmap

```python3
def create_configmap(
    self,
    name,
    key,
    content,
    annotations: Dict = {},
    labels: Dict = {}
)
```

    
#### create_image_pull_secret

```python3
def create_image_pull_secret(
    self,
    name
)
```

    
#### create_namespace

```python3
def create_namespace(
    self,
    labels: dict = None,
    annotations: dict = None
) -> kubernetes.client.models.v1_namespace.V1Namespace
```

    
#### create_pvc

```python3
def create_pvc(
    self,
    name,
    access_modes,
    size,
    storage_class
)
```

    
#### create_resource_quota

```python3
def create_resource_quota(
    self,
    name
)
```

    
#### create_role

```python3
def create_role(
    self,
    name: str,
    verbs: list,
    resources: list = ['pods', 'pods/log'],
    api_groups: list = ['*']
)
```

    
#### create_role_binding

```python3
def create_role_binding(
    self,
    name: str,
    role: str
)
```

    
#### delete_pod

```python3
def delete_pod(
    self,
    name
)
```

    
#### dispose

```python3
def dispose(
    self
)
```

    
#### initialise

```python3
def initialise(
    self
)
```

Create the kubernetes resources to run a Calrissian job

Arg:
    None

**Returns:**

| Type | Description |
|---|---|
| None | None |

    
#### is_config_map_created

```python3
def is_config_map_created(
    self,
    **kwargs
)
```

    
#### is_image_pull_secret_created

```python3
def is_image_pull_secret_created(
    self,
    **kwargs
)
```

    
#### is_namespace_created

```python3
def is_namespace_created(
    self,
    **kwargs
)
```

    
#### is_namespace_deleted

```python3
def is_namespace_deleted(
    self,
    **kwargs
)
```

Helper function for retry in dispose

    
#### is_object_created

```python3
def is_object_created(
    self,
    read_method,
    **kwargs
)
```

    
#### is_pvc_created

```python3
def is_pvc_created(
    self,
    **kwargs
)
```

    
#### is_resource_quota_created

```python3
def is_resource_quota_created(
    self,
    **kwargs
)
```

    
#### is_role_binding_created

```python3
def is_role_binding_created(
    self,
    **kwargs
)
```

    
#### is_role_created

```python3
def is_role_created(
    self,
    **kwargs
)
```

    
#### patch_service_account

```python3
def patch_service_account(
    self
)
```