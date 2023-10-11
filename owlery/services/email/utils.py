def generate_oauthbearer_string(identity, access_token):
    identity = identity.replace("=", "=3D").replace(",", "=2C")

    return f"n,a={identity},\1auth={access_token}\1\1"


def generate_xoauth2_string(identity, access_token, vendor=None):
    identity = identity.replace("=", "=3D").replace(",", "=2C")

    auth_string = f"user={identity},\1auth={access_token}\1"
    if vendor:
        auth_string += f"vendor={vendor}\1"
    return auth_string
