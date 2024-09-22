import re
def extract_session_id(session_str: str):
    match = re.search(r"sessions/(.*?)/contexts/", session_str)
    if match:
        extracted_string = match.group(1)
        return extracted_string

    return ""



def get_number(number_str):
    match = re.search(r'\d+', number_str)

    # If a match is found, extract the number
    if match:
        number = match.group()
    return  number

def extract_context(context_str: str):
    context = context_str.split("/")[-1]
    return context


if __name__ =='__main__':
    num= get_number("user_id is 346677")
    print(num , type(num))


