# import base64
# import os
# import ast
# import unittest
# import time
# import yaml
# from loguru import logger
# from pycalrissian.context import CalrissianContext
# from pycalrissian.execution import CalrissianExecution
# from pycalrissian.job import CalrissianJob

# os.environ["KUBECONFIG"] = "~/.kube/kubeconfig-t2-dev.yaml"



# def wait_for_pvc_bound(api, name, namespace, timeout=500):
#     for t in range(timeout):
#         pvc = api.read_namespaced_persistent_volume_claim(name=name, namespace=namespace)
#         phase = pvc.status.phase
#         if t % 10 == 0: 
#             logger.warning(f"PVC phase: {phase}")
#         if phase == "Bound":
#             return True
#         time.sleep(1)
#     raise TimeoutError("PVC did not reach 'Bound' state in time")


# class TestCalrissianExecution(unittest.TestCase):
#     @classmethod
#     def setUpClass(cls):
#         print(os.getenv("CI_TEST_SKIP", None))
#         logger.info(f"-----\n------------------------------  unit test for test_execution.py   ------------------------------\n\n")
#         cls.namespace = "job-namespace"

#         username = "fabricebrito"
#         password = "dckr_pat_cVqA0dOTLkQi6XxDklSPpH91Qic"
#         registry = "https://index.docker.io/v1/"

#         auth = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode(
#             "utf-8"
#         )

#         secret_config = {
#             "auths": {
#                 registry: {
#                     "username": username,
#                     "password": password,
#                     "auth": auth,
#                 }
#             }
#         }

#         session = CalrissianContext(
#             namespace=cls.namespace,
#             storage_class="microk8s-hostpath",  # "microk8s-hostpath",
#             volume_size="10G",
#             image_pull_secrets=secret_config,
#         )

#         session.initialise()
        
#         cls.session = session

#     @classmethod
#     def tearDown(cls):
#         cls.session.dispose()

#     @unittest.skipIf(os.getenv("CI_TEST_SKIP") == "1", "Test is skipped via env variable")
#     def test_simple_job(self):
#         logger.info(f"-----\n------------------------------  test_simple_job   ------------------------------\n\n")
#         with open("tests/simple.cwl", "r") as stream:

#             cwl = yaml.safe_load(stream)

#         params = {"message": "hello world!"}

#         pod_env_vars = {"A": "1", "B": "2"}

#         job = CalrissianJob(
#             cwl=cwl,
#             params=params,
#             runtime_context=self.session,
#             pod_env_vars=pod_env_vars,
#             debug=True,
#             max_cores=2,
#             max_ram="4G",
#             keep_pods=True,
#             backoff_limit=1,
#         )

#         execution = CalrissianExecution(job=job, runtime_context=self.session)

#         execution.submit()
#         wait_for_pvc_bound(self.session.core_v1_api, "calrissian-wdir", self.session.namespace)
#         execution.monitor(interval=5, wall_time=360)

#         print(f"complete {execution.is_complete()}")
        
#         print(execution.get_start_time())
#         print(execution.get_completion_time())
#         self.assertTrue(execution.is_succeeded())
#         logger.success(f"succeeded {execution.is_succeeded()}")

#     @unittest.skipIf(os.getenv("CI_TEST_SKIP") == "1", "Test is skipped via env variable")
#     def test_wrong_docker_pull_job(self):
#         logger.info(f"-----\n------------------------------  test_wrong_docker_pull_job   ------------------------------\n\n")
#         """tests the imagepullbackoff state of a pod, the job is killed"""
#         with open("tests/wrong_docker_pull.cwl", "r") as stream:

#             cwl = yaml.safe_load(stream)

#         params = {"message": "hello world!"}

#         pod_env_vars = {"A": "1", "B": "2"}

#         job = CalrissianJob(
#             cwl=cwl,
#             params=params,
#             runtime_context=self.session,
#             pod_env_vars=pod_env_vars,
#             debug=True,
#             max_cores=2,
#             max_ram="4G",
#             keep_pods=True,
#             backoff_limit=1,
#         )

#         execution = CalrissianExecution(job=job, runtime_context=self.session)

#         execution.submit()

#         execution.monitor(interval=5, grace_period=60, wall_time=120)

#         logger.success(f"execution killed {execution.killed}")
#         self.assertFalse(execution.is_succeeded())
#         logger.success(f"Is succeeded? {execution.is_succeeded()}")

#     @unittest.skipIf(os.getenv("CI_TEST_SKIP") == "1", "Test is skipped via env variable")
#     def test_high_reqs_job(self):
#         """tests the high reqs for RAM and cores, the job is killed"""
#         logger.info(f"-----\n------------------------------  test_high_reqs_job   ------------------------------\n\n")
#         with open("tests/high_reqs.cwl", "r") as stream:

#             cwl = yaml.safe_load(stream)

#         params = {"message": "hello world!"}

#         pod_env_vars = {"A": "1", "B": "2"}

#         job = CalrissianJob(
#             cwl=cwl,
#             params=params,
#             runtime_context=self.session,
#             pod_env_vars=pod_env_vars,
#             debug=True,
#             max_cores=2,
#             max_ram="4G",
#             keep_pods=True,
#             backoff_limit=1,
#         )

#         execution = CalrissianExecution(job=job, runtime_context=self.session)

#         execution.submit()

#         execution.monitor(interval=5, grace_period=60, wall_time=120)

#         logger.success(f"killed {execution.killed}")
#         self.assertFalse(execution.is_succeeded())

#     @unittest.skipIf(os.getenv("CI_TEST_SKIP") == "1", "Test is skipped via env variable")
#     def test_wall_time_reached_job(self):
#         """tests wall time reached, the job is killed"""
#         logger.info(f"-----\n------------------------------  test_wall_time_reached_job   ------------------------------\n\n")
#         with open("tests/sleep.cwl", "r") as stream:

#             cwl = yaml.safe_load(stream)

#         params = {"message": "hello world!"}

#         job = CalrissianJob(
#             cwl=cwl,
#             params=params,
#             runtime_context=self.session,
#             debug=True,
#             max_cores=2,
#             max_ram="4G",
#             keep_pods=True,
#             backoff_limit=1,
#         )

#         execution = CalrissianExecution(job=job, runtime_context=self.session)

#         execution.submit()

#         execution.monitor(interval=15, grace_period=30, wall_time=45)

#         print(f"killed {execution.killed}")
#         self.assertFalse(execution.is_succeeded())

#     @unittest.skipIf(os.getenv("CI_TEST_SKIP") == "1", "Test is skipped via env variable")
#     def test_wall_time_not_reached_job(self):
#         logger.info(f"-----\n------------------------------  test_wall_time_not_reached_job   ------------------------------\n\n")
#         """tests wall time reached, the job is killed"""
#         with open("tests/sleep.cwl", "r") as stream:

#             cwl = yaml.safe_load(stream)

#         params = {"message": "hello world!"}

#         job = CalrissianJob(
#             cwl=cwl,
#             params=params,
#             runtime_context=self.session,
#             debug=True,
#             max_cores=2,
#             max_ram="4G",
#             keep_pods=True,
#             backoff_limit=1,
#         )

#         execution = CalrissianExecution(job=job, runtime_context=self.session)

#         execution.submit()

#         execution.monitor(interval=15, grace_period=30, wall_time=120)

#         self.assertTrue(execution.is_succeeded())
#     def test_job_namespace_disposing(self):
#         logger.info(f"-----\n------------------------------  test_job_namespace_disposing   ------------------------------\n\n")
#         response = self.session.dispose()
#         status_dict = ast.literal_eval(response.status)
#         self.assertEqual(status_dict["phase"], "Terminating")

