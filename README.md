# Aconex Mail Data Query

This program simplifies the process of querying Aconex web services to retrieve project mail data across a portfolio of projects for a single user. Specifically, it retrieves all projects for a user using the Projects API and passes these to the Mail API to retrieve up to 250 project mails per day per project and stores them locally in a csv file. By default up to 11 mail field/value pairs will be retrieved. Users can set the data range for the search window to limit the size of the data requests. For larger projects a shorter search window is suggested.  

### Prerequisites:
Please note that you’ll need Organisation Admin rights in Aconex and an API Authorisation Code for your organisation from Aconex to run this query. Sensitive data will be stored in an environment file.

### Set up Aconex: 
First log into Aconex as Organisation Admin and go to ‘User Role Configuration’ under setup and grant ‘Web Services API’ access for the appropriate user group within your organisation. 

Then create an API User account on Aconex and add this user to all of the projects in the portfolio of interest. Finally, go into ‘User Role Assignment’ and ensure that the API User is added to the user group with ‘Web Services API’ access.

### Setting up and Running the Query: 
Enter the search date range for the query using the date fields. For the initial query its recommended that you run a single day to make sure that everything is working correctly.

Then enter the API Credentials for the API User and the API Authorisation Code from Aconex. 

### Running the query
Go to 'Runtime' and select 'Run all'. 

Also, please note that the API queries can take a while to run depending on the search window selected.
 
Once completed save a local copy of the temporary csv file to access the retrieved data.
 
## Authors:
@egekaplan <br>
Thanks to @AddVennture
