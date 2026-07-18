# AI-Driven Cloud Cost & Carbon Optimization Platform

An intelligent Cloud FinOps and sustainable resource optimization platform designed to analyze cloud infrastructure usage, identify resource wastage, predict future resource requirements, and provide cost and carbon optimization recommendations.

## Project Overview

Modern cloud environments often suffer from resource overprovisioning, idle infrastructure, unused storage, and inefficient workload scheduling. These problems increase operational costs and contribute to unnecessary energy consumption and carbon emissions.

This project aims to develop an AI-driven platform that integrates cloud computing, DevOps, FinOps, and machine learning techniques to monitor cloud resources and provide intelligent optimization recommendations.

## Key Features

- AWS cloud resource discovery
- EC2 utilization monitoring
- CloudWatch metrics collection
- AWS cost analysis
- Idle resource detection
- Overprovisioned resource detection
- Cloud cost forecasting
- AI-based resource usage prediction
- EC2 rightsizing recommendations
- Kubernetes resource optimization
- Carbon emission estimation
- Cost and carbon comparison
- Automated optimization recommendations
- Monitoring dashboards
- CI/CD automation
- Infrastructure as Code

## Technology Stack

### Backend
- Python
- FastAPI
- SQLAlchemy
- PostgreSQL

### Frontend
- React
- JavaScript

### Cloud
- AWS
- EC2
- CloudWatch
- Cost Explorer
- S3

### DevOps
- Git
- GitHub
- GitHub Actions
- Docker
- Docker Compose
- Kubernetes
- Helm
- Terraform

### AI / Machine Learning
- Python
- Scikit-learn
- Time-series forecasting

### Monitoring
- Prometheus
- Grafana

## Current Architecture

User
  |
React Dashboard
  |
FastAPI Backend
  |
  +-- AWS Integration
  |     +-- EC2
  |     +-- CloudWatch
  |     +-- Cost Explorer
  |
  +-- Optimization Engine
  |
  +-- AI Prediction Engine
  |
  +-- Carbon Estimation Engine
  |
PostgreSQL Database

The application and supporting services will be containerized using Docker and deployed using Kubernetes.

## Current Development Status

- [x] Development environment configured
- [x] Git repository initialized
- [x] GitHub repository configured
- [x] FastAPI backend initialized
- [x] PostgreSQL configured using Docker
- [x] FastAPI connected to PostgreSQL
- [ ] GitHub Actions CI pipeline
- [ ] AWS integration
- [ ] CloudWatch metrics collection
- [ ] AWS cost analysis
- [ ] Optimization engine
- [ ] Carbon estimation engine
- [ ] AI prediction engine
- [ ] React dashboard
- [ ] Dockerize backend
- [ ] Kubernetes deployment
- [ ] Terraform infrastructure
- [ ] Prometheus and Grafana monitoring

## Research Objective

The research component of this project investigates whether predictive resource optimization can reduce cloud infrastructure costs and estimated carbon emissions while maintaining acceptable application performance.

The platform will compare resource utilization, cloud cost, and estimated carbon impact before and after optimization recommendations.

## Research Question

Can AI-driven predictive resource optimization reduce cloud infrastructure costs and estimated carbon emissions without negatively affecting application performance?

## Project Type

MCA Minor Project and Research Project

## Author

Gorachand Pradhan