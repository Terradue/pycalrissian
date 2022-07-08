import os

from setuptools import find_packages, setup


def package_files(where):
    paths = []
    for directory in where:
        for (path, _, filenames) in os.walk(directory):
            for filename in filenames:
                paths.append(os.path.join(path, filename).replace("mosaic/", ""))
    return paths


extra_files = []

print(extra_files)
setup(
    description="pycalrissian",
    url="https://git.terradue.com",
    author="Terradue",
    author_email="fabrice.brito@terradue.com",
    license="EUPL",
    include_package_data=True,
    packages=find_packages(),
    zip_safe=False,
    entry_points={},
    package_data={"": extra_files},
)
