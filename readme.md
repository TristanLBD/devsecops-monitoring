# Installer Docker + outils

```bash
sudo apt update
sudo apt install -y docker.io docker-compose git curl
```

## Activer Docker :

```bash
sudo systemctl start docker
sudo systemctl enable docker
```

## Ajouter le user :

```bash
sudo usermod -aG docker $USER
```

# Fix problème Podman

```bash
unset DOCKER_HOST
```

Verif : docker context use default

# Création projet

```bash
mkdir devsecops-monitoring
cd devsecops-monitoring
git init
```

# docker-compose.yml

```bash
nano docker-compose.yml
```

## y mettre

```bash
services:

  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    restart: unless-stopped
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    ports:
      - "9090:9090"
    networks:
      - monitoring

  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    restart: unless-stopped
    ports:
      - "9100:9100"
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    networks:
      - monitoring

  db:
    image: mysql:5.7
    container_name: mysql
    restart: unless-stopped
    environment:
      MYSQL_DATABASE: wordpress
      MYSQL_USER: wpuser
      MYSQL_PASSWORD: wppassword
      MYSQL_ROOT_PASSWORD: rootpassword
    volumes:
      - mysql_data:/var/lib/mysql
    networks:
      - monitoring

  wordpress:
    image: wordpress:latest
    container_name: wordpress
    restart: unless-stopped
    depends_on:
      - db
    ports:
      - "8080:80"
    environment:
      WORDPRESS_DB_HOST: db:3306
      WORDPRESS_DB_USER: wpuser
      WORDPRESS_DB_PASSWORD: wppassword
      WORDPRESS_DB_NAME: wordpress
    networks:
      - monitoring

networks:
  monitoring:
    driver: bridge

volumes:
  prometheus_data:
  mysql_data:
```

# Prometheus config

```bash
mkdir monitoring
nano monitoring/prometheus.yml
```

## Contenu :

```bash
global:
  scrape_interval: 15s

scrape_configs:

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
```

# Lancer la stack

```bash
sudo docker compose up -d
```

## verifier

```bash
docker ps
```

# Accès services

## Penser a mettre les bridge de redirection de port de ma machine vers la VM

- WordPress : http://localhost:8080/
- Grafana : http://localhost:3000/
- Prometheus : http://localhost:9090/

# Ce que fait la stack

- Monitoring :
    - Prometheus collecte les métriques
    - Grafana affiche dashboards
    - Node Exporter donne CPU/RAM/disque
- App :
    - WordPress site web
    - MySQL base de données

# Installer trivy

```bash
sudo apt install trivy -y
```

# Scan du projet

```bash
trivy fs .
```

# Scan image WordPress

```bash
trivy image wordpress:latest
```

# Générer un rapport

```bash
trivy image -f json -o trivy-report.json wordpress:latest
```

## Puis l'ajouter au repo

```bash
git add trivy-report.json
git commit -m "Add Trivy vulnerability report"
git push
```

# Script Python (recap des failles)

```bash
mkdir scripts
nano scripts/analyze_trivy.py
```

## Code du ficheir python :

```python
import json

file = "trivy-report.json"

with open(file) as f:
    data = json.load(f)

total = 0
critical = 0
high = 0

for result in data.get("Results", []):
    for v in result.get("Vulnerabilities", []):
        total += 1
        if v.get("Severity") == "CRITICAL":
            critical += 1
        if v.get("Severity") == "HIGH":
            high += 1

print("=== TRIVY REPORT ===")
print(f"Total vulnerabilities: {total}")
print(f"Critical: {critical}")
print(f"High: {high}")
```

## Lancer le code python

```bash
python3 scripts/analyze_trivy.py
```

# Scan Python (Bandit)

## Installer bandit

```bash
pip install bandit
```

## Scan

```bash
bandit -r scripts/
```

## Rapport

```bash
bandit -r scripts/ -f json -o bandit-report.json
```

# CI GitHub Actions

## Cette pipeline va :

- vérifier automatiquement la sécurité du code à chaque push sur main
- détecter des vulnérabilités avec Trivy
- Analyser et résumer le rapport avec le script python
- sauvegarder le résultat pour consultation
- (Dans l'onglet action du repo, il doit y avoir la pipeline, le scan et le fichier généré)

```bash
mkdir -p .github/workflows
nano .github/workflows/security.yml
```

```bash
name: Security Pipeline

on:
  push:
    branches: [ "main" ]

jobs:

  scan:

    runs-on: ubuntu-latest

    steps:

      - name: Checkout code
        uses: actions/checkout@v4

      # ---------------- TRIVY ----------------
      - name: Install Trivy
        run: |
          sudo apt-get update
          sudo apt-get install -y wget
          wget https://github.com/aquasecurity/trivy/releases/latest/download/trivy_0.50.0_Linux-64bit.deb
          sudo dpkg -i trivy_0.50.0_Linux-64bit.deb

      - name: Scan filesystem
        run: trivy fs . > trivy-report.txt

      # ---------------- PYTHON SCRIPT ----------------
      - name: Run Python analyzer
        run: |
          sudo apt-get install -y python3
          python3 scripts/analyze_trivy.py

      # ---------------- UPLOAD REPORT ----------------
      - name: Upload report
        uses: actions/upload-artifact@v4
        with:
          name: security-report
          path: trivy-report.txt
```

```bash
git add .
git commit -m "Add GitHub Actions security pipeline"
git push
```
