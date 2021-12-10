FROM ghcr.io/openfaas/of-watchdog:0.9.2@sha256:53930578070cf81faa309294a9215b8b850c313ac51f1b885454e8a74234780e as watchdog
FROM python:3.9.9-slim-bullseye@sha256:d67e4b3e185208a010e0d06dd1f655292dd92c5dd08a64b1c59a0acbd387b1e9 AS base

# Allows you to add additional packages via build-arg
ARG packages

# install updates and dependencies
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get -q update && apt-get -y upgrade \
 && apt-get install -y --no-install-recommends ca-certificates ${packages} \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# create the lmnop user (do not use yet)
RUN useradd -u 1000 -g 100 -d /home/lmnop --create-home lmnop
ENV PATH="/home/lmnop/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# copy the watchdog from openfaas
COPY --from=watchdog /fwatchdog /usr/bin/fwatchdog
RUN chmod +x /usr/bin/fwatchdog

FROM base AS builder

# copy everything over to this builder container
COPY . /usr/local/src

# make sure certain files are there
# the entrypoint file MUST be supplied by the caller
# but the "initialize" and "requirements.txt" files are optional
WORKDIR /usr/local/src/function
RUN touch initialize requirements.txt

FROM base AS final

# copy things from the builder that we needed
COPY --chown=0:0 --from=builder /usr/local/src/function/entrypoint /entrypoint
COPY --chown=0:0 --from=builder /usr/local/src/function/initialize /initialize
COPY --chown=1000:100 --from=builder /usr/local/src/function/requirements.txt /home/lmnop/requirements.txt
COPY --chown=1000:100 --from=builder /usr/local/src/function/function /home/lmnop/function
RUN chmod +x /entrypoint /initialize

# run everything here after as our application user
USER lmnop

# work in the function's directory so relative paths work
WORKDIR /home/lmnop/function

# this is the requirements file that comes from the actual function
RUN pip install --no-cache -r /home/lmnop/requirements.txt

# run any user initialization
RUN /initialize

# these environment variables are needed for fwatchdog
ENV fprocess="/entrypoint"
ENV mode="http"
ENV upstream_url="http://127.0.0.1:5000"
CMD ["fwatchdog"]
