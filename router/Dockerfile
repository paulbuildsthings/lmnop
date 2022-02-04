FROM debian:bullseye-slim@sha256:4c25ffa6ef572cf0d57da8c634769a08ae94529f7de5be5587ec8ce7b9b50f9c AS base

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get -q update && apt-get -y upgrade \
 && apt-get install -y --no-install-recommends apache2 apache2-utils prometheus-apache-exporter \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

RUN a2dismod autoindex access_compat -f \
 && a2disconf security serve-cgi-bin other-vhosts-access-log -f \
 && a2enmod remoteip headers rewrite deflate status proxy_http \
 && sed -i '/^ErrorLog/d' /etc/apache2/apache2.conf \
 && rm -rf /var/www/html \
 && mkdir -p /var/run/apache2

# copy over the container configuration
COPY /router/conf /

EXPOSE 80/tcp
ENTRYPOINT ["/entrypoint"]
