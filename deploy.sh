#!/bin/bash

set -e

set -a; source .env.local; set +a

# NOTE: docs content (flat / manual / modules + contributors) is NOT generated
# here — it's gitignored build output that persists between deploys. Regenerate
# it only when the source changes, with:
#   npm run generate:flat && npm run generate:manual:all \
#     && npm run generate:modules:all && npm run generate:contributors
#
# Resolve legacy PmWiki #tocN anchors → real heading anchors (idempotent).
python3 scripts/resolve-toc-anchors.py

NODE_OPTIONS=--max-old-space-size=6144 ./node_modules/.bin/astro build

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
