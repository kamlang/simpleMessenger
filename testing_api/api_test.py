#!/usr/bin/python

import json
import requests
import click
import warnings

# Removing warning about untrusted ssl certificate so it can be used to do testing with self signed certificate.
# Allow us to pipe the result directly as valid json.
from urllib3.connectionpool import InsecureRequestWarning

warnings.filterwarnings("ignore", category=InsecureRequestWarning)

HTTP_METHODS = ["GET", "POST", "DELETE", "PUT", "PATCH"]
URL_BASE = "https://localhost:5000"
OAUTH_TOKEN_ENDPOINT="/auth/oauth/token"

@click.command(no_args_is_help=True)
@click.argument("api_endpoint", nargs=1, type=click.STRING, required=True)
@click.option("-m", "--method", help="HTTP method to use. Default GET." ,default="GET", type=click.STRING)
@click.option(
    "-d",
    "--data",
    default="",
    help='HTTP body data specified as json. Should be wrapped between single quotation mark: \'{"k1":"v1","k2":"v2"}\'.',
    type=click.STRING,
)
@click.option(
    "-v", "--verify", default=True, help="Disable verification of SSL certifiacte if set to False.", type=click.BOOL
)
@click.option(
    "-c",
    "--credentials_file",
    default="credentials.json",
    help="Path to credentials.json file. Looking in current directory by default.",
    type=click.Path(exists=True),
)
@click.option(
    "-t",
    "--token_file",
    default="token.json",
    help="Path to token.json file. Looking in current directory by default.",
    type=click.Path(exists=True),
)
def run(method, api_endpoint, data, credentials_file, token_file, verify):
    """ Small CLI which can interact with an API that uses OAuth 2.0 protocol for authorization.
    It's expected that credentials file has a valid OAuth client id and client secret included,
    and that token file has a valid refresh token. It will take care of automatically refresh OAuth token when needed.
    API_ENDPOINT is a relative url path like: '/api/user/endpoint/'."""
    credentials_data = load_from_file(credentials_file)
    token_data = load_from_file(token_file)

    make_request = get_request_function(method)
    headers = {"Authorization": "Bearer " + token_data["access_token"]}
    url = URL_BASE + api_endpoint

    if data:
        data = json.loads(data)
        request_keywords = {"data": data,"headers":headers,"verify":verify}
    else:
        request_keywords = {"headers":headers,"verify":verify}

    res = make_request(url, **request_kwords)

    if res.status_code == 401: 
        token_data = get_fresh_token_data(token_data,credentials_data,token_file,verify)
        request_kwords["headers"] = {"Authorization": "Bearer " + token_data["access_token"]}
        res = make_request(url, **request_kwords)

    click.echo(prettify(res.json()))

def get_fresh_token_data(token_data,credentials_data,token_file,verify):

    url = URL_BASE + OAUTH_TOKEN_ENDPOINT

    make_request = get_request_function("POST")
    auth = (credentials_data["client_id"], credentials_data["client_secret"])
    data = {
        "refresh_token": token_data["refresh_token"],
        "scope": token_data["scope"],
        "grant_type": "refresh_token",
    }
    res = make_request(url, auth=auth, verify=verify, data=data)
    new_token_data = res.json()
    token_data |= new_token_data
    with open(token_file, "w") as f:
        f.write(json.dumps(token_data))
    return token_data


def prettify(json_response):
    return json.dumps(json_response, indent=2)


def get_request_function(method):
    if method.upper() in HTTP_METHODS:
        return getattr(requests, method.lower())
    else:
        raise Exception("The HTTP method specified is not valid.")


def load_from_file(file):
    try:
        with open(file) as f:
            json_data = json.load(f)
    except json.JSONDecodeError:
        raise Exception("File is invalid. Please verify content is valid json.")
    return json_data


if __name__ == "__main__":
    run()
