#!/usr/bin/env python3
from __future__ import print_function

import copy
import datetime
import getopt
import pickle
import os.path
import os
import sys

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pandas as pd

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '19Rc6b7x1BtYy4Uxf77mbcc-g-Cx4hQQVfUgVWU5cuEY'
SAMPLE_RANGE_NAME = 'iglinks!A:C'


def main():
    """Shows basic usage of the Sheets API.
    Prints rows from a sample spreadsheet.
    """

    path = evaluate_args()

    sheet = open_gsheet()

    parse_and_update(sheet, path)


def update_htaccess(link, path):
    """ Determine if the .htaccess file exists at the given path if not error and quit
        Does the htaccess contain are start/stop markers? If not, append them to the end of the file.
        Insert our redirect between the markers.
        Close the file"""

    START_REDIRECT = '## BEGIN IGUPDATER'
    END_REDIRECT = '## END IGUPDATER'
    REDIRECT = 'Redirect 302 /instagram-profile '
    keep_line = True
    htaccess = ".htaccess"
    filepath = path + htaccess
    new_htaccess = ''
    SPACER = '-------\n\n'
    print('The complete file path is: ' + filepath)

    # put existing htaccess in a list called lines
    with open(filepath, 'r') as file:
        lines = file.readlines()
    print(SPACER)
    print('The original file lines:')
    for line in lines:
        print(line.strip())
    print(SPACER)
    # Strip out the existing redirect and tags from the lines list
    for line in lines:
        if line.strip() == START_REDIRECT:
            # trash the start redirect tag
            keep_line = False
        if keep_line:
            # keep exiting lines when keep_line is true
            new_htaccess += line
        if line.strip() == END_REDIRECT:
            # trash the end redirect tag
            keep_line = True
    print(SPACER)
    print('The interim htaccess string:')
    print(new_htaccess)

    # now append our new redirect to the end
    new_redirect = START_REDIRECT + '\n' + REDIRECT + link + '\n' + END_REDIRECT + '\n'
    new_htaccess += new_redirect

    print('The final htaccess file:')
    print(new_htaccess)

    with open(filepath, 'w') as file:
        for line in new_htaccess:
            file.write(line)

def parse_and_update(sheet, path):
    """ This method will make sure that:
            all date/time groups are valid and marked updated as applicable
            all links are valid (at least validly formed)
        Then it will find the row that contains the link to update/add to .htaccess

    """

    # Code to follow
    right_now = datetime.datetime.now()
    past = list(filter(lambda x: x < right_now, sheet['Date']))
    most_recent_past = past[len(past) - 1]
    link = sheet.loc[sheet['Date'].eq(most_recent_past).idxmax(), 'Profile Link']
    print('The link to add to htaccess is: ', link)
    # after finding the right row
    update_htaccess(link, path)


def open_gsheet():
    """ Opens the sheet from google and sorts it by date, then time.
    Returns a pandas dataframe"""

    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('./secrets/token.pickle'):
        with open('./secrets/token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.path.dirname(sys.argv[0]) + './secrets/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(os.path.dirname(sys.argv[0]) + '/secrets/token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('sheets', 'v4', credentials=creds)
    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range=SAMPLE_RANGE_NAME).execute()
    rows = result.get('values', [])
    if not rows:
        print('No data found.')
    # else:
    #     for row in rows:
    #         # Print columns A -C , which correspond to indices 0 - 2.
    #         print('%s, %s, %s' % (row[0], row[1], row[2]))

    # covert to pandas dataframe
    df = pd.DataFrame(rows[1:], columns=rows[0])
    pd.set_option("display.max_rows", None, "display.max_columns", None)
    # print(df)
    df['Date'] = pd.to_datetime(df.Date)
    # df['Time'] = pd.to_datetime(df.Time)
    df.sort_values(by=['Date'], inplace=True)
    # print(df)
    return df


def evaluate_args():
    path = ''
    usageMessage = 'Usage: updateIGLink.py -p <path to .htaccess>'
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hp:", "path=")
        print(sys.argv)
    except getopt.GetoptError:
        print(usageMessage)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(usageMessage)
            sys.exit()
        elif opt in ("-p", "--path"):
            path = arg
            print('Path given for .htaccess is %s' % path)
        else:
            print('A path to htaccess must be provided.')
            print(usageMessage)
            sys.exit(2)
    return path


#    links = pd.read_csv('https://docs.google.com/spreadsheets/d/19Rc6b7x1BtYy4Uxf77mbcc-g-Cx4hQQVfUgVWU5cuEY/export?format=csv')
if __name__ == '__main__':
    main()
