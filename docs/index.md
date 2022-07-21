# pycalrissian

_pycalrissian_ is a Python client library for running Common Workflow Language (CWL) descriptions on Kubernetes using [Calrissian](https://github.com/Duke-GCB/calrissian).

It provides simple objects and methods to:

* prepare a Kubernetes namespace ready to run Calrissian kubernetes jobs.
* create a Calrissian Kubernetes job in that namespace based on a CWL description and its parameters
* submit and monitor the job execution and retrieve usage, logs and outputs

Refer to the [installation](installation/) documentation for installing _pycalrissian_.

Refer to the [getting started](gettingstarted/) documentation to get started with _pycalrissian_.

Refer to the [API](api/pycalrissian/) documentation to learn more about the _pycalrissian_ API.
