import mysql.connector
import os
# Fetching the environment variables using os.getenv()
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")


cnx = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=3306
        )

def get_availability(book_name):
    cursor = cnx.cursor()

    # Parameterized query to safely fetch the availability status
    query = "SELECT available FROM Books WHERE title = %s"
    cursor.execute(query, (book_name,))

    # Fetching the result
    result = cursor.fetchone()

    # Closing the cursor
    cursor.close()

    # Check if a result is found and return availability status
    if result:
        availability = result[0]
        return availability == 1  # Return True if available, otherwise False
    else:
        return None  # Return None if the book is not found

def check_user_credentials(user_id, password):
    cursor = cnx.cursor()

    # Parameterized query to safely fetch user credentials
    query = "SELECT * FROM Users WHERE user_id = %s AND password = %s"
    cursor.execute(query, (user_id, password))

    # Fetching the result
    result = cursor.fetchone()

    # Closing the cursor
    cursor.close()

    # Check if result is None
    if result is None:
        return False  # No user found

    # If result is found, return True
    return True


def get_shelf(book_name):
    cursor = cnx.cursor()

    # Parameterized query to safely fetch the shelf number
    query = "SELECT shelf_no FROM Books WHERE title = %s"
    cursor.execute(query, (book_name,))

    # Fetching the result
    result = cursor.fetchone()

    # Closing the cursor
    cursor.close()

    # If a result is found, return the shelf number
    if result:
        return result[0]  # Return the first column which is the shelf_no
    else:
        return None  # Return None if the book is not found


def get_book_names(user_id):
    cursor = cnx.cursor()

    # Query to get all book titles borrowed by the user
    query = """
        SELECT title 
        FROM Books 
        WHERE book_id IN (
            SELECT book_id 
            FROM Borrowed_Books 
            WHERE user_id = %s
        )
    """

    # Execute the query
    cursor.execute(query, (user_id,))

    # Fetch all results
    results = cursor.fetchall()

    # Closing the cursor
    cursor.close()

    # Return the list of titles if found
    if results:
        return [row[0] for row in results]  # Return a list of book titles
    else:
        return []  # Return an empty list if no books are found

