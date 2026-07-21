import os

from setuptools import find_namespace_packages, find_packages, setup

setup_dir = os.path.abspath(os.path.dirname(__file__))


def read_file(filename):
    filepath = os.path.join(setup_dir, filename)
    with open(filepath) as file:
        return file.read()


def parse_git(root, **kwargs):
    """
    Parse function for setuptools_scm
    """
    from setuptools_scm.git import parse

    kwargs["describe_command"] = "git describe --dirty --tags --long"
    return parse(root, **kwargs)


setup(
    name="pelican-jupyter",
    use_scm_version=True,
    packages=(
        find_packages(
            include=[
                "pelican_jupyter",
                "pelican_jupyter.vendor",
                "pelican_jupyter.vendor.*",
            ]
        )
        + find_namespace_packages(include=["pelican.plugins.ipynb_reader*"])
    ),
    data_files=[("share/doc/pelican-jupyter", ["docs/PROVENANCE.md"])],
    # package_dir={"": "src"},
    zip_safe=False,
    include_package_data=False,
    # package_data={"pelican_jupyter": ["includes/*"]},
    # data_files=data_files,
    # cmdclass={"install": InstallCmd},
    # entry_points = {},
    python_requires=">=3.10,<3.14",
    setup_requires=["setuptools_scm"],
    install_requires=read_file("requirements.txt").splitlines(),
    extras_require={
        "test": ["pytest", "pytest-cov", "toml"],
        "dev": read_file("requirements-dev.txt").splitlines(),
    },
    description="Pelican plugin for blogging with Jupyter/IPython Notebooks",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    license="Apache-2.0",
    license_files=("LICENSE.txt",),
    author="Daniel Rodriguez and contributors",
    url="https://github.com/nekrasovp/pelican-jupyter",
    project_urls={
        "Source": "https://github.com/nekrasovp/pelican-jupyter",
        "Upstream": "https://github.com/danielfrg/pelican-jupyter",
    },
    keywords=[],
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)
