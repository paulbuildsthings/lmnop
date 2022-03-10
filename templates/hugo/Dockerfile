FROM ghcr.io/openfaas/of-watchdog:0.9.2@sha256:53930578070cf81faa309294a9215b8b850c313ac51f1b885454e8a74234780e as watchdog
FROM debian:bullseye-slim@sha256:d5cd7e54530a8523168473a2dcc30215f2c863bfa71e09f77f58a085c419155b AS base

# install updates and dependencies
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get -q update && apt-get -y upgrade \
 && apt-get install -y --no-install-recommends lighttpd \
 && apt-get clean && rm -rf /var/lib/apt/lists/* \
 && rm -rf /etc/lighttpd /var/www/html

# copy the watchdog from openfaas
COPY --from=watchdog /fwatchdog /usr/bin/fwatchdog
RUN chmod +x /usr/bin/fwatchdog

FROM base AS builder

RUN apt-get -q update \
 && apt-get install -y --no-install-recommends wget ca-certificates \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# download hugo
ENV HUGO_VERSION="0.92.1"
ENV HUGO_RELEASE_NAME=hugo_${HUGO_VERSION}_Linux-64bit.deb
ENV HUGO_RELEASE_URL=https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/${HUGO_RELEASE_NAME}
RUN wget $HUGO_RELEASE_URL && dpkg -i $HUGO_RELEASE_NAME

# copy everything over to this builder container
# the user's stuff ends up in /usr/local/src/function
COPY . /usr/local/src

# build the hugo site
WORKDIR /usr/local/src/function/site
RUN rm -rf ./public ./resources/_gen && hugo

FROM base AS final

# copy things from the builder and the template that are needed
COPY --chown=0:0 --from=builder /usr/local/src/function/site/public /var/www/html
COPY --chown=0:0 --from=builder /usr/local/src/lighttpd.conf /etc/lighttpd/lighttpd.conf
COPY --chown=0:0 --from=builder /usr/local/src/entrypoint /entrypoint
RUN chmod +x /entrypoint

# these environment variables are needed for fwatchdog
ENV fprocess="/entrypoint"
ENV mode="http"
ENV upstream_url="http://127.0.0.1:80"
CMD ["fwatchdog"]
