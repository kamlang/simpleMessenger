import re
import os

def build_api_doc(file_path = os.path.join(os.getcwd(),"app/api/views.py")):
    """ Parsing api views.py file, to generate a list containg the endpoint,
    the http method and the doc string for each route."""

    with open(file_path) as file:
        file_content = file.read()

    viewfunc_pattern = re.compile(r"""@api\.route      
            \(\"(.*?)\".*?\[\"(.*?)\"\]\)\n  # Getting the route's path and the http method
            (?:@.*\n)*?                      # Eventually taking extra decorators into account
            def.*\)\:\n                      # Checking if a function is defined
            \s+["]{3}((.*?\n?)*?)["]{3}      # Getting the docstring
            """,re.VERBOSE)

    api_doc_list = re.findall(viewfunc_pattern,file_content)

    clean_api_doc_list = []
    for route in api_doc_list:
        route_dict = {}
        route_dict["path"] = "/api" + route[0]
        route_dict["method"] = route[1]
        route_dict["help"] = route[2].replace("\n","").strip()
        clean_api_doc_list.append(route_dict)
    return clean_api_doc_list

if __name__ == "__main__":
    print(build_api_doc(file_path="views.py"))
