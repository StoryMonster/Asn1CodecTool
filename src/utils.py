

def reformat_payload(payload):
    return "".join(payload.split())

def read_from_file(filename):
    data = ''
    with open(filename, "r") as fd:
        data = fd.read()
    return data