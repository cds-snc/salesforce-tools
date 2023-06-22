# pylint: disable=import-error,line-too-long,missing-function-docstring,missing-module-docstring
from unittest.mock import call, patch, MagicMock

from script import (
    add_contact,
    add_engagement_contact_role,
    get_contact_id,
    get_engagement_contact_role,
    get_engagement_id,
    get_name_parts,
    main,
    query_one,
    query_param_sanitize,
    parse_result,
    update_contact,
    LOGIN_USERNAME,
    LOGIN_PASSWORD,
    LOGIN_SECURITY_TOKEN,
    LOGIN_DOMAIN,
    REQUEST_HEADERS,
)


@patch("script.open")
@patch("script.add_engagement_contact_role")
@patch("script.get_contact_id", side_effect=["9", "8"])
@patch("script.get_engagement_id", side_effect=[{"Id": "1", "AccountId": "2"}, None])
@patch("script.get_engagement_contact_role", side_effect=[False, {"Id": "9"}])
@patch("script.get_session", return_value="session")
def test_main(
    mock_session,
    mock_get_engagement_contact_role,
    mock_get_engagement_id,
    mock_get_contact_id,
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
        ]
    )
    mock_get_engagement_contact_role.assert_has_calls(
        [
            (("session", "1", "9"),),
            (("session", "1", "8"),),
        ]
    )
    mock_add_engagement_contact_role.assert_has_calls(
        [
            (("session", "1", "9"),),
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


def test_update_contact():
    mock_session = MagicMock()
    user = {
        "user_id": "user_id",
        "user_name": "Frodo Baggins",
        "user_email": "frodo@fellowship.org",
        "account_id": "account_id",
    }
    update_contact(mock_session, "3", user)
    mock_session.Contact.update.assert_called_once_with(
        "3",
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
    assert get_engagement_id(mock_session, service) == {"Id": "7", "AccountId": "8"}
    mock_query_one.assert_called_once_with(
        mock_session,
        "SELECT Id, Name, ContactId, AccountId FROM Opportunity where CDS_Opportunity_Number__c = '12345' LIMIT 1",
    )


@patch("script.query_one", return_value=None)
def test_get_engagement_id_create(mock_query_one):
    mock_session = MagicMock()
    service = {"service_id": "12345"}
    assert get_engagement_id(mock_session, service) is None


@patch("script.update_contact")
@patch("script.query_one", return_value={"Id": "11"})
def test_get_contact_id_existing(mock_query_one, mock_update_contact):
    mock_session = MagicMock()
    user = {"user_id": "54321", "user_email": "foo@bar.com"}
    assert get_contact_id(mock_session, user) == "11"
    mock_update_contact.assert_called_once_with(mock_session, "11", user)
    mock_query_one.assert_called_once_with(
        mock_session,
        "SELECT Id, FirstName, LastName, AccountId FROM Contact WHERE CDS_Contact_ID__c = '54321' OR Email = 'foo@bar.com' LIMIT 1",
    )


@patch("script.query_one", return_value=None)
@patch("script.add_contact", return_value="12")
def test_get_contact_id_create(mock_add_contact, mock_query_one):
    mock_session = MagicMock()
    user = {"user_id": "54321", "user_email": "foo@bar.com"}
    assert get_contact_id(mock_session, user) == "12"
    mock_add_contact.assert_called_once_with(mock_session, user)


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
