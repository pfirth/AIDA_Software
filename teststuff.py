import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

def updateSheet(sheet,D):
    L = sheet.row_values(1)
    #find out if a new column needs to be added
    for coltitle in D.keys():
        if coltitle in L:
            pass
        else:#if the column title is not in the list, add it
            L.append(coltitle)

    #update columns
    num_cols = len(L)
    cells_to_update = 'A1:' +chr(ord('@')+num_cols) +'1'
    sheet.update(cells_to_update,[L])

    #building a list to update
    toupdate = []
    for coltitle in L:
        try:
            toupdate.append(D[coltitle])
        except KeyError: #if there isn't a value in the sheet
            toupdate.append('')

    #updating the values
    sheet.append_row(toupdate)

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
cred = ServiceAccountCredentials.from_json_keyfile_name('aida-update-e3da1e0863cf.json',scope)

client = gspread.authorize(cred)

D = {'Date':str(datetime.now()), 'time':2, 'Sample ID':3, 'Run ID':4,'test3':9, 'SiH4':5, 'He':6,'Test':7,'o2':60,
     'RF':5,'Pressure':5000}
try:
    sheet = client.open_by_key('1KfwftgVLMEHyujG-p6m1Kvqw07hqFSUgQVP4ldVyrN8').sheet1
    updateSheet(sheet, D)
except:
    print('No Internet!')


#



