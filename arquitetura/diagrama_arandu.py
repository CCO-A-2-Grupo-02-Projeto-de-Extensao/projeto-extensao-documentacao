from diagrams import Cluster, Diagram, Edge

# AWS General
from diagrams.aws.general import User
from diagrams.aws.general import Client

# Network
from diagrams.aws.network import InternetGateway
from diagrams.aws.network import ELB
from diagrams.aws.network import NATGateway
from diagrams.aws.database import RDS
from diagrams.aws.storage import S3

from diagrams.programming.language import Java

# Storage
from diagrams.aws.storage import EFS

# Linguagem de Programação
from diagrams.programming.language import Nodejs
from diagrams.programming.framework import React
from diagrams.programming.framework import Spring

from diagrams.onprem.network import Nginx

node_attr = {
    "fixedsize": "true",
    "height": "1.0",
    "width": "1.0"
}

with Diagram("Arquitetura Arandu", show=False,
             graph_attr={
                 "splines": "ortho",
                 "nodesep": "1.8",
                 "ranksep": "1.5",
                 # Title layout: top, centered and larger
                 "labelloc": "t",
                 "labeljust": "c",
                 "fontsize": "36",
                 "fontname": "Arial",
                 # explicit label to ensure the title is rendered as graph label
                 "label": "Arquitetura Arandu",
             },
             node_attr=node_attr):
    user = User("Usuário")
    client = Client("Cliente")

    with Cluster("AWS Cloud", graph_attr={"bgcolor": "#f0f0f0", "style": "solid", "color": "black"}):

        S3_bucket = S3("S3 Documentos")

        with Cluster("Arquitetura Medalhão", graph_attr={"bgcolor": "#fff8e1", "style": "solid", "color": "#B8860B"}):
            s3_bronze = S3("S3 Bronze")
            s3_silver = S3("S3 Silver")
            s3_gold = S3("S3 Gold")

        with Cluster("VPC 10.0.0.0/16", graph_attr={"bgcolor": "#e7ffe65a", "style": "bold", "color": "green"}):
            internet_gateway = InternetGateway("Internet Gateway")
            load_balancer = ELB("Load Balancer")
            efs = EFS("AWS EFS")   # recurso compartilhado entre as AZs

            with Cluster("us-east-1b", graph_attr={"bgcolor": "#cfe2f3", "style": "dashed", "color": "green"}):
                with Cluster("Public Subnet 10.0.2.0/24", graph_attr={"bgcolor": "#DDFFD7", "style": "solid", "color": "darkgreen"}):
                    nat_gateway_1b = NATGateway("NAT Gateway")
                    with Cluster("EC2 front_end_2", graph_attr={"bgcolor": "#fce5cd", "style": "solid", "color": "orange"}):
                        node_1b = Nodejs("Node.js")
                        react_1b = React("React")
                        nginx_1b = Nginx("Nginx")

            with Cluster("us-east-1a", graph_attr={"bgcolor": "#cfe2f3", "style": "dashed", "color": "blue"}):
                with Cluster("Public Subnet 10.0.1.0/24", graph_attr={"bgcolor": "#DDFFD7", "style": "solid", "color": "darkgreen"}):
                    nat_gateway_1a = NATGateway("NAT Gateway")
                    with Cluster("EC2 front_end_1", graph_attr={"bgcolor": "#fce5cd", "style": "solid", "color": "orange"}):
                        node_1a = Nodejs("Node.js")
                        react_1a = React("React")
                        nginx_1a = Nginx("Nginx")
                with Cluster("Private Subnet 10.0.3.0/24", graph_attr={"bgcolor": "#1180FF2B", "style": "solid", "color": "darkgreen"}):
                    with Cluster("EC2 Backend", graph_attr={"bgcolor": "#fce5cd", "style": "solid", "color": "orange"}):
                        springboot_backend = Spring("Spring Boot")
                        java_backend = Java("Java Backend")
                with Cluster("Private Subnet 10.0.4.0/24", graph_attr={"bgcolor": "#77B7FF2B", "style": "solid", "color": "darkgreen"}):
                    rds = RDS("AWS RDS")

    # =========================================================
    #  ESTILOS DE ARESTA (definidos uma vez, reaproveitados)
    # =========================================================
    INVIS   = {"style": "invis"}                       # apenas posicionamento
    LB      = {"color": "blue",    "style": "dashed"}  # distribuição do Load Balancer
    STORAGE = {"color": "#2E7D32", "style": "dashed"}  # acesso a EFS / S3

    # ---- Alinhamento interno dos nós (invisível) ----
    nat_gateway_1a >> Edge(**INVIS) >> node_1a >> Edge(**INVIS) >> react_1a >> Edge(**INVIS) >> nginx_1a
    nat_gateway_1b >> Edge(**INVIS) >> node_1b >> Edge(**INVIS) >> react_1b >> Edge(**INVIS) >> nginx_1b
    springboot_backend >> Edge(**INVIS) >> java_backend

    # ---- Entrada: usuário -> Load Balancer -> frontends ----
    user >> client >> internet_gateway >> load_balancer
    load_balancer >> Edge(**LB) >> node_1a
    load_balancer >> Edge(**LB) >> node_1b

    # ---- Frontend -> Backend ----
    nginx_1a >> springboot_backend
    nginx_1b >> springboot_backend

    # ---- Backend -> dados ----
    java_backend >> rds
    java_backend >> Edge(**STORAGE) >> S3_bucket
    rds          >> Edge(**STORAGE) >> S3_bucket
    s3_bronze >> Edge(**STORAGE) >> s3_silver >> Edge(**STORAGE) >> s3_gold
    java_backend >> Edge(**STORAGE) >> [s3_bronze, s3_silver, s3_gold]

    # ---- Storage compartilhado (EFS) ----
    nginx_1a >> Edge(**STORAGE) >> efs
    nginx_1b >> Edge(**STORAGE) >> efs
    