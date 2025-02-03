## README

## 1. Structure

The project is composed of three main services, orchestrated using Docker Compose:

### Services Overview

```
project_root/
│-- query_translator/    # Natural language to SQL translation service (LLM based)
│-- backend/             # Main backend service
│-- init-db/             # Initializes database of mysql service
│-- docker-compose.yml

other services/
│-- mysql/               # Additional service based on offical docker image
```

- **query_translator**
  - Machine learning service for query translation
  - LLM Model:
    - **sqlcoder-7b-2** when NVIDIA GPU and CUDA are available
    - **t5-small-awesome-text-to-sql** otherwise
  - Exposes port **5000**

- **mysql**
  - MySQL **8.0** database service
  - Exposes port **3306**
  - Uses a **persistent volume** (`mysql_data`) to store data

- **backend**
  - FastAPI application that interacts with `query_translator` and `mysql`
  - Exposes port **8080**
  - Uses environment variables to connect to the database and query translator
  - Provides a **Swagger UI** for API interaction

## 2. Build and Run

To build and start the project, run:

```sh
docker compose up --build
```

- Containers for **query_translator**, **mysql**, and **backend** should start
- No errors should be displayed in the logs

  Run
  `docker ps`
  to show all services running

## 3. Use

### Option A: Swagger UI
Once running, access the FastAPI **Swagger UI** to test the API:
- Open your browser and go to:
  
  ```
  http://localhost:8080/docs
  ```
- Try out the `/db_users/query_sales` endpoint to send questions to the system and get the responses with data from the database
### Option B: CLI
Using curl on command line:
  ```
 curl -X POST "http://localhost:8080/db_users/query_sales" \
     -H "accept: application/json" \
     -H "Content-Type: application/json" \
     -d '{"question": "What is the most bought product on Mondays?"}'

  ```

## 4. To do
- Prompt engineering on _t5-small-awesome-text-to-sql_ model in order to get actually usables SQL queries
- Make docker load the _sqlcoder-7b-2_ model (CUDA needed here) in order to be able to use the best of both models (this one works very well with the current prompt)
- An actual frontend

