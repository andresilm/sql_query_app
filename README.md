## Installation

## 1. Structure

The project is composed of three main services, orchestrated using Docker Compose:

### Services Overview:

```
project_root/
│-- query_translator/    # Natural language to SQL translation service (optional:GPU)
│-- backend/             # Main backend service
│-- docker-compose.yml   
```

### Docker Compose Structure:

- **query_translator**
  - Machine learning service for query translation
  - Uses **NVIDIA GPU** for acceleration
  - Exposes port **5000**

- **mysql**
  - MySQL **8.0** database service
  - Exposes port **3306**
  - Uses a **persistent volume** (`mysql_data`) to store data

- **backend**
  - FastAPI application that interacts with `query_translator` and `mysql`
  - Exposes port **5001**
  - Uses environment variables to connect to the database and query translator
  - Provides a **Swagger UI** for API interaction

## 2. Build and Run

To build and start the project, run:

```sh
docker compose up --build
```

### Expected Output on Success:
- Containers for **query_translator**, **mysql**, and **backend** should start
- No errors should be displayed in the logs

  Run
  `docker ps`
  to show all services running

## 3. Use

Once running, access the FastAPI **Swagger UI** to test the API:

- Open your browser and go to:
  
  ```
  http://localhost:5001/docs
  ```

- Try out the `/ask` endpoint to send questions to the system and get the responses with data from the database


