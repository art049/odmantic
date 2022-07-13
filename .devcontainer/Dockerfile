FROM fkrull/multi-python

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    git-lfs \
    netcat \
  && apt-get clean autoclean \
  && apt-get autoremove -y \
  && rm -rf /var/lib/apt/lists/* \
  && rm -f /var/cache/apt/archives/*.deb

# Install task
RUN curl -sL https://taskfile.dev/install.sh | sh
ENV PATH /root/.bin/:/root/.local/bin/:${PATH}

# Install devtools
RUN python3.8 -m pip install flit tox pre-commit

# Allow flit install as root
ENV FLIT_ROOT_INSTALL 1
