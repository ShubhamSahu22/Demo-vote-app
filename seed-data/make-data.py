import urllib.parse

# Function to create URL-encoded files for votes
def create_encoded_file(filename, params):
    with open(filename, 'w') as outfile:
        encoded = urllib.parse.urlencode(params)
        outfile.write(encoded)

# Create URL-encoded files for votes 'a' and 'b'
create_encoded_file('posta', {'vote': 'a'})
create_encoded_file('postb', {'vote': 'b'})
