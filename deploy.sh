#!/bin/bash

set -e

set -a; source .env.local; set +a

NODE_OPTIONS=--max-old-space-size=4096 ./node_modules/.bin/astro build

./node_modules/.bin/pagefind --site dist/client

RELEASE=$(date +%Y%m%d%H%M%S)

rsync -a --delete dist/client/ opensips-web:/var/www/html/opensips.org/releases/$RELEASE/
rsync -a --delete dist/server/ opensips-web:/opt/opensips-astro/server/

ssh opensips-web "
  ln -sfn /var/www/html/opensips.org/releases/$RELEASE /var/www/html/opensips.org/current &&
  ln -sfn /var/www/html/opensips.org/src/node_modules /opt/opensips-astro/server/node_modules &&
  systemctl restart opensips-astro &&
  nginx -t && systemctl reload nginx
"
