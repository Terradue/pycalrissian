class JobExecution(object):
    def __init__(self, job, runtime_context) -> None:
        self.job = job
        self.runtime_context = runtime_context

    def submit(self):
        """Submits the job to the cluster"""

    def get_status(self):
        """Returns the job status"""

    def is_complete(self):
        """Returns True if the job execution is completed (success or failed)"""

    def is_succeeded(self):
        """Returns True if the job execution is completed and succeeded"""

    def is_active(self):
        """Returns True if the job execution is on-going"""

    def get_output(self):
        """Returns the job output"""

    def get_log(self):
        """Returns the job execution log"""

    def get_usage_report(self):
        """Returns the job usage report"""
