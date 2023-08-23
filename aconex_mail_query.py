import requests as rq
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import csv
import os

from dotenv import load_dotenv
load_dotenv()

#search dates YYYYMMDD
strt_date = "2023-08-18" 
end_date = "2023-08-25"

# search windows
srch_wdw = pd.date_range(strt_date, end_date)
#print(srch_wdw)

dates=[]
for day in srch_wdw:
  a = str(day)[0:10] # taking at most 10 chars of day in search windows
  b = a.replace('-','') # removing hyphens from dates
  dates.append(b) # adding into list 
print(f"DATES: {dates} ")

# SETTING UP THE ACONEX API CONNECTION

username = os.getenv("ACONEX_USERNAME")
password = os.getenv("ACONEX_PASSWORD")
key = os.getenv("ACONEX_KEY")

b_url='https://uk1.aconex.co.uk/api/' # base path for all Aconex web services
headers={'Accept': 'application/vnd.aconex.mail.v2+xml','Authorization': f'Bearer {key}'}


# DEFINED FUNCTIIONS

def get_inmail(aconex_id,strt_date,end_date):
    
    """
    Generates a list of project mail, using "List Mail (Version 2) in the Aconex Mail API"
    """
    mailbox='inbox' #mailbox for querying, available alternatives are: inbox, sentbox, draftbox
    srch_qry=f'sentdate:[{strt_date} TO {end_date}]'
    r_fields=('corrtypeid') #check mail schema first to confirm result field availability - Available options: subject,sentdate,responsedate
    s_field='sentdate' #results sorted by correspondence type 
    data=rq.get(
      f'https://uk1.aconex.co.uk/api/projects/{aconex_id}/mail',
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


# 
def get_outmail(aconex_id,strt_date,end_date):
    """
    Generates a list of project mail, using "List Mail (Version 2) in the Aconex Mail API"
    """
    mailbox='sentbox' #mailbox for querrying, available alternatives are: inbox, sentbox, draftbox
    srch_qry=f'sentdate:[{strt_date} TO {end_date}]'
    r_fields=('corrtypeid') #check mail schema first to confirm result field availability - Available options: subject,sentdate,responsedate
    s_field='sentdate' #results sorted by correspondence type 
    data=rq.get(f'https://uk1.aconex.co.uk/api/projects/{aconex_id}/mail',
                auth=(username,password),
                headers=headers,
                params=(
                  {'mail_box':mailbox,'search_query':srch_qry,'return_fields':r_fields,'sort_field':s_field}
                  ))
    root=ET.fromstring(data.text)
    return root



def get_mailmeta(aconex_id,mail_id):
    """
    GETS metadata for individual mails using 'View Mail Metadata (V2)'
    """
    data=rq.get(f'https://uk1.aconex.co.uk/api/projects/{aconex_id}/mail/{mail_id}',
                auth=(username,password),
                headers=headers)
    #root=ET.fromstring(data.text)
    return data


def prj_mails(mail_root):
  """
  creates a dictionary of mail ids for a project
  """
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
prj_headers={'User':username,'Authorization': f'Bearer {key}'}
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
