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
