#!/usr/bin/python -u
#
# The -u specified not output buffering which is tee-friendly.
#----------------------------------------------------
# a simple JIRA custom field value migrator.
# version 4, updated September 27, 2017.
# writte by Tin K Nguyen
#----------------------------------------------------


import json
import requests
import sys
import source_jira_creds
import destination_jira_creds

# Disable SSL warnings
requests.packages.urllib3.disable_warnings()

from requests.auth import HTTPBasicAuth

ISSUE_TYPE = "issuetype"

#Source Field Configuration
SOURCE_REQUESTOR = "customfield_10101"
SOURCE_ROUGH_ESTIMATE = "customfield_11000"
SOURCE_QA_PRIORITY = "customfield_11202"
SOURCE_SEVERITY = "customfield_10100"


SOURCE_FIELDS = [SOURCE_REQUESTOR,SOURCE_ROUGH_ESTIMATE,SOURCE_QA_PRIORITY,SOURCE_SEVERITY]
SOURCE_FIELDS_STR = ",".join(SOURCE_FIELDS)

#Destination Field Configuration
DESTINATION_REQUESTOR = "customfield_19989"
DESTINATION_ROUGH_ESTIMATE = "customfield_19993"
DESTINATION_QA_PRIORITY = "customfield_19985"
DESTINATION_SEVERITY = "customfield_19998"


DESTINATION_FIELDS = [DESTINATION_REQUESTOR,DESTINATION_ROUGH_ESTIMATE,DESTINATION_QA_PRIORITY,DESTINATION_SEVERITY]
DESTINATION_FIELDS_STR = ",".join(DESTINATION_FIELDS)

def get_source_meta():
    "Returns meta data that includes custom field names and ID used above."
    auth = HTTPBasicAuth(migrate_jira_creds.username, migrate_jira_creds.password)
    url = "{source_url}/rest/api/2/issue/createmeta?expand=projects.issuetypes.fields".format(**vars())
    r = requests.get(url=url, verify=False, auth=auth)
    issue = json.loads(r.text)
    print 'Response: {}'.format(json.dumps(issue, indent=4))

def get_dest_meta():
    "Returns meta data that includes custom field names and ID used above."
    auth = HTTPBasicAuth(DESTINATION_jira_creds.username, DESTINATION_jira_creds.password)
    url = "{destination_url}/rest/api/2/issue/createmeta?projectKeys=DS&expand=projects.issuetypes.fields".format(**vars())
    r = requests.get(url=url, verify=False, auth=auth)
    issue = json.loads(r.text)
    print 'Response: {}'.format(json.dumps(issue, indent=4))

def get_source_issue(issue):
    auth = HTTPBasicAuth(migrate_jira_creds.username, migrate_jira_creds.password)
    url = '{source_url}/rest/api/2/issue/'.format(**vars()) + issue + '?fields=' + SOURCE_FIELDS_STR
    r = requests.get(url=url, verify=False, auth=auth)
    if r.status_code == 404:
        print "Source Issue {} NOT FOUND: {}".format(issue, r.text)
        return None
    elif r.status_code == 403:
        print "Source Issue {} FORBIDDEN: {}".format(issue, r.text)
        return None
    elif r.status_code != 200:
        r.raise_for_status()
    source_issue = json.loads(r.text)
    return source_issue

def get_dest_issue(issue):
    auth = HTTPBasicAuth(DESTINATION_jira_creds.username, DESTINATION_jira_creds.password)
    url = "{destination_url}/rest/api/2/issue/".format(**vars()) + issue + '?fields=' + DESTINATION_FIELDS_STR
    r = requests.get(url=url, verify=False, auth=auth)
    if r.status_code == 404:
        print "DESTINATION Issue {} NOT FOUND: {}".format(issue, r.text)
        return None
    elif r.status_code != 200:
        r.raise_for_status()
    dest_issue = json.loads(r.text)
    return dest_issue

def update_dest_fields(source_issue, dest_issue):
    source_fields=source_issue['fields']
    dest_fields=dest_issue['fields']
    update_fields={}

    #### These are drop-down widgets so setting the value here has different rules. ####

        #QA_Priority
    if source_fields[SOURCE_QA_PRIORITY] is None:
        if not dest_fields[DESTINATION_QA_PRIORITY] is None:
            update_fields[DESTINATION_QA_PRIORITY]=None
    elif dest_fields[DESTINATION_QA_PRIORITY] is None or source_fields[SOURCE_QA_PRIORITY]['value'] != dest_fields[DESTINATION_QA_PRIORITY]['value']:
        update_fields[DESTINATION_QA_PRIORITY]={'value': str(source_fields[SOURCE_QA_PRIORITY]['value'])}

        #Severity
    if source_fields[SOURCE_SEVERITY] is None:
        if not dest_fields[DESTINATION_SEVERITY] is None:
            update_fields[DESTINATION_SEVERITY]=None
    elif dest_fields[DESTINATION_SEVERITY] is None or source_fields[SOURCE_SEVERITY]['value'] != dest_fields[DESTINATION_SEVERITY]['value']:
        update_fields[DESTINATION_SEVERITY]={'value': str(source_fields[SOURCE_SEVERITY]['value'])}

        ####NO DROP DOWNS####

        #Requestor
     #Value is a simple array.
    if source_fields[SOURCE_REQUESTOR] != dest_fields[DESTINATION_REQUESTOR]:
        update_fields[DESTINATION_REQUESTOR]= source_fields[SOURCE_REQUESTOR]

        #Rough_Estimate
     #Value is a simple number.
    if source_fields[SOURCE_ROUGH_ESTIMATE] != dest_fields[DESTINATION_ROUGH_ESTIMATE]:
        update_fields[DESTINATION_ROUGH_ESTIMATE]= source_fields[SOURCE_ROUGH_ESTIMATE]



    if bool(update_fields):
        #print "Issue {} needs update ..... ".format(source_issue['key'])
        update_data = { 'fields': update_fields }
        auth = HTTPBasicAuth(DESTINATION_jira_creds.username, DESTINATION_jira_creds.password)
        url = "{destination_url}/rest/api/2/issue/".format(**vars()) + source_issue['key']
        #print "Data: {}".format(json.dumps(update_data, indent=4))
        r = requests.put(json=update_data, url=url, verify=False, auth=auth)
        print "Issue {} needs update ..... {}".format(source_issue['key'], r.status_code)
        if r.status_code == 404:
            print "Issue {} NOT FOUND: {}".format(source_issue['key'], r.text)
        elif r.status_code == 400:
            print "Cannot change....{}:  {}".format(source_issue['key'], r.text)
        elif r.status_code != 204:
            print r.text
            r.raise_for_status()
    else:
        print "Issue {} is up to date".format(source_issue['key'])

            #### Issue Type Configuration ####
    # you can have multiple issue types it will apply to
    # or you can use a single one.
    # the purpose is incase of workflow restrictions based on issue type.

def migrate(issue):
    source_issue = get_source_issue(issue)
    if not source_issue is None:
        issue_num  = source_issue['key']
        issue_type = source_issue['fields']['issuetype']['name']
        if issue_type == 'Enhancement' or issue_type == 'Feature':
        #if issue_type == 'Defect':
        #if issue_type == 'Epic':
        #if issue_type == 'Documentation':
        #if issue_type == 'Release Note':
        #if issue_type == 'QA Validation':

            dest_issue = get_dest_issue(issue)
            if not dest_issue is None:
                update_dest_fields(source_issue, dest_issue)
        else:
            print 'Issue {} is {}, no action taken.'.format(issue_num, issue_type)

            #### Range Control ####
            # Project Key Config #
def main():
    print "Issue: {}".format(sys.argv[1])
    if sys.argv[1] is None:
        print "Usage:  script [issue number]"
    elif sys.argv[1] == "ALL":
         for x in range(0, 100):

             #Change the project KEY below keeping the '-'
            migrate('JRA-' + str(x))
             #^^^^^^^^^^^^^^^^^^^^^^

    else:
        migrate(sys.argv[1])

if __name__ == "__main__":
    main()
    # get_field_data()def get_dest_issue():
