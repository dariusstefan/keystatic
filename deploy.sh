#!/bin/bash

set -e

set -a; source .env.local; set +a

# NOTE: docs content (flat / manual / modules + contributors) is NOT generated
# here — it's gitignored build output that persists between deploys. Regenerate
# it only when the source changes, with:
#   npm run generate:flat && npm run generate:manual:all \
#     && npm run generate:modules:all && npm run generate:contributors
#
# Anchor links (#tocN and changed #ids, same- and cross-page) are now resolved
# statically by the converters against src/data/{module,manual}-anchors.json, so
# no build-time link-resolution pass is needed.

# Avoid stale prerender chunks from a previous failed/partial build, and clear
# Astro's content-layer store (node_modules/.astro) so that converter/plugin
# changes that don't alter the source .md still take effect (otherwise the
# cached render is reused and e.g. anchor-rule changes silently no-op).
rm -rf dist .astro node_modules/.astro node_modules/.vite

NODE_OPTIONS=--max-old-space-size=8192 ./node_modules/.bin/astro build

./node_modules/.bin/pagefind --site dist/client

RELEASE=$(date +%Y%m%d%H%M%S)

rsync -az --delete -e "ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=10" dist/client/ opensips-web:/var/www/html/opensips.org/releases/$RELEASE/
rsync -az --delete -e "ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=10" dist/server/ opensips-web:/opt/opensips-astro/server/

ssh opensips-web "
  ln -sfn /var/www/html/opensips.org/releases/$RELEASE /var/www/html/opensips.org/current &&
  ln -sfn /var/www/html/opensips.org/src/node_modules /opt/opensips-astro/server/node_modules &&
  systemctl restart opensips-astro &&
  nginx -t && systemctl reload nginx &&
  ls -1dt /var/www/html/opensips.org/releases/*/ | tail -n +3 | xargs rm -rf
"
