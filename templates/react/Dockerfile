FROM ghcr.io/openfaas/of-watchdog:0.9.2@sha256:53930578070cf81faa309294a9215b8b850c313ac51f1b885454e8a74234780e as watchdog
FROM debian:bullseye-slim@sha256:b0d53c872fd640c2af2608ba1e693cfc7dedea30abcd8f584b23d583ec6dadc7 AS base

# install updates and dependencies
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get -q update && apt-get -y upgrade \
 && apt-get install -y --no-install-recommends lighttpd \
 && apt-get clean && rm -rf /var/lib/apt/lists/* \
 && rm -rf /etc/lighttpd /var/www/html

# copy the watchdog from openfaas
COPY --from=watchdog /fwatchdog /usr/bin/fwatchdog
RUN chmod +x /usr/bin/fwatchdog

FROM node:lts-bullseye-slim@sha256:b0a27877c45f2d31d54a6197bcca1bbd1e307a557b1f655c8fbe80170567ca3e AS builder

# install updates and dependencies
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get -q update && apt-get -y upgrade \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# copy over the dependency files
COPY function/package.json /usr/local/src
COPY function/package-lock.json /usr/local/src

# install dependencies
WORKDIR /usr/local/src
RUN npm install

# copy everything over to this builder container
# the user's stuff ends up in /usr/local/src/function
COPY . /usr/local/src
WORKDIR /usr/local/src/function
RUN npm run build

FROM base AS final

# copy things from the builder and the template that are needed
COPY --chown=0:0 --from=builder /usr/local/src/function/build /var/www/html
COPY --chown=0:0 --from=builder /usr/local/src/lighttpd.conf /etc/lighttpd/lighttpd.conf
COPY --chown=0:0 --from=builder /usr/local/src/entrypoint /entrypoint
RUN chmod +x /entrypoint

# these environment variables are needed for fwatchdog
ENV fprocess="/entrypoint"
ENV mode="http"
ENV upstream_url="http://127.0.0.1:80"
CMD ["fwatchdog"]
