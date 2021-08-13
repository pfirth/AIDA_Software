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

def connectToSheet(sheetID):
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    cred = ServiceAccountCredentials.from_json_keyfile_name('aida-update-e3da1e0863cf.json', scope)

    client = gspread.authorize(cred)

    try:
        sheet = client.open_by_key(sheetID).sheet1
        print('successfully connected to sheet')
        return sheet
    except Exception as e:
        if 'Max retries exceeded with url' in str(e):
            print('no internet!')
            return -1

        elif 'Requested entity was not found' in str(e):
            print('bad sheet name')
            return -1

        elif 'The caller does not have permission' in str(e):
            print('need to share sheet')
            return -1

        else:
            print(str(e))
            return -1

D = {'Date':str(datetime.now()), 'time':2, 'Sample ID':3, 'Run ID':4,'test3':9, 'SiH4':5, 'He':6,'Test':7,'o2':60,
     'RF':5,'Pressure':5000}

sheet = connectToSheet('1HVA9cyYvAC-fXiE51zEIgCcVA4PRgXLs6Lz4Gyfhx7Q')
if sheet == -1:
    pass
else:
    updateSheet(sheet, D)

#       '1KfwftgVLMEHyujG-p6m1Kvqw07hqFSUgQVP4ldVyrN8'
#       '1HVA9cyYvAC-fXiE51zEIgCcVA4PRgXLs6Lz4Gyfhx7Q'


