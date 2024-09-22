import json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import db_helper
import generic_helper

inprogress_issue = {}

app = FastAPI()


@app.post("/")
async def handle_request(request: Request):
    # Retrieve the JSON data from the request
    payload = await request.json()

    # Extract the necessary information from the payload
    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    output_contexts = payload['queryResult']['outputContexts']

    session_id = generic_helper.extract_session_id(output_contexts[0]['name'])

    # Extract context based on available output contexts
    context = ""
    for context_item in output_contexts:
        context_name = generic_helper.extract_context(context_item['name'])
        if context_name in ["ongoing_issue", "ongoing_return"]:
            context = context_name
            break

    intent_handler_dict = {
        'IssueBook': issue_book,
        'user.confirm:ongoing_issue': user_confirmation_issue,
        'Uid.Pass: ongoing_issue': uid_pass_issue,
        'Uid.Pass: ongoing_return': uid_pass_return,
        'final.return': final_check
    }

    return intent_handler_dict[intent](parameters, session_id, context, output_contexts)

####### BOOK ISSUE ###########
def issue_book(parameters: dict, session_id: str, context: str, output_contexts: list):
    book_name = parameters['book_name']

    # Get availability from the helper function
    availability = db_helper.get_availability(book_name)

    # Formulate the response based on the availability
    if availability is None:
        fulfillmentText = f"The book '{book_name}' was not found in our catalog."
    elif availability:
        inprogress_issue[session_id] = book_name
        fulfillmentText =  f"Yes, '{book_name}' is available. Would you like to proceed? (Yes/No)"
    else:
        fulfillmentText = f"Sorry, '{book_name}' is not available right now. Please check for another book."

    return JSONResponse(content={'fulfillmentText': fulfillmentText})


def user_confirmation_issue(parameters: dict, session_id: str, context: str, output_contexts: list):
    confirmation = parameters.get("confirm", "").capitalize()

    if confirmation == 'Yes':
        fulfillmentText = "Great! Please provide your User ID and password to proceed. (Format: uid = Your User ID, password = Your Password)"
    elif confirmation == 'No':
            fulfillmentText = "The process was not confirmed. Let us know if you need anything else."
    else:
            fulfillmentText = "Kindly respond with either 'Yes' or 'No'."

    return JSONResponse(content={"fulfillmentText": fulfillmentText})


def uid_pass_issue(parameters: dict, session_id: str, context: str, output_contexts: list):
    user_id = parameters.get('user_id', '')
    password = parameters.get('password', '')

    try:
        user_id = user_id.split("=")[1].strip()
        password = password.split("=")[1].strip()
    except IndexError:
        fulfillmentText = "Please provide both user_id and password in the correct format."
        return JSONResponse(content={"fulfillmentText": fulfillmentText})

    if not user_id or not password:
            fulfillmentText = 'Please provide both user_id and password as uid = Your Id and password = Your Password'
    else:
        user_exists = db_helper.check_user_credentials(user_id, password)
        if not user_exists:
            fulfillmentText = "Invalid user_id or password. Please try again."
        else:
            book_name = inprogress_issue.get(session_id)
            if book_name:
                shelf = db_helper.get_shelf(book_name)
                fulfillmentText = f"The book '{book_name}' is present on shelf '{shelf}'."
            else:
                fulfillmentText = "Sorry, we seem to have lost track of the book you were trying to issue. Please try again."
    return JSONResponse(content={"fulfillmentText": fulfillmentText})

########### BOOK Return ##########

from fastapi.responses import JSONResponse

def uid_pass_return(parameters: dict, session_id: str, context: str, output_contexts: list):
    # Extract user_id, password, and book_name from parameters
    user_id = parameters.get('user_id', '')
    password = parameters.get('password', '')
    book_name = parameters.get('book_name', '').strip()

    try:
        user_id = user_id.split("=")[1].strip()
        password = password.split("=")[1].strip()
    except IndexError:
        fulfillmentText = "Please provide both user_id and password in the correct format."
        return JSONResponse(content={"fulfillmentText": fulfillmentText})

    # Check if user_id and password were provided
    if not user_id or not password:
        fulfillmentText = 'Please provide both user_id and password in the format: uid = Your Id and password = Your Password.'
        return JSONResponse(content={"fulfillmentText": fulfillmentText})

    # Check if user credentials are valid
    user_exists = db_helper.check_user_credentials(user_id, password)

    if not user_exists:
        fulfillmentText = "Invalid user_id or password. Please try again."
        return JSONResponse(content={"fulfillmentText": fulfillmentText})

    # Fetch the list of books borrowed by the user
    book_names = db_helper.get_book_names(user_id)

    if len(book_names) == 0:
        fulfillmentText = "You haven't borrowed any books."
    elif len(book_names) > 1:
        fulfillmentText = f"Hey, you've borrowed the following books: {', '.join(book_names)}. Please name the book you want to return for confirmation."
    else:
        fulfillmentText = f"You have borrowed {book_names[0]}. Please type the book name for confirmation."

    # Return JSONResponse and pass book_names in the context for later use
    output_context = {
        "name": f"projects/alaya-khkf/agent/sessions/{session_id}/contexts/final_check",
        "lifespanCount": 5,
        "parameters": {
            "user_id": user_id,
            "book_names": book_names  # Store the list of book names in the context
        }
    }

    return JSONResponse(content={"fulfillmentText": fulfillmentText, "outputContexts": [output_context]})

def final_check(parameters: dict, session_id: str, context: list, output_contexts: list):
    # Normalize the list of borrowed books (convert to lowercase and remove extra spaces)
    borrowed_books = output_contexts[0]['parameters'].get("book_names", [])
    borrowed_books = [book.lower().strip() for book in borrowed_books]

    # Extract and normalize the book name provided by the user
    query = parameters.get("book_name", "").lower().strip()

    # Check if the provided book name exists in the list of borrowed books
    if query in borrowed_books:
        fulfillmentText = f"You have successfully returned '{parameters['book_name']}'."
    else:
        # If the book name doesn't match, provide feedback with the list of borrowed books
        fulfillmentText = f"The borrowed books are: {', '.join(borrowed_books)}. Please provide a valid book name."

    # Return the fulfillment text in JSONResponse
    return JSONResponse(content={"fulfillmentText": fulfillmentText})

