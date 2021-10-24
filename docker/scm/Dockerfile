# we need to pull the faas-cli out of this container
FROM ghcr.io/openfaas/faas-cli:0.13.14@sha256:8cc2473aff2a3fa0c192b195248d985a4a7c447b7889d74d435bb549e711c76f AS faas

# but our actual container runs inside this python container
FROM python:3.9.7-slim-bullseye@sha256:c4dd2f7cb7f0b0d6c056cdd7f3c4ccf647b5e0cc712abb43918fc53997239609 AS base

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
 && rm -rf /var/www/html

FROM base AS builder

# calculate what our version is
RUN pip3 install poetry dunamai --no-cache-dir
COPY . /usr/local/src

# update the version number of our application and build a wheel
WORKDIR /usr/local/src
RUN poetry version $(dunamai from git --dirty) && \
    poetry build

# now install our application
USER lmnop
RUN pip install /usr/local/src/dist/*.whl

FROM base AS final

# copy the faas command line tool
COPY --from=faas /usr/bin/faas-cli /usr/local/bin/faas

# copy the virtual environment that we just built
COPY --from=builder /home/lmnop/.local /home/lmnop/.local

# copy our faas templates
COPY /templates /home/lmnop/templates

# prepare a location to save things that get pushed
RUN mkdir -p /srv/data/git && \
    chown lmnop:lmnop /srv/data/git && \
    git config --system init.defaultBranch main

# copy over the container configuration
COPY /docker/scm/conf /

EXPOSE 80/tcp
VOLUME ["/srv/data"]
ENTRYPOINT ["/entrypoint"]
