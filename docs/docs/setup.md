## Installation

1. Create a new environment using either [`conda`](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-with-commands) (recommended) or [`venv`](https://docs.python.org/3/library/venv.html#creating-virtual-environments)
and [activate it](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#activating-an-environment)

1. Use [UPOD's Cookiecutter for Data Science Projects](https://github.com/UPOD-datascience/cookiecutter-ds) and generate a new project template.

1. Install the `PyCellDyn` package using `pip` with the following command:

   ```
   pip install git+https://github.com/UPOD-datascience/pycelldyn
   ```
   
   3.1 `pip` will try to install the required dependencies. However, for some reason sometimes the SSL certificate can't be confirmed and the installation throws an error:
   
   ```
   Could not fetch URL https://pypi.python.org/simple/PACKAGENAME/: There was a problem confirming the ssl certificate: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:777) - skipping
   Could not find a version that satisfies the requirement PACKAGENAME (from versions: XXX)
   ```
   
   In that case, you need to install the missing packages one by one by hand with the following command:
   
   ```
   pip install PACKAGENAME --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --trusted-host pypi.org
   ```
   
That's it! You are done.
