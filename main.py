import json
import requests
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import os

def encrypt_credentials(credentials, key):
    f = Fernet(key)

    # Sample credentials to encrypt
    credentials = {"userType": "member"}
    credentials_str = json.dumps(credentials).encode()

    # Encrypting the credentials
    encrypted_credentials = f.encrypt(credentials_str).decode()
    return encrypted_credentials

def decrypt_credentials(encrypted_credentials, key):
    f = Fernet(key)
    decrypted = f.decrypt(encrypted_credentials.encode())
    credentials = json.loads(decrypted.decode())
    # Assume credentials now include a userType field
    return credentials

def checkout_book(data):
    # Simulate checking out a book
    print("Checking out book with data:", data)
    return True

def return_book(data):
    # Simulate returning a book
    print("Returning book with data:", data)
    return True

def search_catalog(data):
    # Base URL for the Open Library Search API
    api_url = "https://openlibrary.org/search.json"
    
    # Extracting the search query from the data
    query = data.get("query", "")  # Assuming data contains a "query" key with the search term
    params = {
        "q": query,  # Your search term
        "fields": "key,title,author_name,first_publish_year,cover_i",  # Specifying which fields to return
    }
    
    # Making the GET request to the Open Library API
    response = requests.get(api_url, params=params)
    
    # Check if the request was successful
    if response.status_code == 200:
        search_results = response.json()['docs']  # Extracting the 'docs' from the response
        # Format or process the search_results as needed for your application
        formatted_results = [{"title": result["title"],
                              "author": result.get("author_name", ["Unknown"])[0],
                              "year": result.get("first_publish_year", "Not Available"),
                              "cover_id": result.get("cover_i", None)}
                             for result in search_results]
        return {"results": formatted_results, "status": "success"}
    else:
        return {"results": [], "status": "failure", "message": "Failed to fetch data from Open Library"}

def is_operation_allowed(operation, user_type):
    permissions = {
        'admin': ['checkout', 'return', 'search'],
        'librarian': ['checkout', 'return', 'search'],
        'member': ['search']  # Restrict 'member' to only 'search' operations
    }
    return operation in permissions.get(user_type, [])

def main(job_descriptor):
    load_dotenv()
    encryption_key = os.getenv('ENCRYPTION_KEY').encode()
    credentials = decrypt_credentials(job_descriptor['encryptedCredentials'], encryption_key)
    
    user_type = credentials.get('userType', 'member')  # Default to 'member' if not specified
    operation = job_descriptor['operation']

    # Check if the operation is allowed for the user type
    if not is_operation_allowed(operation, user_type):
        return {"status": "failure", "operation": operation, "message": "Operation not allowed for user type: {}".format(user_type)}
    
    # Perform the operation based on the job descriptor
    data_to_process = job_descriptor['dataToProcess']
    if operation == 'checkout':
        checkout_result = checkout_book(data_to_process)
        result_message = "Checkout successful" if checkout_result else "Checkout failed"
    elif operation == 'return':
        return_result = return_book(data_to_process)
        result_message = "Return successful" if return_result else "Return failed"
    elif operation == 'search':
        search_results = search_catalog(data_to_process)
        result_message = "Search completed with results: " + str(search_results["results"])
    else:
        raise ValueError("Unsupported operation")

    # Return a result
    return {"status": "success", "operation": operation, "message": result_message}

def test_search_catalog():
    data_to_process = {
    "query": "the lord of the rings"
    }

    search_results = search_catalog(data_to_process)
    print(search_results)
# This would be the entry point for the worker to call with the job descriptor
if __name__ == "__main__":
    load_dotenv()  # Load environment variables
    # test_search_catalog()
    # exit()
    # Sample job descriptor fetched from a queue
    sample_encryption_key = os.getenv('ENCRYPTION_KEY').encode()
    encryptedCredentials = encrypt_credentials({"userType": "member"}, sample_encryption_key)
    sample_job_descriptor = {
        "repositoryUrl": "https://github.com/library-system/main-function",
        "dataSourceLinks": [],
        "dataToProcess": {
            "query": "1984"
        },
        "dataSinkLinks": [],
        "encryptedCredentials": encryptedCredentials,
        "operation": "search",
        "parameters": {}
    }

    # Execute the main function with a sample job descriptor
    result = main(sample_job_descriptor)
    print(result)
