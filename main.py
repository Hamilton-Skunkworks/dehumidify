#!/usr/bin/env python3
"""
dehumidify

Quick script to update Cloudflare DNS with the new ephemeral IP address
of your cloud server using Google secret manager

"""

import requests
from google.cloud import secretmanager


def main():
    """ Where the script magic happens """

    r = requests.get(
        "https://ident.me"
    )  # friendly website which just returns ip address

    if r.status_code != 200:
        print(f"IDME status code {r.status_code} exiting!..")
        exit(1)
    ipaddr = r.text

    client = secretmanager.SecretManagerServiceClient()

    ZONE = client.access_secret_version(
        "projects/hamworks-dev/secrets/cf-zone/versions/latest"
    ).payload.data.decode("UTF-8")
    IDENTIFIER = client.access_secret_version(
        "projects/hamworks-dev/secrets/cf-identifier/versions/latest"
    ).payload.data.decode("UTF-8")
    TOKEN = client.access_secret_version(
        "projects/hamworks-dev/secrets/cf-token/versions/latest"
    ).payload.data.decode("UTF-8")
    HOSTNAME = client.access_secret_version(
        "projects/hamworks-dev/secrets/dev-hostname/versions/latest"
    ).payload.data.decode("UTF-8")

    HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE}/dns_records?"

    r = requests.get(url, headers=HEADERS, data={"name": HOSTNAME})

    if r.status_code != 200:
        print(f"CLoudflare GET status code {r.status_code} exiting!..")
        exit(1)

    records = r.json()
    dns = [
        record.get("content")
        for record in records.get("result")
        if record.get("name") == HOSTNAME
    ][0]

    if dns == ipaddr:
        print("Server IP and DNS match. Exiting without doing anything...")
        exit()

    # If they are different, it's time to push the change to Cloudflare

    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE}/dns_records/{IDENTIFIER}"

    DNSUPDATE = {
        "type": "A",
        "name": HOSTNAME,
        "content": ipaddr,
        "ttl": "1",
        "proxied": "false",
    }

    r = requests.put(url, headers=HEADERS, json=DNSUPDATE)

    if r.status_code != 200:
        print(f"CLoudflare PUT status code {r.status_code} exiting!..")
        exit(1)

    print(f"DNS updated to point to {ipaddr}!")
    exit()


if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()
