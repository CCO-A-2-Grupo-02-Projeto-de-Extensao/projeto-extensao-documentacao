RDS_INSTANCE_ID="rds-arandu-db"
RDS_DB_NAME="bdClubeDesbravadores"
RDS_USERNAME="admin"
# Segredos gerados a cada provisionamento — nunca ficam versionados. Para reaproveitar
# uma stack já existente, exporte a variável antes de rodar: RDS_PASSWORD=... ./infra_arandu.sh
RDS_PASSWORD="${RDS_PASSWORD:-$(openssl rand -hex 16)}"
JWT_SECRET="${JWT_SECRET:-$(openssl rand -hex 32)}"
RDS_CLASS="db.t3.micro"
