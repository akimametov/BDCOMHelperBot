import openpyxl
wb = openpyxl.load_workbook('IP-devices.xlsx')
sheet = wb['IP']

def getOltIP(location):
    oltIP=[]
    for row in sheet.iter_rows(min_col=1, max_col=2, values_only=True):
        cell_a, cell_b = row
        if cell_a == location:
            oltIP.append(cell_b)
    return oltIP