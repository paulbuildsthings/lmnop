FROM python:3.9.10-slim-bullseye@sha256:86b3b6af2b6254fe44de9f5c8e6e08248cdef19f3060ee5cf131ef629c375830 AS base

# install updates and dependencies
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get -q update && apt-get -y upgrade && \
    apt-get install -y --no-install-recommends tini && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# create the user (do not use yet)
RUN groupadd -g 1000 lmnop && useradd -u 1000 -g 1000 -d /home/lmnop --create-home lmnop
ENV PATH="/home/lmnop/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

FROM base AS builder

# install dependencies
RUN apt-get -q update && apt-get install -y --no-install-recommends git

# now become the lmnop user to set up poetry and the versioning tool
RUN pip3 install poetry dunamai --no-cache-dir && chown lmnop:lmnop /usr/local/src
COPY --chown=1000:100 . /usr/local/src

USER lmnop

# update the version number of our application
WORKDIR /usr/local/src/portal
RUN poetry version $(dunamai from git --dirty)

# move the application to the application directory
WORKDIR /usr/local/src
RUN mv portal /home/lmnop/app

# now install our application
WORKDIR /home/lmnop/app
RUN poetry config virtualenvs.in-project true && \
    poetry config virtualenvs.create true && \
    poetry install --no-dev --no-ansi --no-interaction

FROM base AS final

# install program entrypoints
USER root
COPY --from=builder --chown=0:0 /home/lmnop/app/entrypoints /entrypoints

# copy over the actual application
USER lmnop
WORKDIR /home/lmnop/app
COPY --from=builder --chown=1000:100 /home/lmnop/app/.venv /home/lmnop/app/.venv
COPY --from=builder --chown=1000:100 /home/lmnop/app/pyproject.toml /home/lmnop/app/pyproject.toml
COPY --from=builder --chown=1000:100 /home/lmnop/app/poetry.lock /home/lmnop/app/poetry.lock
COPY --from=builder --chown=1000:100 /home/lmnop/app/src /home/lmnop/app/src

# copy the tests over so that pytest works inside the container during testing
COPY --from=builder --chown=1000:100 /home/lmnop/app/tests /home/lmnop/app/tests

ENTRYPOINT ["/entrypoints/cmd"]
