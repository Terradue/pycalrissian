# import base64
# import os
# import unittest
# from loguru import logger
# import ast
# import yaml

# from pycalrissian.context import CalrissianContext
# from pycalrissian.execution import CalrissianExecution
# from pycalrissian.job import CalrissianJob

# os.environ["KUBECONFIG"] = "~/.kube/kubeconfig-t2-dev.yaml"


# class TestCalrissianExecutionLogs(unittest.TestCase):
#     @classmethod
#     def setUpClass(cls):
#         logger.info(
#             f"-----\n------------------------------  unit test for test_logs.py   ------------------------------\n\n"
#         )
#         cls.namespace = "job-namespace-unit-test"

#         username = "fabricebrito"
#         password = ""
#         email = "fabrice.brito@terradue.com"
#         registry = "https://index.docker.io/v1/"

#         auth = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode(
#             "utf-8"
#         )

#         secret_config = {
#             "auths": {
#                 registry: {
#                     "username": username,
#                     "password": password,
#                     "email": email,
#                     "auth": auth,
#                 },
#                 "registry.gitlab.com": {"auth": ""},  # noqa: E501
#             }
#         }

#         session = CalrissianContext(
#             namespace=cls.namespace,
#             storage_class="standard",
#             volume_size="10G",
#             image_pull_secrets=secret_config,
#         )

#         session.initialise()

#         cls.session = session

#     @classmethod
#     def tearDown(cls):
#         cls.session.dispose()
        
#     @unittest.skipIf(os.getenv("CI_TEST_SKIP") == "1", "Test is skipped via env variable")
#     def test_job_tool_logs(self):
#         logger.info(
#             f"-----\n------------------------------  test_job_tool_logs  (must skipped) ------------------------------\n\n"
#         )
#         # Set the environment variable for the Calrissian image
#         os.environ["CALRISSIAN_IMAGE"] = "terradue/calrissian:0.11.0-logs"

#         with open("tests/logs.cwl", "r") as stream:
#             cwl = yaml.safe_load(stream)

#         params = {"message": ["one", "two", "three"]}

#         pod_env_vars = {"A": "1", "B": "2"}

#         job = CalrissianJob(
#             cwl=cwl,
#             params=params,
#             runtime_context=self.session,
#             cwl_entry_point="main",
#             pod_env_vars=pod_env_vars,
#             pod_node_selector={
#                 "k8s.scaleway.com/pool-name": "processing-node-pool-dev"
#             },
#             debug=False,
#             max_cores=4,
#             max_ram="4G",
#             keep_pods=False,
#             backoff_limit=1,
#             tool_logs=True,
#         )

#         execution = CalrissianExecution(job=job, runtime_context=self.session)

#         execution.submit()

#         execution.monitor(interval=5, grace_period=600, wall_time=120)

#         print(execution.get_log())

#         print(execution.get_usage_report())

#         print(execution.get_output())

#         execution.get_tool_logs()

#         self.assertTrue(execution.is_succeeded())

#     def test_job_namespace_unit_test_disposing(self):
#         logger.info(
#             f"-----\n------------------------------  test_job_namespace_unit_test_disposing   ------------------------------\n\n"
#         )
#         response = self.session.dispose()
#         status_dict = ast.literal_eval(response.status)
#         self.assertEqual(status_dict["phase"], "Terminating")