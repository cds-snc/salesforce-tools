# Notify service user sync

This script will sync Notify service users to Salesforce Contacts and Engagements.
It expects a CSV file with the following columns:
```
service_id: str
service_name: str
service_organisation_notes: str
service_restricted: true|false
user_id: str
user_name: str
user_email: str
```

## Running the script
```sh
cp .env.example .env # and add your values
make install
make
```