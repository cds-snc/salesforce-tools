# pylint: disable=import-error,line-too-long,missing-function-docstring,missing-module-docstring
from unittest.mock import patch, MagicMock

from script import (
    get_org_name_from_notes,
    get_account_id_from_name,
    get_name_parts,
    query_one,
    query_param_sanitize,
    parse_result,
    ORG_NOTES_ORG_NAME_INDEX,
    ORG_NOTES_OTHER_NAME_INDEX,
)


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
