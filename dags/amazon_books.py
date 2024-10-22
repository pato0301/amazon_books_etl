from datetime import datetime, timedelta
from airflow import DAG
import requests
import pandas as pd
from bs4 import BeautifulSoup
from airflow.operators.python import PythonOperator
from airflow.models import TaskInstance
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook


# Define HTTP headers for the Amazon request
headers: dict[str, str] = {
    "Referer": 'https://www.amazon.com/',
    "Sec-Ch-Ua": "Not_A Brand",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": "macOS",
    'User-agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36')
}

def get_amazon_data_books(num_books: int, ti: TaskInstance) -> None:
    """
    Scrapes book data from Amazon for data engineering books and pushes the data to XCom.

    Args:
        num_books (int): The number of books to retrieve.
        ti (TaskInstance): Airflow TaskInstance for XCom pushing.

    Returns:
        None
    """
    base_url: str = "https://www.amazon.com/s?k=data+engineering+books"
    books: list[dict[str, str]] = []
    seen_titles: set[str] = set()  # To track seen book titles
    page: int = 1

    while len(books) < num_books:
        url: str = f"{base_url}&page={page}"
        
        # Send a request to the URL
        response = requests.get(url, headers=headers)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the content of the response with BeautifulSoup
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Find book containers (adjust class names as necessary based on the HTML structure)
            book_containers = soup.find_all("div", {"class": "s-result-item"})
            
            # Loop through book containers and extract data
            for book in book_containers:
                title = book.find("span", {"class": "a-text-normal"})
                author = book.find("a", {"class": "a-size-base"})
                price = book.find("span", {"class": "a-price-whole"})
                rating = book.find("span", {"class": "a-icon-alt"})
                
                if title and author and price and rating:
                    book_title: str = title.text.strip()
                    
                    # Check if the title has been seen before
                    if book_title not in seen_titles:
                        seen_titles.add(book_title)
                        books.append({
                            "Title": book_title,
                            "Author": author.text.strip(),
                            "Price": price.text.strip(),
                            "Rating": rating.text.strip(),
                        })
            page += 1  # Move to the next page
        else:
            print("Failed to retrieve the page")
            break

    # Limit the list to the requested number of books
    books = books[:num_books]
    
    # Convert the list of dictionaries to a DataFrame
    df: pd.DataFrame = pd.DataFrame(books)
    
    # Remove duplicates based on the 'Title' column
    df.drop_duplicates(subset="Title", inplace=True)
    
    # Push the DataFrame to XCom
    ti.xcom_push(key='book_data', value=df.to_dict('records'))

def insert_book_data_into_postgres(ti: TaskInstance) -> None:
    """
    Inserts book data pulled from XCom into a PostgreSQL database.

    Args:
        ti (TaskInstance): Airflow TaskInstance for XCom pulling.

    Returns:
        None
    """
    # Pull book data from XCom
    book_data: list[dict[str, str]] = ti.xcom_pull(key='book_data', task_ids='fetch_book_data')
    if not book_data:
        raise ValueError("No book data found")

    # Set up the PostgreSQL hook
    postgres_hook = PostgresHook(postgres_conn_id='amazon_books_connection')
    insert_query: str = """
        INSERT INTO books (title, authors, price, rating)
        VALUES (%s, %s, %s, %s)
    """
    
    # Insert each book record into the database
    for book in book_data:
        postgres_hook.run(insert_query, parameters=(book['Title'], book['Author'], book['Price'], book['Rating']))


default_args: dict = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 10, 20),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag: DAG = DAG(
    'amazon_books_api_etl',
    default_args=default_args,
    description='A DAG to fetch books data from Amazon books API, clean the data, and store it in Postgres',
    schedule_interval='@daily',
    catchup=False
)

# Task to fetch Amazon book data
fetch_book_data_task: PythonOperator = PythonOperator(
    task_id='fetch_book_data',
    python_callable=get_amazon_data_books,
    op_args=[50],  # Number of books to fetch
    dag=dag,
)

# Task to create the books table in PostgreSQL
create_table_task: PostgresOperator = PostgresOperator(
    task_id='create_table',
    postgres_conn_id='amazon_books_connection',
    sql="""
        CREATE TABLE IF NOT EXISTS books (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            authors TEXT,
            price TEXT,
            rating TEXT
        );
    """,
    dag=dag,
)

# Task to insert book data into PostgreSQL
insert_book_data_task: PythonOperator = PythonOperator(
    task_id='insert_book_data',
    python_callable=insert_book_data_into_postgres,
    dag=dag,
)

# Define task dependencies
fetch_book_data_task >> create_table_task >> insert_book_data_task