# we need to pull the faas-cli out of this container
FROM ghcr.io/openfaas/faas-cli:0.14.2@sha256:cd71b6e0c7464131643b92ae0a273f30ed8454a35e70a57720eb3e40aea58aee AS faas

# but our actual container runs inside this python container
FROM python:3.9.10-slim-bullseye@sha256:86b3b6af2b6254fe44de9f5c8e6e08248cdef19f3060ee5cf131ef629c375830 AS base

# create the user (do not use yet)
RUN groupadd -g 1000 lmnop && useradd -u 1000 -g 1000 -d /home/lmnop --create-home lmnop
ENV PATH="/home/lmnop/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# install common software for all build stages
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get -q update && apt-get -y upgrade && \
    apt-get install -y --no-install-recommends git apache2 apache2-utils libaprutil1-dbd-pgsql prometheus-apache-exporter docker.io libcgi-pm-perl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# then set up the configuration
RUN a2dismod autoindex access_compat -f \
 && a2disconf security serve-cgi-bin other-vhosts-access-log -f \
 && a2enmod remoteip headers rewrite deflate status \
 && a2enmod env cgi alias \
 && a2enmod proxy_http \
 && a2enmod dbd authn_dbd socache_shmcb authn_socache \
 && sed -i '/^ErrorLog/d' /etc/apache2/apache2.conf \
 && rm -rf /var/www/html \
 && mkdir -p /var/run/apache2

FROM base AS builder

# calculate what our version is
RUN pip3 install poetry dunamai --no-cache-dir && chown lmnop:lmnop /usr/local/src
COPY --chown=1000:100 . /usr/local/src

USER lmnop

# update the version number of our application and build a wheel
WORKDIR /usr/local/src/builder
RUN poetry version $(dunamai from git --dirty) && poetry build

# now install our application
RUN pip install /usr/local/src/builder/dist/*.whl

FROM base AS final

# prepare a location to save things that get pushed
RUN mkdir -p /srv/data/git && \
    chown lmnop:lmnop /srv/data/git && \
    git config --system init.defaultBranch main

# copy the faas command line tool
COPY --from=faas /usr/bin/faas-cli /usr/local/bin/faas

# copy the virtual environment that we just built
COPY --from=builder /home/lmnop/.local /home/lmnop/.local

# copy our faas templates
COPY /templates /home/lmnop/templates

# copy over the container configuration
COPY /builder/conf /

EXPOSE 80/tcp
VOLUME ["/srv/data"]
ENTRYPOINT ["/entrypoint"]
