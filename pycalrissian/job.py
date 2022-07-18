class CalrissianJob(object):
    def __init__(self, cwl, params, runtime_context):

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
