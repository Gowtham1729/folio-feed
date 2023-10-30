# Folio Feed
A web application that can be used to track the news regarding the stocks in a portfolio and their current trend.

This application collects the news regarding the stocks listed in user's portfolio from various sources and 
using a sentiment analysis model, we rate the news as positive, negative or neutral.

## Components
- Web Application
- Data Fetcher
- Data Analyzer

## Tech Stack

- **Backend**: Python, Flask
- **Testing**: Pytest
- **Frontend**: HTML, CSS, JS, Vue.js, Nuxt.js
- **Database**: MongoDB
- **Message Broker**: RabbitMQ
- **Deployment**: Docker, Kubernetes, Helm, Terraform, Google Cloud Platform
- **CI/CD**: Git Actions
- **Monitoring**: Prometheus, Grafana

## Basic Architecture

```mermaid
flowchart LR
A((User)) --> B[Web Application]
B --> D[Messaging Queue] --> C[Data Fetcher] --> N[News API]
C -- Cron Job --> C
E[Data Analyzer] --> S[Sentiment Analysis Model API]
E --> F[(Database)]
B --> F
C --> F
B --> A
```



## High Level Design
```mermaid
graph LR
    user((user))
    dev((dev))
    news_api[News API]
    
    subgraph github
        repo[repo] -- push --> on_push_action[On Push Action]
        repo -- merge --> on_merge_action[On Merge Action]
        on_push_action -- Test --> repo
    end
    
    
    subgraph GCP
        GCR[GCR]
        NLP_AI[NLP API]
        subgraph GKE
            DF["Data Fetcher (Cron Job)"]
            DA[Data Analyzer]
            FE[Vue JS Frontend]
            BE[Flask Backend]
            DB[(Mongo DB)]
            ing[GKE Ingress]
            MQ[RabbitMQ]
            
            DF --> DB
            DF -- every 12 hours --> DF
            DA --> DB
            BE --> DB
            ing -- / --> FE
            ing -- /api --> BE
            BE --> MQ
            MQ --> DA
        
        subgraph metrics 
            statsd[StatsD]
            statsd_exp[StatsD Exporter]
            prometheus[Prometheus]
            grafana[Grafana]
            
            statsd --> statsd_exp
            statsd_exp --> prometheus
            prometheus --> grafana
        end
            
        end
        GKE -- pull image --> GCR
        on_merge_action -- helm deploy --> GKE
        DA -- sentiment analysis --> NLP_AI
        
        DA -- metrics --> statsd
        BE -- metrics -->  statsd
        DF -- metrics -->  statsd
        
        ing -- /dashboard --> grafana
        
    end
    
    dev -- changes --> repo
    on_merge_action -- image build --> GCR
    DF -- NEWS Data --> news_api
    user -- HTTPS Requests--> ing
    ing -- response --> user
    
    TF[Terraform] -- deploy --> GCP
    dev -- infrastructure changes --> TF

```