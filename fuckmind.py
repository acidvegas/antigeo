#!/usr/bin/env python
# Mass MaxMind Opt-Out - Developed by acidvegas in Python (https://git.acid.vegas/antigeo)

import urllib.request
import http.client
import urllib.parse
import argparse
import logging
from html.parser import HTMLParser

class CSRFTokenParser(HTMLParser):
    """ Parser to extract CSRF token from HTML. """
    def __init__(self):
        super().__init__()
        self.csrf_token = None

    def handle_starttag(self, tag, attrs):
        if tag == 'input':
            attrs = dict(attrs)
            if attrs.get('name') == 'csrf_token':
                self.csrf_token = attrs.get('value')

def get_csrf_token(url):
    """ Fetch the page to get the CSRF token. """
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        page_content = response.read().decode('utf-8')
    parser = CSRFTokenParser()
    parser.feed(page_content)
    return parser.csrf_token

def submit_form_via_proxy(csrf_token, proxy):
    """ Submit the form via a specified proxy. """
    post_data = urllib.parse.urlencode({
        'csrf_token': csrf_token,
        'request_type': 'global-opt-out'
    }).encode()

    proxy_host, proxy_port = proxy.split(':')
    conn = http.client.HTTPConnection(proxy_host, int(proxy_port))
    conn.set_tunnel("www.maxmind.com")

    headers = {"Content-type": "application/x-www-form-urlencoded"}
    conn.request("POST", "/en/opt-out", post_data, headers)

    response = conn.getresponse()
    logging.info(f"Response from proxy {proxy}: {response.status}, {response.reason}")
    data = response.read()
    logging.debug(data.decode())
    conn.close()

def read_proxies_from_file(file_path):
    """ Read proxies from a file. """
    with open(file_path, 'r') as file:
        return [line.strip() for line in file.readlines()]

def main(proxy_file):
    """ Main function to execute the script logic. """
    url = 'https://www.maxmind.com/en/opt-out'
    csrf_token = get_csrf_token(url)
    if not csrf_token:
        raise ValueError("CSRF token not found")

    proxies = read_proxies_from_file(proxy_file)
    for proxy in proxies:
        try:
            submit_form_via_proxy(csrf_token, proxy)
        except Exception as e:
            logging.error(f"An error occurred with proxy {proxy}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Submit a form via a list of proxies from a file")
    parser.add_argument('--proxy-file', type=str, required=True,
                        help='File containing list of proxies, one per line in the format host:port')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    main(args.proxy_file)