FROM ghcr.io/openfaas/of-watchdog:0.9.2@sha256:53930578070cf81faa309294a9215b8b850c313ac51f1b885454e8a74234780e as watchdog
FROM debian:bullseye-slim@sha256:b0d53c872fd640c2af2608ba1e693cfc7dedea30abcd8f584b23d583ec6dadc7 AS base

# install updates and dependencies
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get -q update && apt-get -y upgrade \
 && apt-get install -y --no-install-recommends apache2 apache2-utils \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# then set up the configuration
RUN a2dismod autoindex access_compat -f \
 && a2disconf security serve-cgi-bin other-vhosts-access-log -f \
 && a2enmod remoteip headers rewrite deflate \
 && sed -i '/^ErrorLog/d' /etc/apache2/apache2.conf \
 && rm -rf /var/www/html

# while our configuration does not use this directory it must be present for
# apache to start correctly. in the 000-default.conf file we change around the
# paths because only /tmp is writable in the container.
RUN mkdir -p /var/run/apache2

# copy the watchdog from openfaas
COPY --from=watchdog /fwatchdog /usr/bin/fwatchdog
RUN chmod +x /usr/bin/fwatchdog

FROM base AS builder

RUN apt-get -q update \
 && apt-get install -y --no-install-recommends wget ca-certificates \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# download hugo
ENV HUGO_VERSION="0.89.4"
ENV HUGO_RELEASE_NAME=hugo_${HUGO_VERSION}_Linux-64bit.deb
ENV HUGO_RELEASE_URL=https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/${HUGO_RELEASE_NAME}
RUN wget $HUGO_RELEASE_URL && dpkg -i $HUGO_RELEASE_NAME

# copy everything over to this builder container
COPY . /usr/local/src

# build the hugo site
WORKDIR /usr/local/src/function/site
RUN rm -rf ./public ./resources/_gen && hugo

FROM base AS final

# copy things from the builder and the template that are needed
COPY --chown=0:0 --from=builder /usr/local/src/function/site/public /var/www/html
COPY --chown=0:0 --from=builder /usr/local/src/000-default.conf /etc/apache2/sites-enabled/000-default.conf
COPY --chown=0:0 --from=builder /usr/local/src/entrypoint /entrypoint
RUN chmod +x /entrypoint

# these environment variables are needed for fwatchdog
ENV fprocess="/entrypoint"
ENV mode="http"
ENV upstream_url="http://127.0.0.1:80"
CMD ["fwatchdog"]
