#!/usr/bin/env bash
set -euo pipefail

# Cloud-init user-data for Ubuntu on AWS EC2

cat >/root/install.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
apt-get update
apt-get install -y git
mkdir -p /opt/sky-portal
cd /opt/sky-portal
git clone ${GIT_REPO_URL:-https://example.com/your/repo.git} . || true
bash deploy/ubuntu_install.sh
cp .env.example .env || true
docker compose up -d --build
SH

chmod +x /root/install.sh
/root/install.sh

