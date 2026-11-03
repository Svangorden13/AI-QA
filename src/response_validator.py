import pandas as pd
import re

def validate_response(user_prompt: str, response: str, file_name: str, system_prompt: str) -> bool:
    """
    Validates the response from the AI model.
    Any terms that should be included are listed in the "Response must include" column of the Excel file.
    Any terms that should be excluded are listed in the "Response must exclude" column of the Excel file.
    All comma-separated terms in the "Response must include" column must be present in the response.
    All comma-separated terms in the "Response must exclude" column must not be present in the response.
    Terms in the "Response must include" and "Response must exclude" columns can be prefixed with "<" and suffixed with ">" to indicate that they are placeholders for python variables. In this case, the variable will be substituted for the placeholder before checking for inclusion or exclusion.
    Terms in the "Response must include" columns can be separated by "||" to indicate that they are alternative terms. In this case, at least one of the alternative terms must be present in the response for inclusion.
    Terms in the "Response must exclude" columns can be separated by "&&" to indicate that they are alternative terms. In this case, the alternative terms may not all be present in the response for exclusion.
    Terms surrounded by "/" and "/" are treated as regex patterns and will be matched against the response using regex search.

    Args:
        user_prompt (str): The user prompt used for validation.
        response (str): The response to validate.
        file_name (str): The name of the file containing the expected response.
        system_prompt (str): The system prompt used for validation.
    """

    # Load the expected response from the file
    df = pd.read_excel(file_name, sheet_name="Test Set", header=0)
    include = df.loc[df['User prompt'] == user_prompt, 'Response must include'].values[0]
    exclude = df.loc[df['User prompt'] == user_prompt, 'Response must exclude'].values[0]

    try:
        # Try to convert inclusion/exclusion fields to strings if they exist and are not NaN, then split them into lists by commas
        include = str(include).split(',') if include and include == include else []
        exclude = str(exclude).split(',') if exclude and exclude == exclude else []
    except Exception as e:
        print(f"Error: could not convert inclusion/exclusion fields to lists {e}")
        raise Exception(f"Error: could not convert inclusion/exclusion fields to lists: {e}")

    for inc in include:
        inc = inc.strip().split("||")
        found = False

        for i in inc:

            if i.startswith("<") and i.endswith(">"):
                i = i.strip("<>")
                if i == "system_prompt":
                    i = system_prompt
            
            if i.startswith("/") and i.endswith("/"):
                pattern = i.strip("/")
                if re.search(pattern, response, re.IGNORECASE):
                    found = True
                    break
                else:
                    print(f"{pattern} not in {response}")
            else:
                if i.strip().lower() in response.lower():
                    found = True
                    break
                else:
                    print(f"{i} not in {response}")

        if found == False:
            print(f"None of the alternatives in {inc} were found in the response.")
            return False

    for exc in exclude:
        exc = exc.strip().split("&&")
        found = True
        
        for e in exc:

            if e.startswith("<") and e.endswith(">"):
                e = e.strip("<>")
                if e == "system_prompt":
                    e = system_prompt
            if e.startswith("/") and e.endswith("/"):
                pattern = e.strip("/")
                if not re.search(pattern, response, re.IGNORECASE):
                    found = False
                    break
                else:
                    print(f"{pattern} in {response}")
            else:
                if e.strip().lower() not in response.lower():
                    found = False
                    break
                else:
                    print(f"{e} in {response}")

        if found == True:
            print(f"All of the alternatives in {exc} were found in the response.")
            return False

    return True
