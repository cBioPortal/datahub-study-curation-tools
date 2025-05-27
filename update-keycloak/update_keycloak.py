# Tool for updating roles or user permissions via the Keycloak REST API

# Case 1: Add roles to a composite role
#
# Usage:
#   python3 update_keycloak.py --realm <realm-name> --composite_role <composite-role-name> --role-filename <filename>
#
# Arguments:
#   --realm            : Name of the Keycloak realm.
#   --composite_role   : Name of the existing composite role to which new roles will be added.
#   --role-filename    : Path to a text file containing a list of role names (one role per line).
#
# Format of the role file (<filename>):
#   Each line in the file should contain the name of a role to be added to the composite role.
#
# Example content of the file:
#   Role1
#   Role2
#   Role3
#   ...

import os
import requests
import argparse
from dotenv import load_dotenv

load_dotenv()
BASE_URL = "https://keycloak.cbioportal.mskcc.org/auth/admin/realms"

def get_access_token():
    username = os.getenv("KEYCLOAK_USERNAME")
    password = os.getenv("KEYCLOAK_PASSWORD")
    
    if not username or not password:
        raise ValueError("Keycloak username and password environment variable not set!")
    
    url = "https://keycloak.cbioportal.mskcc.org/auth/realms/master/protocol/openid-connect/token"
    data = {
        "grant_type": "password",
        "client_id": "admin-cli",
        "username": username,
        "password": password
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(url, data=data, headers=headers)
    response.raise_for_status()
    return response.json()["access_token"]
    
def get_role_by_name(realm, role_name, token):
    url = f"{BASE_URL}/{realm}/roles/{role_name}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 404:
        return None  # Role does not exist
    response.raise_for_status()
    return response.json()
    
def create_role(realm, role_name, token):
    url = f"{BASE_URL}/{realm}/roles"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    role_data = {
        "name": role_name,
        "composite": False,
        "clientRole": False,
        "description": "Created via API"
    }
    response = requests.post(url, headers=headers, json=role_data)
    response.raise_for_status()
    print(f"Created role '{role_name}'")
    # After creation, get the role details (ID)
    return get_role_by_name(realm, role_name, token)

def add_role_to_composite(realm, composite_role_id, role_to_add, token):
    url = f"{BASE_URL}/{realm}/roles-by-id/{composite_role_id}/composites"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, json=[role_to_add])
    response.raise_for_status()

def get_composite_roles(realm, role_id, token):
    url = f"{BASE_URL}/{realm}/roles-by-id/{role_id}/composites"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def main():
    parser = argparse.ArgumentParser(description="Add roles to a composite role in Keycloak")
    parser.add_argument('--realm', required=True, help='Name of the Keycloak realm.')
    parser.add_argument('--composite_role', required=True, help='Name of the composite role.')
    parser.add_argument('--role-filename', required=True, help='Path to the file containing role names.')
    args = parser.parse_args()
    
    realm = args.realm
    composite_role_name = args.composite_role
    roles_file = args.role_filename
    
    token = get_access_token()
    
    # Check if composite_role exists
    composite_role = get_role_by_name(realm, composite_role_name, token)
    if not composite_role:
        print(f"Composite role '{composite_role_name}' not found. Exiting.")
        return
    
    with open(roles_file, "r") as f:
        role_names = [line.strip() for line in f if line.strip()]
    
    """
    # Get all the roles in composite roles to identify missing roles from public studies
    roles = get_composite_roles(realm, composite_role['id'], token)
    print(f"\nRoles in composite role '{composite_role_name}':")
    for role in roles:
        print(f"{role['name']}")
    """
    
    for role_name_to_add in role_names:
        # Check if the role to add exists, else create
        role_to_add = get_role_by_name(realm, role_name_to_add, token)
        if not role_to_add:
            role_to_add = create_role(realm, role_name_to_add, token)
            
        # Add the role to the composite role
        add_role_to_composite(realm, composite_role['id'], role_to_add, token)
        print(f"Added '{role_name_to_add}' to composite role '{composite_role_name}'")

if __name__ == "__main__":
    main()