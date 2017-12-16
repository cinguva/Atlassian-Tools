#Custom Field Migrator JIRA (between instances)#



You will need to define the custom fields you want and find the custom field ID within JIRA.
Modify the source field based on all of the custom fields you want to implement

#WARNING#
This is doing everything via API so if you run into a problem its more then likely a permissions or some other constraint
within JIRA.

You will need to have authentication between Source and Destination JIRA and you will modify the two via API so update the
URL's accordingly.

#Getting Custom Field ID's#
You will need to navigate in JIRA's custom fields configuration page and click on configure the custom field you are interested in. Within the URL of the page you will see the customfield ID. follow the syntax as present on the main script.

#Configuring Ticket range
On Line 170 you will need to adjust the Ticket number range. Keep in mind that Python numbering works so if you want to complete a run of 1 - 10 you will need to assign a value of 0 to start and 11 to finish. The loop stops at 11 with this config meaning that up to 10 was applied.

example:

for x in range(0, 101):

will complete from 1-100

#Configuring Project key
On line 173 you will need to configure the project key for the JIRA project we are focusing on the field migrator. you will see migrate('JRA-' + str(x)) and you will need to update the section that says JRA- with your according project key.


#Running the script
python migrate_jira.py ALL
