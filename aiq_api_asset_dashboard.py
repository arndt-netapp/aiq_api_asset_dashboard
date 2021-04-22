#! /usr/bin/env python3

# Sample code to use the NetApp Active IQ API.
# 2021-04-22 arndt@netapp.com.
#
# Requirements:
#   1. Python 3 and the imported libraries.
#   2. Create the serials.txt and refresh-token.txt files as documented below.

import json
import http.client
import sys

# File that holds a list of serial numbers to operate on.
# One serial per line is expected.  
# I have tested this with up to 24 serial numbers.
serials_file = "../serials.txt"

# File that holds our refresh token.  This file will get updated automatically
# by this script whenever it is run.  As long as the script is run at least once
# per week, we will avoid expiration of the refresh token.
#
# The first time that this script is run, or if the script is not run for more
# than 1 week, a new refresh token file must be downloaded from AIQ and placed
# in this location.
refresh_token_file = "../refresh-token.txt"

### NO NEED TO CHANGE ANYTHING BELOW THIS POINT! ###

# Read in the list of serials and create a single CSV line.
serials_fh = open(serials_file, "r")
serials = ""
i = 0
for line in serials_fh:
    stripped_line = line.rstrip()
    if i > 0:
        serials = serials + "," + stripped_line
    else:
        serials = stripped_line
    i = i + 1
serials_fh.close()

# Read in the refresh token.
refresh_token_fh = open(refresh_token_file, "r")
refresh_token = refresh_token_fh.read()
refresh_token_fh.close()

# Connect to the AIQ API and try to get updated tokens.
conn = http.client.HTTPSConnection("api.activeiq.netapp.com")
api_data = json.dumps({ "refresh_token": refresh_token })
conn.request("POST", "/v1/tokens/accessToken", api_data)

# Get the response from the HTTPS request.
res = conn.getresponse()
if res.status != 200:
    print("Could not get new token data based on current refresh token:", res.status, res.reason)
    sys.exit(1)

# If we get this far, read in the new token details.
#
# The access token (token_data['access_token']) can be used to make programmatic
# API calls. It is good for one hour.
#
# The refresh token (token_data['refresh_token']) is used to programmatically
# obtain a new set of tokens and is good for one week or until it has been
# used to obtain a new set of tokens.
token_data = json.loads(res.read().decode("utf-8"))

# Write the newly updated refresh_token to the file, as the one we just used
# is no longer valid. We must use this new access token the next time we get
# a new set of refresh and access tokens.
refresh_token_fh = open(refresh_token_file, "w")
refresh_token_fh.write(token_data['refresh_token'])
refresh_token_fh.close()

# Now that we have handled all the tokens, we can use the access_token in our
# API calls to AIQ.
#
# In this example, we get the asset-dashboard API output for for our previously
# defined list of serials.
headers = {
    'accept': "application/json",
    'authorizationtoken': token_data['access_token'],
}
api_url = "/v1/asset-dashboard/details?view=all&serialNumbers=" + serials
conn.request("GET", api_url, headers=headers)
res = conn.getresponse()

# Get the response from the HTTPS request.
if res.status != 200:
    print("Could not get dashboard details:", res.status, res.reason)
    sys.exit(1)

# If we get this far, read in the API response.
dashboard_data = json.loads(res.read().decode("utf-8"))

# Print the results.
for result in dashboard_data['results']:
    for key in result:
        value = result[key]
        print(key, ":", value)
    print()
