# Amazon Books Data Pipeline 
-----------


## Create a virtual environment and activate it (optional)
```bash
conda env create -f environment.yml
conda activate amazon_books_etl
```


## Base Airflow documentation guide

https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html


# Setup Instructions

This guide will walk you through setting up and configuring pgAdmin, adding a new server, and creating a new database.

## Prerequisites

- Docker installed on your system.
- `dpage/pgadmin4` container running in Docker.

## Steps

### 1. Access pgAdmin

Open your web browser and go to [localhost:5050](http://localhost:5050). You should see the pgAdmin login screen.

### 2. Add a New Server

Once logged into pgAdmin, follow these steps to add a new server:

1. Click on **Add New Server**.
2. In the **General** tab, choose a name for your server (e.g., `Postgres Server`).

### 3. Configure Connection Settings

1. Navigate to the **Connection** tab.
2. Enter the **Username** and **Password** of your PostgreSQL server.

   - If you haven't set a custom username/password, the default PostgreSQL username is `postgres`, and you can set the password via environment variables when running the container.

### 4. Get the Hostname

To retrieve the host address of your PostgreSQL server running in Docker:

1. Open a terminal and run:

```bash
docker container ls
```

2. Find the container ID for the `dpage/pgadmin4` container from the list.

3. Run the following command, replacing `CONTAINER_ID` with the actual ID of the container:

```bash
docker inspect CONTAINER_ID
```

4. In the output, locate the Gateway address. This is the host address you will need.
5. Enter Hostname in pgAdmin. In the Connection tab of pgAdmin, enter the retrieved Gateway as the Host address.
6. Create a New Database

After successfully connecting to the server:

1. Right-click on the server name in pgAdmin.
2. Select Create > Database.
3. Name the database amazon_books.
4. Save the new database.


## Airflow Setup

Once you have pgAdmin configured, the next step is to set up a connection in Apache Airflow.

### 1. Access Airflow

- Open your browser and go to [localhost:8080](http://localhost:8080).
- Log in using your Airflow credentials. If you are using the default setup, the username is usually `airflow` and the password is `airflow`.

### 2. Add a New Connection

1. In the Airflow dashboard, go to the **Admin** tab in the top menu and select **Connections**.

2. On the **Connections** page, click the **+** (Add a new record) button in the top-right corner.

3. Fill in the connection details:

   - **Conn Id**: A unique name for this connection (e.g., `postgres_connection`).
   - **Conn Type**: Select `Postgres` from the dropdown menu.
   - **Host**: Enter the host IP address for your PostgreSQL server (this is the `Gateway` address from the previous steps).
   - **Schema**: (Optional) Enter the name of the database you want to connect to (e.g., `amazon_books`).
   - **Login**: Your PostgreSQL username (e.g., `postgres`).
   - **Password**: Your PostgreSQL password.
   - **Port**: Enter `5432` (the default PostgreSQL port).

4. Click **Save** to create the new connection.