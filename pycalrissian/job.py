from typing import Dict


class CalrissianJob(object):
    def __init__(
        self,
        cwl,
        params,
        runtime_context,
        pod_env_vars: Dict = None,
        pod_node_selector: Dict = None,
        max_ram: int = 8,
        max_cores: int = 16,
        security_context: Dict = None,
        storage_class: str = None,
        debug=False,
        no_read_only=False,
    ):

        self.cwl = cwl
        self.params = params
        self.runtime_context = runtime_context

        self._create_cwl_cm(self)
        self._create_params_cm(self)

    def _create_cwl_cm(self):
        """Create configMap with CWL"""

    def _create_params_cm(self):
        """Create configMap with params"""

    def to_dict(self):
        """Serialize to a dictionary"""

    def to_k8s_job(self):
        """Cast to kubernetes Job"""
