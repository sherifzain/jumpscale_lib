
from JumpScale import j
from Sheet import *


class Sheets(j.code.classGetBase()):

    def __init__(self):
        self.sheets = {}
        self.sheetsByCategory = {}
        self.sheetNames = []

    def new(self, name, nrcols=72, headers=[], category=None):
        sheet = Sheet(name, nrcols=nrcols, headers=headers)
        self.add(sheet, category)
        return sheet

    def add(self, sheet, category=None):
        self.sheets[sheet.name] = sheet
        if category != None:
            if category not in self.sheetsByCategory:
                self.sheetsByCategory[category] = []
            self.sheetsByCategory[category].append(sheet.name)
        self.sheetNames.append(sheet.name)

    def dict2sheet(self, data):
        sheet = Sheet("", nrmonths=72, headers=[])
        sheet.dict2obj(data)
        return sheet

    def aggregateSheets(self, sheetnames, rowdescr, category, aggregateSheetName="Total", aggregation={}):
        """
        @param sheetnames are the sheets to aggregate
        @param rowdescr {groupname:[rownames,...]}
        """
        sheettotal = self.new(name=aggregateSheetName, category=category)
        sheettotal.description = "sheet aggregation of %s" % category
        sheettotal.addRows(rowdescr, aggregation)
        sheets = []
        for name in sheetnames:
            sheets.append(self.sheets[name])
        for group in rowdescr.keys():
            rownames = rowdescr[group]
            for rowname in rownames:
                for x in range(0, sheettotal.nrcols):
                    rowdest = sheettotal.rows[rowname]
                    sumvalue = 0.0
                    for sheet in sheets:
                        if sheet.rows[rowname].cells[x] == None:
                            raise RuntimeError("could not aggregate sheet%s row:%s, found None value" % (sheet.name, rowname))
                        sumvalue += sheet.rows[rowname].cells[x]
                    rowdest.cells[x] = sumvalue
        return sheettotal

    def applyFunction(self, rows, method, rowDest=None, params={}):
        """
        @param rows is array if of rows we would like to use as inputvalues
        @param rowDest if empty will be same as first row
        @param method is python function with params (values,params) values are inputvalues from the rows
        """
        if rowDest == "":
            rowDest = rows[0]
        for colnr in range(rowDest.nrcols):
            input = []
            for row in rows:
                val = row.cells[colnr]
                if val == None:
                    val = 0.0
                input.append(val)
            rowDest.cells[colnr] = method(input, params)
        return rowDest

    def sumRows(self, rows, newRow):
        """
        make sum of rows
        @param rows is list of rows to add
        @param newRow is the row where the result will be stored
        """
        def sum(values, params):
            total = 0.0
            for value in values:
                total += value
            return total
        rows2 = []
        for row in rows:
            if row != None:
                rows2.append(row)
        newRow = self.applyFunction(rows2, sum, newRow)
        return newRow

    def multiplyRows(self, rows, newRow):
        def mult(values, params):
            total = 1.0
            for value in values:
                total = total * value
            return total
        rows2 = []
        for row in rows:
            if row != None:
                rows2.append(row)
        newRow = self.applyFunction(rows2, mult, newRow)
        return newRow
