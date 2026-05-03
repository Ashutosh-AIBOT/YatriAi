FROM ubuntu:22.04

# Prevent interactive prompts during apt
ENV DEBIAN_FRONTEND=noninteractive

# 1. Install core system dependencies
RUN apt-get update && apt-get install -y \
    openjdk-21-jdk \
    python3.10 \
    python3.10-venv \
    python3-pip \
    curl \
    wget \
    redis-server \
    postgresql \
    postgresql-contrib \
    maven \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Node.js 20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# 3. Install Kafka (KRaft mode)
RUN wget https://archive.apache.org/dist/kafka/3.6.1/kafka_2.13-3.6.1.tgz \
    && tar -xzf kafka_2.13-3.6.1.tgz \
    && mv kafka_2.13-3.6.1 /opt/kafka \
    && rm kafka_2.13-3.6.1.tgz \
    && KAFKA_CLUSTER_ID="$(/opt/kafka/bin/kafka-storage.sh random-uuid)" \
    && /opt/kafka/bin/kafka-storage.sh format -t $KAFKA_CLUSTER_ID -c /opt/kafka/config/kraft/server.properties

# 4. Setup Postgres (Create role and database)
USER postgres
RUN /etc/init.d/postgresql start \
    && psql --command "CREATE USER yatri WITH SUPERUSER PASSWORD 'yatri';" \
    && createdb -O yatri yatri_db
USER root

# 5. Copy the entire repository into the image
WORKDIR /app
COPY . .

# 6. Build Spring Boot Gateway
WORKDIR /app/gateway
RUN mvn clean package -DskipTests

# 7. Setup Python Orchestrator
WORKDIR /app/orchestrator
RUN python3 -m venv .venv \
    && .venv/bin/pip install -r requirements.txt

# 8. Setup Node Notification Service
WORKDIR /app/notification
RUN npm install

# 9. Setup Next.js Frontend
WORKDIR /app/frontend
RUN npm install && npm run build

# 10. Configure Entrypoint
WORKDIR /app
RUN chmod +x hf_entrypoint.sh

# Hugging Face Spaces exposes port 7860 by default
EXPOSE 7860

CMD ["./hf_entrypoint.sh"]
