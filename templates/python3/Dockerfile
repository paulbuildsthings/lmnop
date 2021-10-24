FROM ghcr.io/openfaas/of-watchdog:0.8.4 as watchdog
FROM python:3.9-slim-buster

# Allows you to add additional packages via build-arg
ARG packages

# install updates and dependencies
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get -q update && apt-get -y upgrade && \
    apt-get install -q -y --no-install-recommends ca-certificates ${packages} && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# create the app user (do not use yet)
RUN useradd -u 1000 -g 100 -d /home/app --create-home app
ENV PATH="/home/app/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# copy the watchdog from openfaas
COPY --from=watchdog /fwatchdog /usr/bin/fwatchdog
RUN chmod +x /usr/bin/fwatchdog

# run everything here after as our application user
USER app

# this is the requirements file that comes from the actual function
COPY --chown=1000:100 function/requirements.txt /home/app/requirements.txt
RUN pip install --no-cache -r /home/app/requirements.txt

# copy the entrypoint
USER root

# copy the entrypoint function
COPY function/entrypoint /entrypoint
RUN chmod +x /entrypoint

# copy everything else
USER app

# then copy the actual function itself
COPY --chown=1000:100 function/function /home/app/function

# work in the function's directory so relative paths work
WORKDIR /home/app/function

# these environment variables are needed for fwatchdog
ENV fprocess="/entrypoint"
ENV mode="http"
ENV upstream_url="http://127.0.0.1:8000"
CMD ["fwatchdog"]
