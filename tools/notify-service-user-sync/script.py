"""
This script will sync Notify service users to Salesforce Contacts and Engagements.
It expects a CSV file with the following columns:
- service_id: str
- service_name: str
- service_organisation_notes: str
- service_restricted: true|false
- user_id: str
- user_name: str
- user_email: str
"""
# pylint: disable=logging-fstring-interpolation,line-too-long

import csv
import logging
import os
from datetime import datetime
from time import sleep

import requests
from requests.adapters import HTTPAdapter
from dotenv import load_dotenv
from simple_salesforce import Salesforce

logging.basicConfig(level=logging.INFO)
load_dotenv()

CSV_PATH = os.getenv("CSV_PATH")

ENGAGEMENT_PRODUCT = "GC Notify"
ENGAGEMENT_TEAM = "Platform"
ENGAGEMENT_TYPE = "New Business"
ENGAGEMENT_STAGE_LIVE = "Live"
ENGAGEMENT_STAGE_TRIAL = "Trial Account"
ENGAGEMENT_RECORD_TYPE = os.getenv("ENGAGEMENT_RECORD_TYPE")
ENGAGEMENT_STANDARD_PRICEBOOK_ID = os.getenv("ENGAGEMENT_STANDARD_PRICEBOOK_ID")
ENGAGEMENT_PRODUCT_ID = os.getenv("ENGAGEMENT_PRODUCT_ID")

GENERIC_ACCOUNT_ID = os.getenv("GENERIC_ACCOUNT_ID")

LOGIN_USERNAME = os.getenv("LOGIN_USERNAME")
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD")
LOGIN_SECURITY_TOKEN = os.getenv("LOGIN_SECURITY_TOKEN")
LOGIN_DOMAIN = os.getenv("LOGIN_DOMAIN")

ORG_NOTES_ORG_NAME_INDEX = 0
ORG_NOTES_OTHER_NAME_INDEX = 1

REQUEST_HEADERS = {"Sforce-Duplicate-Rule-Header": "allowSave=true"}


class TimeoutAdapter(HTTPAdapter):
    """
    3 second timeout for all requests
    """

    def send(self, *args, **kwargs):
        kwargs["timeout"] = 3
        return super().send(*args, **kwargs)


def main():
    """
    Loops through the service users CSV file and creates Salesforce Contacts and Engagements
    """
    session = get_session(
        LOGIN_USERNAME, LOGIN_PASSWORD, LOGIN_SECURITY_TOKEN, LOGIN_DOMAIN
    )
    with open(CSV_PATH, "r", encoding="utf-8") as data:
        account_id = None
        engagement_id = None
        service_id = None

        for row in csv.DictReader(data):
            try:
                logging.info(f"🚣 processing {row}")

                # Check we need to refresh our cached engagement data
                if service_id != row["service_id"]:
                    service_id = row["service_id"]
                    account_name = get_org_name_from_notes(
                        row["service_organisation_notes"], ORG_NOTES_ORG_NAME_INDEX
                    )
                    row["account_id"] = get_account_id_from_name(
                        session, account_name, GENERIC_ACCOUNT_ID
                    )
                    engagement_id, account_id = get_engagement_id(session, row)

                row["account_id"] = account_id
                contact_id = get_contact_id(session, row)

                # Add the Engagement ContactRole if it doesn't already exist
                if not get_engagement_contact_role(session, engagement_id, contact_id):
                    add_engagement_contact_role(session, engagement_id, contact_id)

                sleep(1)
            except Exception as ex:  # pylint: disable=broad-except
                logging.error(f"Failed to process row: {ex}")
                raise ex


def add_contact(session, user):
    """
    Create a Salesforce Contact from the given Notify User
    """
    name_parts = get_name_parts(user["user_name"])
    result = session.Contact.create(
        {
            "FirstName": name_parts["first"],
            "LastName": name_parts["last"],
            "Title": "created by Notify API",
            "CDS_Contact_ID__c": user["user_id"],
            "Email": user["user_email"],
            "AccountId": user["account_id"],
        },
        headers=REQUEST_HEADERS,
    )
    parse_result(result, f"Contact create for '{user['user_email']}'")
    return result.get("id")


def add_engagement(session, service):
    """
    Create a Salesforce Engagement from the given Notify Service
    """
    result = session.Opportunity.create(
        {
            "Name": service["service_name"][:120],
            "AccountId": service["account_id"],
            "CDS_Opportunity_Number__c": service["service_id"],
            "Notify_Organization_Other__c": get_org_name_from_notes(
                service["service_organisation_notes"], ORG_NOTES_OTHER_NAME_INDEX
            ),
            "CloseDate": datetime.today().strftime("%Y-%m-%d"),
            "RecordTypeId": ENGAGEMENT_RECORD_TYPE,
            "StageName": ENGAGEMENT_STAGE_TRIAL
            if service["service_restricted"] == "true"
            else ENGAGEMENT_STAGE_LIVE,
            "Type": ENGAGEMENT_TYPE,
            "CDS_Lead_Team__c": ENGAGEMENT_TEAM,
            "Product_to_Add__c": ENGAGEMENT_PRODUCT,
        },
        headers=REQUEST_HEADERS,
    )
    parse_result(result, f"Engagement create for service '{service['service_name']}'")
    engagement_id = result.get("id")
    if engagement_id:
        result = session.OpportunityLineItem.create(
            {
                "OpportunityId": engagement_id,
                "PricebookEntryId": ENGAGEMENT_STANDARD_PRICEBOOK_ID,
                "Product2Id": ENGAGEMENT_PRODUCT_ID,
                "Quantity": 1,
                "UnitPrice": 0,
            },
            headers=REQUEST_HEADERS,
        )
        parse_result(
            result,
            f"Engagement OpportunityLineItem create for service ID '{service['service_name']}'",
        )
    return (engagement_id, service["account_id"])


def add_engagement_contact_role(session, engagement_id, contact_id):
    """
    Create a Salesforce ContactRole from the given engagement and contact IDs
    """
    result = session.OpportunityContactRole.create(
        {"ContactId": contact_id, "OpportunityId": engagement_id},
        headers=REQUEST_HEADERS,
    )
    parse_result(
        result,
        f"ContactRole add for contact_id '{contact_id}' and engagement_id '{engagement_id}'",
    )


def get_engagement_contact_role(session, engagement_id, contact_id):
    """
    Returns the Salesforce ContactRole for the given engagement and contact IDs
    """
    query = f"SELECT Id, OpportunityId, ContactId FROM OpportunityContactRole WHERE OpportunityId = '{engagement_id}' AND ContactId = '{contact_id}' LIMIT 1"
    return query_one(session, query)


def get_engagement_id(session, service):
    """
    Get the Salesforce Engagement ID for the given Notify Service.
    If an Engagement does not exist, one will be created.
    """
    query = f"SELECT Id, Name, ContactId, AccountId FROM Opportunity where CDS_Opportunity_Number__c = '{service['service_id']}' LIMIT 1"
    engagement = query_one(session, query)
    return (
        (engagement["Id"], engagement["AccountId"])
        if engagement
        else add_engagement(session, service)
    )


def get_org_name_from_notes(organisation_notes, name_index):
    """
    Given a service's organisation notes, returns either the organisation name or
    organisation other name.  The organisation notes structure is as follows:

    "ORG_NAME > ORG_OTHER_NAME"

    For example:

    "Treasury Board Secretariat > Canadian Digital Service"
    """
    note_parts = (
        organisation_notes.split(">") if isinstance(organisation_notes, str) else []
    )
    if len(note_parts) > name_index:
        return note_parts[name_index].strip()
    return organisation_notes


def get_account_id_from_name(session, account_name, generic_account_id):
    """
    Returns the Account ID for the given Account Name.  If no match is found, a generic
    Account not found ID is returned.
    """
    result = None
    account_name_sanitized = query_param_sanitize(account_name)
    if len(account_name_sanitized.strip()):
        query = f"SELECT Id FROM Account where Name = '{account_name_sanitized}' OR CDS_AccountNameFrench__c = '{account_name_sanitized}' LIMIT 1"
        result = query_one(session, query)
    return result.get("Id") if result else generic_account_id


def get_contact_id(session, user):
    """
    Get the Salesforce Contact ID for the given Notify User.
    If a Contact does not exist, one will be created.
    """
    query = f"SELECT Id, FirstName, LastName, AccountId FROM Contact WHERE CDS_Contact_ID__c = '{user['user_id']}' LIMIT 1"
    contact = query_one(session, query)
    return contact["Id"] if contact else add_contact(session, user)


def get_session(username, password, security_token, domain):
    """
    Get a Salesforce session
    """
    session = requests.Session()
    session.mount("https://", TimeoutAdapter())
    session.mount("http://", TimeoutAdapter())

    return Salesforce(
        client_id="Notify",
        username=username,
        password=password,
        security_token=security_token,
        domain=domain,
        session=session,
    )


def get_name_parts(full_name):
    """
    Get the first and last name parts from the given full name.
    If the name cannot be split, the first name will be blank and the last name will be set to the passed in full name.
    """
    name_parts = full_name.split()
    return {
        "first": name_parts[0] if len(name_parts) > 1 else "",
        "last": " ".join(name_parts[1:]) if len(name_parts) > 1 else full_name,
    }


def parse_result(result, operation):
    """
    Parse a Salesforce API result object and log the result
    """
    is_success = (
        200 <= result <= 299
        if isinstance(result, int)
        else result.get("success", False)
    )
    if is_success:
        logging.info(f"✅ {operation} succeeded")
    else:
        logging.error(f"❌ {operation} failed: {result}")
    return is_success


def query_one(session, query):
    """
    Execute an SOQL query that expects to return a single record.
    """
    results = session.query(query)
    return results.get("records")[0] if results.get("totalSize") == 1 else None


def query_param_sanitize(param):
    """Escape single quotes from parameters that will be used in
    SOQL queries since these can cause injection attacks.
    """
    return param.replace("'", r"\'")


if __name__ == "__main__":
    main()
