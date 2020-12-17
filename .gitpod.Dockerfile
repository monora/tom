FROM gitpod/workspace-full

# Install custom tools, runtimes, etc.
# For example "bastet", a command-line tetris clone:
# RUN brew install bastet
#
# More information: https://www.gitpod.io/docs/config-docker/

USER gitpod
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
RUN ln -s $HOME/.poetry/env $HOME/.bashrc.d/99-poetry
# Because of https://github.com/gitpod-io/gitpod/issues/479 
RUN echo "export PIP_USER=no" > ~/.bashrc.d/99-pip-env


