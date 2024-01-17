# Folio Feed: Personalized Portfolio News and Sentiment Dashboard
In today's fast-paced financial markets, keeping track of news affecting your stock portfolio can be a daunting and time-consuming task especially when your portfolio contains many individual stocks, mutual funds and cryptocurrencies. 
Even more challenging is understanding the overall sentiment of the news related to each stock, which can be pivotal in making informed investment decisions. 
Folio Feed addresses this gap by offering a one-stop solution to aggregate, analyze, and visualize news articles for the stocks in your portfolio.

Folio Feed not only aggregates news from multiple, reputable sources but also employs advanced AI sentiment analysis to categorize each article as positive, negative, or neutral. 
Through an easy-to-use dashboard, Folio Feed empowers investors to keep their fingers on the pulse of companies they have invested in, without having to sift through a myriad of news portals and financial reports.

With Folio Feed, stay updated and make smarter investment choices, even on your busiest days.

## Components
- Web Application
- Data Fetcher
- Data Analyzer

## Tech Stack

- **Backend**: Python, Django
- **Testing**: Pytest, Unittest
- **Frontend**: HTML, CSS, JS, Bootstrap
- **Database**: Postgresql
- **Message Broker**: RabbitMQ
- **Deployment**: Docker, Kubernetes (Google Kubernetes Engine), Helm, Terraform, Google Cloud Platform
- **CI/CD**: Git Actions
- **Monitoring**: Google Managed Prometheus, Google Cloud Monitoring

## Basic Architecture

```mermaid
flowchart LR
A((User)) --> B[Web Application]
B --> C[Data Fetcher] --> N[External News API]
C --> D[Messaging Queue]
C -- Cron Job --> C
E[Data Analyzer] --> S[Sentiment Analysis Model API]
D --> E
E --> F[(Database)]
F --> E
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
        NLP_AI[Vertex AI]
        subgraph GKE
            DF["Data Fetcher (Cron Job)"]
            DA[Data Analyzer]
            WA[Django Web application]
            DB[(Postgres)]
            ing[GKE Ingress]
            MQ[RabbitMQ]
            
            DF --> DB
            DF -- every n hours --> DF
            MQ --> DA
            DA --> DB
            WA --> DB
            ing -- / --> WA
            ing -- "/api (RESTful API)" --> WA
        
            prometheus[GKE Managed Prometheus]
            
        end
        GKE -- pull image --> GCR
        on_merge_action -- helm deploy --> GKE
        DA -- sentiment analysis --> NLP_AI
        
        prometheus -- metrics --> monitoring[Google Cloud Monitoring]
        
        
    end
    
    dev -- changes --> repo
    on_merge_action -- image build --> GCR
    DF -- NEWS Data --> news_api
    user -- HTTPS Requests--> ing
    ing -- Response --> user
    
    TF[Terraform] -- deploy --> GCP
    dev -- infrastructure changes --> TF
```

## Screenshots
<img width="1571" alt="image" src="https://github.com/Gowtham1729/folio-feed/assets/25081151/8f9f8f6d-ae4d-4648-8637-4db3dd51d363">

<img width="1571" alt="image" src="https://github.com/Gowtham1729/folio-feed/assets/25081151/54f96af7-6240-480c-b3aa-2ea57b2ae54c">

<img width="1571" alt="image" src="https://github.com/Gowtham1729/folio-feed/assets/25081151/76479ac4-efae-4d3f-9814-deae61f66f24">
