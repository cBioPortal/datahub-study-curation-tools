## This Docker image is used for the Airflow worker pods.

FROM apache/airflow:2.9.2
USER root

# Install dependencies
RUN curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
         git git-lfs \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Git LFS setup
RUN git lfs install --skip-repo --skip-smudge

# The following commands need to be run as the `airflow` user so the packages
# will be installed in the correct location.
USER airflow

# Python3 dependencies must be built into the Docker image
COPY requirements.txt /
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r /requirements.txt