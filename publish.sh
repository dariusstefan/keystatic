#!/bin/bash

dir="/var/www/html/opensips.org"

release="$dir/releases/$(date +%Y%m%d%H%M%S)"

mkdir -p "$release"
rsync -a --delete dist/ "$release/"
rm -rf "$dir/current"
ln -sfn "$release" "$dir/current"

nginx -t
systemctl reload nginx
