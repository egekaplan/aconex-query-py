import requests as rq
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import csv
import os


# # Import PyDrive and associated libraries.
# from pydrive.auth import GoogleAuth
# from pydrive.drive import GoogleDrive
# from oauth2client.client import GoogleCredentials
from dotenv import load_dotenv

load_dotenv()

#search dates
strt_date = "2021-02-01" 
end_date = "2021-02-6"

# search windows
srch_wdw = pd.date_range(strt_date, end_date)
#print(srch_wdw)

dates=[]
for day in srch_wdw:
  a = str(day)[0:10] # taking at most 10 chars of day in search windows
  b = a.replace('-','') # removing hyphens from dates
  dates.append(b) # adding into list 
#print(dates)

# SETTING UP THE ACONEX API CONNECTION

username = os.getenv("ACONEX_USERNAME")
password = os.getenv("ACONEX_PASSWORD")
key = os.getenv("ACONEX_KEY")

b_url='https://uk1.aconex.co.uk/api/' # base path for all Aconex web services
headers={'Accept': 'application/vnd.aconex.mail.v2+xml','Authorization': 'Bearer {0}'.format(key)}


# DEFINED FUNCTIIONS

# Generates a list of project mail, using "List Mail (Version 2) in the Aconex Mail API"
def get_inmail(aconex_id,strt_date,end_date):
    mailbox='inbox' #mailbox for querying, available alternatives are: inbox, sentbox, draftbox
    srch_qry='sentdate:[{0} TO {1}]'.format(strt_date,end_date)
    r_fields=('corrtypeid') #check mail schema first to confirm result field availability - Available options: subject,sentdate,responsedate
    s_field='sentdate' #results sorted by correspondence type 
    data=rq.get(
      'https://uk1.aconex.co.uk/api/projects/{0}/mail'.format(aconex_id),
                auth=(username,password),
                headers=headers,
                params=({
                          'mail_box':mailbox,
                          'search_query':srch_qry,
                          'return_fields':r_fields,
                          'sort_field':s_field
                        })
       )
    root=ET.fromstring(data.text)
    return root


# Generates a list of project mail, using "List Mail (Version 2) in the Aconex Mail API"
def get_outmail(aconex_id,strt_date,end_date):
    mailbox='sentbox' #mailbox for querrying, available alternatives are: inbox, sentbox, draftbox
    srch_qry='sentdate:[{0} TO {1}]'.format(strt_date,end_date)
    r_fields=('corrtypeid') #check mail schema first to confirm result field availability - Available options: subject,sentdate,responsedate
    s_field='sentdate' #results sorted by correspondence type 
    data=rq.get('https://uk1.aconex.co.uk/api/projects/{0}/mail'.format(aconex_id),auth=(username,password),headers=headers,params=({'mail_box':mailbox,'search_query':srch_qry,'return_fields':r_fields,'sort_field':s_field}))
    root=ET.fromstring(data.text)
    return root



# GETS metadata for individual mails using 'View Mail Metadata (V2)'
def get_mailmeta(aconex_id,mail_id):
    data=rq.get('https://uk1.aconex.co.uk/api/projects/{0}/mail/{1}'.format(aconex_id,mail_id),auth=(username,password),headers=headers)
    #root=ET.fromstring(data.text)
    return data


# Function creates a dictionary of mail ids for a project
def prj_mails(mail_root):
  prj_mails={}
  counter=0
  for mail in mail_root.findall('.//Mail'):
    prj_mails[counter]=mail.attrib
    counter=counter+1
  return prj_mails


# THIS FUNCTION CAPTURES SOME OF THE AVAILABLE #Option to permanently save temporary csv file to Google Drive.
# Note requires authentication in Section 3.
def maildata3(mailmeta_root):
  try:
    prj_id=mailmeta_root.find('ProjectId').text
  except:
    prj_id='NONE'
  try:
    corrtype=mailmeta_root.find('CorrespondenceType').text
  except:
    corrtype='NONE'
  try:
    sentdate=mailmeta_root.find('SentDate').text
  except:
    sentdate='NONE'
  try:
    status=mailmeta_root.find('Status').text
  except:
    status='NONE'
  try:
    subject=mailmeta_root.find('Subject').text
  except:
    subject='NONE'
  try:
    mailthread=mailmeta_root.find('ThreadId')
  except:
    mailthread='NONE'

  mail=mailmeta_root.attrib['MailId']

  coredata=[prj_id,mail,sentdate,corrtype,subject,status,mailthread]

  for mff in mailmeta_root.findall('.//MailFormField'):
      coredata.append(mff.find('Label').text)
      coredata.append(mff.find('Value').text)
  return coredata


# GETTING LIST OF PROJECTS


#Running project search query and retrieving project list for user.
prj_headers={'User':username,'Authorization': 'Bearer {0}'.format(key)}
prj_data=rq.get('https://uk1.aconex.co.uk/api/projects',auth=(username,password),headers=prj_headers)
prj_root=ET.fromstring(prj_data.text) #Bringing data into element tree for processing
#[elem.tag for elem in prj_root.iter()] #Optional step to check data structure
#prj_root.attrib #Check on total number of projects 


# Generating a list of project ids for mail search queries.
prj_ids=[]
for child in prj_root.iter('ProjectId'):
    prj_ids.append(child.text)


# FETCHING & SAVING MAIL DATA

# Opening temporary csv file to write data out to. 
with open('TEMP_DATA.csv',mode='w') as csvfile:
    csvwriter=csv.writer(csvfile)


# Getting data for all INBOX mails on all projects for the search date range and writting them to a csv file
# Note depending on the size of the query this may take a while to run.
for day in dates:
  for prj_id in prj_ids:
    mails=get_inmail(prj_id,day,day) 
    p_mails=prj_mails(mails)
    #print(p_mails)
    counter=0
    for mail in p_mails:
      mail_id=p_mails[counter]['MailId']
      #print(prj_id,mail_id)
      metadata=get_mailmeta(prj_id,mail_id)
      mailmeta_root=ET.fromstring(metadata.text)
      md=maildata3(mailmeta_root)
      df=pd.DataFrame(md)
      dft=df.transpose()
      dft.to_csv('TEMP_DATA.csv',header=False,mode='a')
      counter=counter+1
      #print(md)


# Getting data for all SENT mails on all projects for the search date range and adding them to the AGM_data.csv file
# Note depending on the size of the query this may take a while to run.
for day in dates:
  for prj_id in prj_ids:
    mails=get_outmail(prj_id,day,day) 
    p_mails=prj_mails(mails)
    print(p_mails)
    counter=0
    for mail in p_mails:
      mail_id=p_mails[counter]['MailId']
      print(prj_id,mail_id)
      metadata=get_mailmeta(prj_id,mail_id)
      mailmeta_root=ET.fromstring(metadata.text)
      md=maildata3(mailmeta_root)
      df=pd.DataFrame(md)
      dft=df.transpose()
      dft.to_csv('TEMP_DATA.csv',header=False,mode='a')
      counter=counter+1
      #print(md)
