import unittest

from click.testing import CliRunner
from pycalrissian import app


class TestCli(unittest.TestCase):
    def setUp(self):
        pass

    def test_water_bodies(self):
        runner = CliRunner()
        result = runner.invoke(
            app.main,
            [
                "--max-ram",
                "8G",
                "--max-cores",
                "2",
                "--volume-size",
                "10Gi",
                "--storage-class",
                "openebs-nfs-test",
                "--secret-config",
                "~/.docker/config.json",
                "--monitor-interval",
                "15",
                "--stdout",
                "this-is-the-stdout.json",
                "https://github.com/Terradue/ogc-eo-application-package-hands-on/"
                "releases/download/1.1.6/app-water-bodies.1.1.6.cwl#water_bodies",
                "params.yml",
            ],
        )

        print(result.output)
