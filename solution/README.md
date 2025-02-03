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

## 2. Installation

### Enabling NVIDIA GPU support

This is disabled by default and can be enabled by doin these two steps:
1. Uncommenting in file docker-compose.yml:

```
#runtime: nvidia  # Use the NVIDIA runtime
    #environment:
    #  - NVIDIA_VISIBLE_DEVICES=all  # This allows the container to use all available GPUs  
```

2. Comment the dependency
```
torch
```
in sql_query/requirements.txt and uncomment
```
#torch @ https://download.pytorch.org/whl/cu126/torch-2.6.0%2Bcu126-cp312-cp312-manylinux_2_28_x86_64.whl#sha256=6bc5b9126daa3ac1e4d920b731da9f9503ff1f56204796de124e080f5cc3570e

```
### Build and run

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

## 4. Known issues & to do
- Prompt engineering on _t5-small-awesome-text-to-sql_ model in order to get actually usables SQL queries
- Make docker load the _sqlcoder-7b-2_ model (CUDA needed here) in order to be able to use the best of both models (this one works very well with the current prompt)

  **UPDATE** Loading of  _sqlcoder-7b-2_ is actually working but is terribly slow the first time since it has to download 15 GB (it takes several minutes). On second start it just loads the model relatively quick

- An actual frontend

