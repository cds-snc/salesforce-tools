# pylint: disable=import-error,line-too-long,missing-function-docstring,missing-module-docstring
from datetime import date
from unittest.mock import call, patch, MagicMock

from script import (
    add_contact,
    add_engagement,
    add_engagement_contact_role,
    get_contact_id,
    get_engagement_contact_role,
    get_engagement_id,
    get_org_name_from_notes,
    get_account_id_from_name,
    get_name_parts,
    main,
    query_one,
    query_param_sanitize,
    parse_result,
    ENGAGEMENT_PRODUCT,
    ENGAGEMENT_PRODUCT_ID,
    ENGAGEMENT_RECORD_TYPE,
    ENGAGEMENT_STAGE_LIVE,
    ENGAGEMENT_STANDARD_PRICEBOOK_ID,
    ENGAGEMENT_TEAM,
    ENGAGEMENT_TYPE,
    LOGIN_USERNAME,
    LOGIN_PASSWORD,
    LOGIN_SECURITY_TOKEN,
    LOGIN_DOMAIN,
    ORG_NOTES_ORG_NAME_INDEX,
    ORG_NOTES_OTHER_NAME_INDEX,
    REQUEST_HEADERS,
)


@patch("script.open")
@patch("script.add_engagement_contact_role")
@patch("script.get_account_id_from_name", return_value="account_id")
@patch("script.get_contact_id", side_effect=["9", "8", "7"])
@patch("script.get_engagement_id", side_effect=[("1", "2"), ("3", "4")])
@patch("script.get_engagement_contact_role", side_effect=[False, False, {"Id": "9"}])
@patch("script.get_session", return_value="session")
def test_main(
    mock_session,
    mock_get_engagement_contact_role,
    mock_get_engagement_id,
    mock_get_contact_id,
    mock_get_account_id_from_name,
    mock_add_engagement_contact_role,
    mock_open,
):
    mock_open.return_value.__enter__.return_value = [
        "service_id,service_name,service_organisation_notes,service_restricted,user_id,user_name,user_email",
        "4d3185a7-f0dc-44c0-a54a-8af37640562f,some name,Treasury Board Secretariat,true,35645d50-3ff2-4777-81ea-31dc62d0c3dc,Jane Doe,jane.doe@tbs-sct.gc.ca",
        "4d3185a7-f0dc-44c0-a54a-8af37640562f,some name,Treasury Board Secretariat,true,378cda53-2479-40f9-941c-db57b33e75d4,Jimmy Doe,jimmy.doe@tbs-sct.gc.ca",
        "092a1718-8579-4367-a758-7cd0c566a21d,another name,National Defence > Air Cadets,false,06c1c666-e75b-4a67-9689-f42019492e62,John Doe,john.doe@forces.gc.ca",
    ]
    main()

    mock_session.assert_called_once_with(
        LOGIN_USERNAME, LOGIN_PASSWORD, LOGIN_SECURITY_TOKEN, LOGIN_DOMAIN
    )
    mock_get_account_id_from_name.assert_has_calls(
        [
            (("session", "Treasury Board Secretariat", "4"),),
            (("session", "National Defence", "4"),),
        ]
    )
    mock_get_engagement_id.assert_has_calls(
        [
            call(
                "session",
                {
                    "service_id": "4d3185a7-f0dc-44c0-a54a-8af37640562f",
                    "service_name": "some name",
                    "service_organisation_notes": "Treasury Board Secretariat",
                    "service_restricted": "true",
                    "user_id": "35645d50-3ff2-4777-81ea-31dc62d0c3dc",
                    "user_name": "Jane Doe",
                    "user_email": "jane.doe@tbs-sct.gc.ca",
                    "account_id": "2",
                },
            ),
            call(
                "session",
                {
                    "service_id": "092a1718-8579-4367-a758-7cd0c566a21d",
                    "service_name": "another name",
                    "service_organisation_notes": "National Defence > Air Cadets",
                    "service_restricted": "false",
                    "user_id": "06c1c666-e75b-4a67-9689-f42019492e62",
                    "user_name": "John Doe",
                    "user_email": "john.doe@forces.gc.ca",
                    "account_id": "4",
                },
            ),
        ]
    )
    mock_get_contact_id.assert_has_calls(
        [
            call(
                "session",
                {
                    "service_id": "4d3185a7-f0dc-44c0-a54a-8af37640562f",
                    "service_name": "some name",
                    "service_organisation_notes": "Treasury Board Secretariat",
                    "service_restricted": "true",
                    "user_id": "35645d50-3ff2-4777-81ea-31dc62d0c3dc",
                    "user_name": "Jane Doe",
                    "user_email": "jane.doe@tbs-sct.gc.ca",
                    "account_id": "2",
                },
            ),
            call(
                "session",
                {
                    "service_id": "4d3185a7-f0dc-44c0-a54a-8af37640562f",
                    "service_name": "some name",
                    "service_organisation_notes": "Treasury Board Secretariat",
                    "service_restricted": "true",
                    "user_id": "378cda53-2479-40f9-941c-db57b33e75d4",
                    "user_name": "Jimmy Doe",
                    "user_email": "jimmy.doe@tbs-sct.gc.ca",
                    "account_id": "2",
                },
            ),
            call(
                "session",
                {
                    "service_id": "092a1718-8579-4367-a758-7cd0c566a21d",
                    "service_name": "another name",
                    "service_organisation_notes": "National Defence > Air Cadets",
                    "service_restricted": "false",
                    "user_id": "06c1c666-e75b-4a67-9689-f42019492e62",
                    "user_name": "John Doe",
                    "user_email": "john.doe@forces.gc.ca",
                    "account_id": "4",
                },
            ),
        ]
    )
    mock_get_engagement_contact_role.assert_has_calls(
        [
            (("session", "1", "9"),),
            (("session", "1", "8"),),
            (("session", "3", "7"),),
        ]
    )
    mock_add_engagement_contact_role.assert_has_calls(
        [
            (("session", "1", "9"),),
            (("session", "1", "8"),),
        ]
    )


def test_add_contact():
    mock_session = MagicMock()
    mock_session.Contact.create.return_value = {"id": "1", "success": True}
    user = {
        "user_id": "user_id",
        "user_name": "Frodo Baggins",
        "user_email": "frodo@fellowship.org",
        "account_id": "account_id",
    }
    assert add_contact(mock_session, user) == "1"
    mock_session.Contact.create.assert_called_once_with(
        {
            "FirstName": "Frodo",
            "LastName": "Baggins",
            "Title": "created by Notify API",
            "CDS_Contact_ID__c": user["user_id"],
            "Email": user["user_email"],
            "AccountId": user["account_id"],
        },
        headers=REQUEST_HEADERS,
    )


@patch("script.datetime", return_value="1954-07-29")
def test_add_engagement(mock_datetime):
    mock_datetime.today.return_value = date(1954, 7, 29)
    mock_session = MagicMock()
    mock_session.Opportunity.create.return_value = {"id": "2", "success": True}
    mock_session.OpportunityLineItem.create.return_value = {"success": True}
    service = {
        "service_name": "The Fellowship of the Ring",
        "account_id": "42",
        "service_id": "12345",
        "service_organisation_notes": "Fellowship > The Hobbits",
        "service_restricted": "false",
    }
    assert add_engagement(mock_session, service) == ("2", "42")
    mock_session.Opportunity.create.assert_called_once_with(
        {
            "Name": service["service_name"][:120],
            "AccountId": service["account_id"],
            "CDS_Opportunity_Number__c": service["service_id"],
            "Notify_Organization_Other__c": "The Hobbits",
            "CloseDate": "1954-07-29",
            "RecordTypeId": ENGAGEMENT_RECORD_TYPE,
            "StageName": ENGAGEMENT_STAGE_LIVE,
            "Type": ENGAGEMENT_TYPE,
            "CDS_Lead_Team__c": ENGAGEMENT_TEAM,
            "Product_to_Add__c": ENGAGEMENT_PRODUCT,
        },
        headers=REQUEST_HEADERS,
    )
    mock_session.OpportunityLineItem.create.assert_called_once_with(
        {
            "OpportunityId": "2",
            "PricebookEntryId": ENGAGEMENT_STANDARD_PRICEBOOK_ID,
            "Product2Id": ENGAGEMENT_PRODUCT_ID,
            "Quantity": 1,
            "UnitPrice": 0,
        },
        headers=REQUEST_HEADERS,
    )


def test_add_engagement_contact_role():
    mock_session = MagicMock()
    mock_session.OpportunityContactRole.create.return_value = {"success": True}
    add_engagement_contact_role(mock_session, "1", "2")
    mock_session.OpportunityContactRole.create.assert_called_once_with(
        {
            "ContactId": "2",
            "OpportunityId": "1",
        },
        headers=REQUEST_HEADERS,
    )


@patch("script.query_one", return_value={"Id": "42"})
def test_get_engagement_contact_role(mock_query_one):
    mock_session = MagicMock()
    assert get_engagement_contact_role(mock_session, "1", "2") == {"Id": "42"}
    mock_query_one.assert_called_once_with(
        mock_session,
        "SELECT Id, OpportunityId, ContactId FROM OpportunityContactRole WHERE OpportunityId = '1' AND ContactId = '2' LIMIT 1",
    )


@patch("script.query_one", return_value={"Id": "7", "AccountId": "8"})
def test_get_engagement_id_existing(mock_query_one):
    mock_session = MagicMock()
    service = {"service_id": "12345"}
    assert get_engagement_id(mock_session, service) == ("7", "8")
    mock_query_one.assert_called_once_with(
        mock_session,
        "SELECT Id, Name, ContactId, AccountId FROM Opportunity where CDS_Opportunity_Number__c = '12345' LIMIT 1",
    )


@patch("script.query_one", return_value=None)
@patch("script.add_engagement", return_value=("9", "10"))
def test_get_engagement_id_create(mock_add_engagement, mock_query_one):
    mock_session = MagicMock()
    service = {"service_id": "12345"}
    assert get_engagement_id(mock_session, service) == ("9", "10")
    mock_add_engagement.assert_called_once_with(mock_session, service)


@patch("script.query_one", return_value={"Id": "11"})
def test_get_contact_id_existing(mock_query_one):
    mock_session = MagicMock()
    user = {"user_id": "54321"}
    assert get_contact_id(mock_session, user) == "11"
    mock_query_one.assert_called_once_with(
        mock_session,
        "SELECT Id, FirstName, LastName, AccountId FROM Contact WHERE CDS_Contact_ID__c = '54321' LIMIT 1",
    )


@patch("script.query_one", return_value=None)
@patch("script.add_contact", return_value="12")
def test_get_contact_id_create(mock_add_contact, mock_query_one):
    mock_session = MagicMock()
    user = {"user_id": "54321"}
    assert get_contact_id(mock_session, user) == "12"
    mock_add_contact.assert_called_once_with(mock_session, user)


def test_get_org_name_from_notes():
    assert (
        get_org_name_from_notes(
            "Account Name 1 > Service Name", ORG_NOTES_ORG_NAME_INDEX
        )
        == "Account Name 1"
    )
    assert (
        get_org_name_from_notes(
            "Account Name 2 > Another service Name", ORG_NOTES_ORG_NAME_INDEX
        )
        == "Account Name 2"
    )
    assert (
        get_org_name_from_notes(
            "Account Name 3 > Some service", ORG_NOTES_OTHER_NAME_INDEX
        )
        == "Some service"
    )
    assert (
        get_org_name_from_notes("Account Name 4 > Service Name > Team Name", 2)
        == "Team Name"
    )
    assert get_org_name_from_notes(None, 0) is None
    assert get_org_name_from_notes(">", 0) == ""


@patch("script.query_one", return_value={"Id": "account_id"})
def test_get_account_id_from_name(mock_query_one):
    mock_session = MagicMock()
    assert (
        get_account_id_from_name(mock_session, "Account Name", "generic_account_id")
        == "account_id"
    )
    mock_query_one.assert_called_with(
        mock_session,
        "SELECT Id FROM Account where Name = 'Account Name' OR CDS_AccountNameFrench__c = 'Account Name' LIMIT 1",
    )


@patch("script.query_one", return_value=None)
def test_get_account_id_from_name_generic(mock_query_one):
    mock_session = MagicMock()
    assert (
        get_account_id_from_name(mock_session, "l'account", "generic_account_id")
        == "generic_account_id"
    )
    mock_query_one.assert_called_with(
        mock_session,
        "SELECT Id FROM Account where Name = 'l\\'account' OR CDS_AccountNameFrench__c = 'l\\'account' LIMIT 1",
    )


def test_get_account_id_from_name_blank():
    mock_session = MagicMock()
    assert (
        get_account_id_from_name(mock_session, "", "generic_account_id")
        == "generic_account_id"
    )
    assert (
        get_account_id_from_name(mock_session, "     ", "generic_account_id")
        == "generic_account_id"
    )


def test_get_name_parts():
    assert get_name_parts("Frodo Baggins") == {"first": "Frodo", "last": "Baggins"}
    assert get_name_parts("Smaug") == {"first": "", "last": "Smaug"}
    assert get_name_parts("") == {"first": "", "last": ""}
    assert get_name_parts("Gandalf The Grey") == {
        "first": "Gandalf",
        "last": "The Grey",
    }


def test_query_one_result():
    mock_session = MagicMock()
    mock_session.query.return_value = {"totalSize": 1, "records": [{"id": "123"}]}
    assert query_one(mock_session, "some query") == {"id": "123"}
    mock_session.query.assert_called_once_with("some query")


def test_query_one_no_results():
    mock_session = MagicMock()
    mock_session.query.side_effect = [{"totalSize": 2}, {}]
    assert query_one(mock_session, "some query") is None
    assert query_one(mock_session, "some query") is None


def test_query_param_sanitize():
    assert query_param_sanitize("some string") == "some string"
    assert (
        query_param_sanitize("fancy'ish apostrophe's") == "fancy\\'ish apostrophe\\'s"
    )


def test_parse_result():
    assert parse_result(200, "int") is True
    assert parse_result(299, "int") is True
    assert parse_result(100, "int") is False
    assert parse_result(400, "int") is False
    assert parse_result(500, "int") is False
    assert parse_result({"success": True}, "dict") is True
    assert parse_result({"success": False}, "dict") is False
    assert parse_result({}, "dict") is False
