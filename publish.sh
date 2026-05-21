#!/bin/bash

set -e

dir="/var/www/html/opensips.org"
server_dir="/opt/opensips-astro"

# Load env so PUBLIC_ vars are available at build time (baked into the JS bundle)
set -a; source /etc/opensips-keystatic.env; set +a

./node_modules/.bin/astro build

release="$dir/releases/$(date +%Y%m%d%H%M%S)"

mkdir -p "$release"
rsync -a --delete dist/client/ "$release/"

mkdir -p "$server_dir/server" "$server_dir/client"
rsync -a --delete dist/server/ "$server_dir/server/"
ln -sfn /var/www/html/opensips.org/src/node_modules "$server_dir/server/node_modules"

rm -rf "$dir/current"
ln -sfn "$release" "$dir/current"

systemctl restart opensips-astro

nginx -t
systemctl reload nginx
