**Short Introduction**  
This project is an ongoing development of an *agentic RAG (Retrieval-Augmented Generation)* system for analyzing stock assets. It processes queries by forwarding them to *phidata*, utilizes *gdrant* as a vector database for feature storage, and stores raw OHLC data in MongoDB. A FastAPI-based logging service is already set up (along with its own Docker Compose configuration), and the core of the chat system is also functional. Front-end work is currently in progress.

---

# Agentic Asset Recommender

An agentic RAG system for stock asset analysis.

## Table of Contents
- [Agentic Asset Recommender](#agentic-asset-recommender)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Features](#features)
  - [Project Structure](#project-structure)
  - [Prerequisites](#prerequisites)
  - [Setup \& Installation](#setup--installation)
  - [Usage](#usage)
  - [Logging Service](#logging-service)
  - [Current Status](#current-status)
  - [Contributing](#contributing)

---

## Overview
This project aims to provide an automated research and analysis pipeline for stock assets using retrieval-augmented generation (RAG). By sending user queries to *phidata*, the system orchestrates data retrieval, analysis, and conversational insights. Over time, additional modules and improvements (including a front-end interface) will be integrated.

---

## Features
- **RAG Chat System**: Employs a retrieval-augmented approach to answer queries related to stock assets.
- **GDRant Vector Database**: Stores vector embeddings for better data retrieval and semantic search.
- **MongoDB for OHLC Data**: Tracks raw stock data (Open, High, Low, Close) for analysis.
- **FastAPI Logging Service**: Records system logs and events, connected to MongoDB.
- **Dockerized Components**: The logging service comes with its own Docker Compose setup.

---

## Project Structure
A high-level view (actual folder names and structure may vary):

```
project-root/
│
├─ backend/
│   ├─ app
│   └─ requirements.txt
│
├─ logging-service/
│   ├─ Dockerfile
│   ├─ docker-compose.yml
│   ├─ app
│   └─ ...
│
├─ database/
│   ├─ app/
│   │   └─ ...
│   ├─ dockerfile
│   
│   
│
├─ frontend/
│   └─ ...
│
├─ README.md
└─ ...
```

- **chat-core**: Contains the main logic for the chat system and analysis engine.  
- **logging-service**: Implements the FastAPI-based logging system, storing logs in MongoDB.  
- **data-services**: Manages connections to GDRant (for vector embeddings) and MongoDB (for OHLC data).  
- **frontend**: Work in progress for the UI.

---

## Prerequisites
- **Docker** and **Docker Compose** (for the logging service and other containerized parts).
- **Python 3.8+** (for the chat-core and other scripts).
- **MongoDB** (if not using Docker for the logging service or if you want a separate local instance).
- **Qdrant** (vector DB, can be run locally or via Docker).

---

## Setup & Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/artaasd95/agentic-asset-recommender
   cd agentic-asset-recommender
   ```

2. **Set up Python environment** (for the chat-core and additional scripts):
   ```bash
   python -m venv venv
   source venv/bin/activate  # or .\venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   - Create an `.env` file or export variables for the needed variables in each service

---

## Usage
1. **Chat Core**:  
   - Start the chat-related services and workers (details depend on your implementation).  
   - This component will connect to GDRant and MongoDB for data retrieval and storage.

2. **Logging Service**:
   - Refer to [Logging Service](#logging-service) below for startup instructions.

3. **Query Flow**:
   - The user sends a query (through the chat or another interface).
   - The system retrieves relevant data from GDRant or MongoDB.
   - The system processes the data and responds using RAG techniques.

---

## Logging Service
- The logging service is powered by **FastAPI** and uses **MongoDB** to store logs.
- **Docker Compose** is provided in the `logging-service/docker-compose.yml`. 
- To run:
  ```bash
  cd logging-service
  docker-compose up -d
  ```
- This will start the FastAPI logging service and MongoDB (if configured in the compose file).

---

## Current Status
- **Ongoing Development**: Core chat functionality and logging system are in place.
- **Front-End**: A front-end interface is under construction and not yet ready for production.
- **Data Services**: GDRant integration for vector embeddings is functional, while MongoDB is used to store OHLC data.  

---

## Contributing
Contributions are welcome! Please open an issue to discuss proposed changes or to report bugs. Feel free to submit pull requests for review.  

