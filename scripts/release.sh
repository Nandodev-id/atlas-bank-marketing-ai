#!/bin/sh
# Install on the approved host at /opt/atlas/release.sh; run under the deployment user.
set -eu
cd /opt/atlas
candidate_tag="$1"
case "$candidate_tag" in *[!a-f0-9]*|'') exit 2;; esac
[ "${#candidate_tag}" -eq 40 ]
# /opt/atlas/api.env must contain ATLAS_API_KEY; create it outside source control.
test -s api.env
docker load -i image.tar
old_image=$(docker inspect --format '{{.Config.Image}}' atlas-api 2>/dev/null || true)
docker rm -f atlas-api 2>/dev/null || true
start_image() {
  docker run -d --name atlas-api --restart unless-stopped --env-file api.env \
    --read-only --tmpfs /tmp --cap-drop ALL --security-opt no-new-privileges \
    --memory 2g --cpus 2 -v atlas-audit:/app/runtime -p 127.0.0.1:8000:8000 "$1"
}
if ! start_image "atlas-bank-marketing:$candidate_tag"; then
  docker rm -f atlas-api 2>/dev/null || true
  if [ -n "$old_image" ]; then start_image "$old_image"; fi
  exit 1
fi
attempt=0
while [ "$attempt" -lt 20 ]; do
  if curl --fail --silent http://127.0.0.1:8000/health >/dev/null; then exit 0; fi
  sleep 2
  attempt=$((attempt+1))
done
docker rm -f atlas-api
if [ -n "$old_image" ]; then start_image "$old_image"; fi
exit 1
