
from JumpScale import j
from Sheets import *


class Row(j.code.classGetBase()):

    def __init__(self, name="", ttype="float", nrcols=72, aggregate="T", description="", groupname="", groupdescr="",
                 format="", defval="default", nrfloat=None):
        """
        @param ttype int,perc,float,empty,str,unknown
        @param aggregate= T,MIN,MAX,LAST,FIRST,AVG
        @format bold (if empty then normal)
        """
        self.name = name
        if defval == "default":
            if ttype == "float" or ttype == "perc" or ttype == "int":
                defval = 0.0
            if ttype == "empty":
                defval = ""

        self.cells = [defval for item in range(nrcols)]
        self.defval = defval

        self.ttype = ttype
        self.format = format
        self.description = description
        self.groupname = groupname
        self.groupdescr = groupdescr
        self.aggregateAction = aggregate
        self.nrfloat = nrfloat
        if aggregate not in ["T", "MAX", "MIN", "LAST", "FIRST", "AVG"]:
            raise RuntimeError("Cannot find action:%s for agreggate" % self.aggregateAction)
        if ttype not in ["int", "perc", "float", "empty", "str", "unknown"]:
            raise RuntimeError("only support format: int,perc,float,empty,str,unknown")
        self.nrcols = nrcols

    def setDefaultValue(self, defval=None, stop=None):
        if defval == None:
            defval = self.defval
        if defval == None:
            defval = 0.0
        if stop == None:
            stop = self.nrcols
        else:
            stop += 1
        for colid in range(0, int(stop)):
            if self.cells[colid] == None:
                self.cells[colid] = defval

    def indexation(self, yearlyIndexationInPerc, roundval=100):

        for year in range(2, 7):
            now = 12 * (year - 1)
            prev = 12 * (year - 2)
            self.cells[now] = self.cells[prev] * (1 + yearlyIndexationInPerc)
            self.setDefaultValue(0.0)
            self.round(roundval=roundval)
            self.makeGoHigher()

    def makeGoHigher(self):
        """
        make sure each cell of row is higher than previous cell
        """
        prev = 0
        for colid in range(0, self.nrcols):
            if self.cells[colid] < prev:
                self.cells[colid] = prev
            prev = self.cells[colid]

    def aggregate(self, period="Y"):
        """
        @param period is Q or Y (Quarter/Year)
        """

        def calc(months):

            if self.aggregateAction == "LAST":
                return self.cells[months[-1]]
            if self.aggregateAction == "FIRST":
                return self.cells[months[0]]
            result = 0.0
            if self.aggregateAction == "MIN":
                result = 9999999999999999999
            for m in months:
                val = self.cells[m]
                if val == None:
                    raise RuntimeError("Cannot aggregrate row %s from group %s,\n%s" % (self.name, self.groupname, self.cells))
                if self.aggregateAction == "T" or self.aggregateAction == "AVG":
                    result += val
                if self.aggregateAction == "MIN":
                    if (val < 0 and val < result) or (val > 0 and val > result):
                        result = val
                if self.aggregateAction == "MAX":
                    if (val > 0 and val > result) or (val < 0 and val < result):
                        result = val
            if self.aggregateAction == "AVG":
                result = result / len(months)
            return result

        #monthAttributes=[item.name for item in self.months[1].JSModel_MODEL_INFO.attributes]
        if period == "Y":
            result = [0.0 for item in range(6)]
            for year in range(1, 7):
                months = [12 * (year - 1) + i for i in range(12)]
                # name=self._getYearStringFromYearNr(year)
                result[year - 1] = calc(months)
        if period == "Q":
            result = [0.0 for item in range(6 * 4)]
            for quarter in range(1, 4 * 6 + 1):
                months = [3 * (quarter - 1) + i for i in range(3)]
                # name=self._getYearStringFromYearNr(year)
                result[quarter - 1] = calc(months)
        return result

    def interpolate(self, start=None, stop=None, variation=0, min=None, max=None):
        """
        @param random if 5 means will put 5% variation on it while interpolating
        """
        # tointerpolate=[]
        # for item in self.cells:
            # if item==0.0:
                # item=None
            # tointerpolate.append(item)
        if start == None:
            start = 0
        if stop == None:
            stop = len(self.cells) - 1
        tointerpolate = self.cells[start:stop + 1]
        try:
            interpolated = j.tools.numtools.interpolateList(tointerpolate, floatnr=self.nrfloat)
        except Exception as e:
            print "could not interpolate row %s" % self.name
            from JumpScale.core.Shell import ipshellDebug, ipshell
            print "DEBUG NOW cannot interpolate, explore self & tointerpolate"
            ipshell()
        xx = 0
        for x in range(start, stop + 1):
            self.cells[x] = interpolated[xx]
            xx += 1

        self.randomVariation(variation, min=min, max=max)

    def randomVariation(self, variation, start=None, stop=None, min=None, max=None):
        if variation == 0:
            return
        if start == None:
            start = 0
        if stop == None:
            stop = len(self.cells) - 1
        # variation=float(self.getMax())/100*float(random)
        variation = int(float(variation) * 100.0)
        roundd = self.ttype in ["perc", "int"]
        for x in range(start, stop + 1):
            self.cells[x] = self.cells[x] - variation / 200 + float(j.base.idgenerator.generateRandomInt(1, variation)) / 100
            if roundd:
                self.cells[x] = int(self.cells[x])

    def complete(self, start, vvariation=0.2, hvariation=0, minvalue=0, maxvalue=100, lastpos=70):
        """
        will copy beginning of row with certain variation to rest of row
        will start doing that from mentioned startpoint
        @param hvariation not implemented
        """
        stop = len(self.cells) - 1
        blocksize = start - 1
        halt = False
        x = start
        while halt == False:
            for xInBlock in range(0, blocksize + 1):
                x += 1
                xorg = xInBlock
                # print "xorg:%s"%xorg
                if x > self.nrcols:
                    halt = True
                    self.setCell(self.nrcols - 1, lastpos, minvalue, maxvalue)
                    break
                if self.cells[xorg] != None:
                    val = self.cells[xorg]
                    # print val
                    val = val + self._getVariationRelative(vvariation, val)
                    self.setCell(x, val, minvalue, maxvalue)

    def setCell(self, posx, value, minvalue=None, maxvalue=None):
        if minvalue != None and value < minvalue:
            value = minvalue
        if maxvalue != None and value > maxvalue:
            value = maxvalue
        if posx > self.nrcols - 1:
            print "out of range: x:%s y:%s" % (posx, value)
            return None, None
        self.cells[posx] = value
        # print "x:%s y:%s" % (posx,value)
        return posx, value

    def _getVariationAbsoluteInt(self, val, variation):
        variation = int(variation)
        changeMin = int(val - variation)
        changeMax = int(val + variation)
        gd = j.base.idgenerator.generateRandomInt(changeMin, changeMax)
        return gd

    def _getVariationPositive(self, change, variation):
        change = float(change)
        if change < 0:
            raise RuntimeError("change needs to be positive")
        variation = float(variation)
        if variation < 0 or variation > 1:
            raise RuntimeError("Variation cannot be more than 1 and not less than 0.")
        changeMin = int(100.0 * (change - variation * change))
        changeMax = int(100.0 * (change + variation * change))
        gd = float(j.base.idgenerator.generateRandomInt(changeMin, changeMax) / 100.0)
        return gd

    def goDown(self, start, stop, godown, nrSteps, hvariation, vvariation, isActiveFunction=None):
        start = int(start)
        stop = int(stop)
        blocksize = float(stop + 1 - start) / float(nrSteps)
        runNr = 0
        if start > self.nrcols:
            return start, None
        y = self.cells[start]  # start height
        if y == None:
            raise RuntimeError("start position y needs to <> None")
        y = float(y)
        minvalue = y - godown
        if minvalue < 0:
            raise RuntimeError("Minvalue in go down can not be < 0")
        godown = float(godown) / float(nrSteps)
        maxvalue = y - 1
        while True:
            runNr += 1
            start2 = start + blocksize * (runNr)
            if isActiveFunction != None:
                if not isActiveFunction(start2):
                    stop += int(blocksize)
                    continue
            x = self._getVariationAbsoluteInt(start2, hvariation)
            y = y - self._getVariationPositive(godown, vvariation)
            y2 = y
            if x > stop:
                return self.setCell(stop, y)
            x, y = self.setCell(x, y, minvalue, maxvalue)
            if y == None:
                self.setCell(self.nrcols - 1, y2)
                return x, y2

    def goUp(self, start, stop, goup, nrSteps, hvariation, vvariation, isActiveFunction=None):
        start = int(start)
        stop = int(stop)
        blocksize = float(stop + 1 - start) / float(nrSteps)
        runNr = 0
        if start > self.nrcols:
            return start, None
        y = self.cells[start]  # start height
        if y == None:
            raise RuntimeError("start position y needs to <> None")
        y = float(y)
        minvalue = y
        if minvalue < 0:
            raise RuntimeError("Minvalue in go up can not be < 0")
        maxvalue = y + goup
        goup = float(goup) / float(nrSteps)
        while True:
            runNr += 1
            start2 = start + blocksize * (runNr)
            if isActiveFunction != None:
                if not isActiveFunction(start2):
                    stop += int(blocksize)
                    continue
            x = self._getVariationAbsoluteInt(start2, hvariation)
            y = y + self._getVariationPositive(goup, vvariation)
            y2 = y
            if x > stop:
                return self.setCell(stop, y)
            x, y = self.setCell(x, y, minvalue, maxvalue)
            if y == None:
                self.setCell(self.nrcols - 1, y2)
                return x, y

    def getMax(self, start=None, stop=None):
        if start == None:
            start = 0
        if stop == None:
            stop = len(self.cells) - 1
        r = 0
        for x in range(start, stop + 1):
            if self.cells[x] > r:
                r = self.cells[x]
        return r

    def checkFilledIn(self, start, stop):
        for x in range(start, stop + 1):
            if start < 0:
                continue
            if self.cells[x] != None:
                return True
        return False

    def _roundNrCumul(self, val, x, args):
        nr = val
        if nr == None:
            nr = 0.0
        # print "%s %s %s" % (self.name,nr,self._cumul)
        if nr + self._cumul > 0.5 and nr + self._cumul < 10:
            self._cumul = nr + self._cumul
            nr2 = j.tools.numtools.roundDown(self._cumul * 2, 0) / 2
            self._cumul += nr - nr2
            self._cumul = self._cumul - nr2
            # print "<10 %s %s" % (nr2,self._cumul)
            return nr2
        elif nr + self._cumul == 0.5:
            self._cumul = 0.0
            return 0.5
        elif nr + self._cumul < 0.5:
            self._cumul += nr
            # print "<0.5 %s %s" % (0,self._cumul)
            return 0
        elif nr + self._cumul >= 10:
            nr2 = j.tools.numtools.roundDown(nr, 0)
            self._cumul += nr - nr2
            return nr2
        else:
            raise RuntimeError("error in normalizing, should not get here")
        return nr

    def applyFunction(self, ffunction, args={}):
        """
        call ffunction with params (val of cell, x, args as dict)
        row gets modified
        """
        for x in range(0, self.nrcols):
            self.cells[x] = ffunction(self.cells[x], x, args)

    def text2row(self, data, standstill=0, defval=None, startval=None, round=False, interpolate=None):
        """
        convert string format 2:100,5:200 to an array with required length (month 2=100, ...)
        values can be 10%,0.1,100,1m,1k  m=million USD/EUR/CH/EGP/GBP are also understood
        result will be put into the given row
        data kan be 1 string or list
        if list then list need to be of length len(row)/12 so is a value per year
        standstill is first X nr of months which are made 0
        """
        def custom2rowvalues(datas):
            interp = False
            maxpos = None
            maxval = 0.0
            start = None
            year = -1
            for data in datas:
                year += 1
                if not(str(data).find(",") == -1 and str(data).find(":") == -1):
                    # means custom value
                    if data.find("I") != -1:
                        data = data.replace("I", "").strip()
                        interp = True
                    data = data.replace("'", "").strip()
                    splitted = data.split(",")
                    maxpos = 0.0
                    maxval = 0.0
                    for item in splitted:
                        if len(item.split(":")) != 2:
                            raise RuntimeError("text2row input not properly formatted: %s, subpart: %s" % (data, item))
                        pos, value = item.split(":")
                        pos = int(pos) + (12 * year)
                        if start == None and interp:
                            start = (int(j.tools.numtools.roundDown((float(pos) / 12)))) * 12
                        try:
                            value = j.tools.numtools.text2val(value)
                        except Exception as e:
                            print "error: %s " % e
                            print "error in parsing input data for %s" % datas
                            print "error in element %s" % data
                            print "row:%s" % self.name
                        if value > maxval:
                            maxval = value
                        self.cells[pos - 1] = value
                        if pos > maxpos:
                            maxpos = pos
                        # calculate end of year of last found position where data was set
            if maxpos == None:
                stop = 0
            else:
                stop = int(j.tools.numtools.roundUp((float(maxpos) / 12)))
            if start == None:
                start = 0
            if interpolate == True or (interp and interpolate == None):
                if len(datas) != 1:
                    self.interpolate(start, stop * 12 - 1)
                else:
                    self.interpolate()
                maxval = value
            else:
                maxval = 0
                # no interpolate
            self.setDefaultValue(self.defval, stop * 12 - 1)
            return stop, maxval

        if defval != None:
            self.defval = defval

        if startval != None:
            self.cells[0] = float(startval)

        if standstill > 0:
            for x in range(0, standstill):
                self.cells[x] = self.defval

        if not j.basetype.list.check(data):
            if data == None:
                self.cells[0] = float(startval)
            elif str(data).find(",") == -1 and str(data).find(":") == -1:
                # is only 1 value so set all data
                if str(data).strip() == "" or data == None:
                    data = "0.0"
                self.setDefaultValue(float(data))
            else:
                # is custom format, need to process
                custom2rowvalues([data])
            if round:
                self._cumul = 0.0
                self.applyFunction(self._roundNrCumul)
            return
        else:
            datas = data
            stop, maxval = custom2rowvalues(datas)
            if stop * 12 < self.nrcols and self.cells[stop * 12] == None:
                self.cells[stop * 12] = maxval
            for x in range(len(datas)):
                data = datas[x]
                year = x + 1
                # print "%s %s" % (year,stop)
                if year > stop:
                    # print "normal values in year %s" % year
                    if str(data).find(",") == -1 and str(data).find(":") == -1 and data != None:
                        # is only 1 value
                        if str(data).strip() == "":
                            data = "0.0"
                        data = float(data)
                        self.cells[year * 12 - 1] = data
            self.interpolate(stop * 12)
            self.setDefaultValue()

        if round:
            self._cumul = 0.0
            self.applyFunction(self._roundNrCumul)

    def recurring(self, row, delay, start, churn, nrmonths):
        """
        @param row is the row we will fill in with recurring calc
        @param start value to start with at month 0 (is first month)
        @param churn 2 means 2% churn
        @param delay is different beween selling & being active
        """
        # print "churn:%s" % churn
        if churn == "1000%":
            row.setDefaultValue(0.0)
            return row
        delay = int(round(delay, 0))
        for delaynr in range(0, delay):
            row.cells[delaynr] = start
        for colid in range(0, int(self.nrcols)):
            nractive = float(start)
            if (colid - int(nrmonths)) < 0:
                start2 = 0
            else:
                start2 = colid - int(nrmonths)
            for monthprevid in range(start2, colid + 1):
                nractive += float(self.cells[monthprevid]) * ((1 - float(churn) / 12) ** (colid - monthprevid))
            if colid + delay < row.nrcols:
                row.cells[colid + delay] = nractive

        row.round()
        return row

    def round(self, nrfloat=None, roundval=None):
        """
        @param roundval if e.g. 100 means round will be done with values of 10, nr float will then be 0 (automatically)
        """
        if nrfloat == None:
            nrfloat = self.nrfloat
        if roundval > 0:
            nrfloat = 0

        for colid in range(0, int(self.nrcols)):
            if self.cells[colid] != None:
                if roundval > 0:
                    self.cells[colid] = round(self.cells[colid] / roundval, nrfloat) * roundval
                if self.ttype == "int":
                    self.cells[colid] = int(round(self.cells[colid], nrfloat))
                elif self.ttype == "float":
                    self.cells[colid] = round(self.cells[colid], nrfloat)

    def areCosts(self):
        """
        negate the values in the row
        """
        for colid in range(0, int(self.nrcols)):
            if self.cells[colid] > 0:
                self.cells[colid] = -self.cells[colid]

    def invert(self):
        """
        invert + becomes - and reverse
        """
        for colid in range(0, int(self.nrcols)):
            self.cells[colid] = -self.cells[colid]

    def delay(self, delay=0, defval=None):
        if defval != None:
            self.defval = defval
        delay = int(delay)
        out = [0.0 for item in range(self.nrcols)]
        nrmax = self.nrcols
        if delay > 0:
            for i in range(delay):
                out[i] = self.defval
        delayed = 0.0
        if delay < 0:
            for i in range(-delay + 1):
                # print "delay: %s %s %s" % (self.name,i,self.cells[i])
                delayed += self.cells[i]
            # print delayed
        i = delay
        for cell in self.cells:
            if i < nrmax and i > -1:
                out[i] = cell
            i += 1
        i = 0
        if delay < 0:
            out[0] += delayed
        self.cells = out

    def __str__(self):
        if self.nrcols > 18:
            l = 18
        else:
            l = self.nrcols
        result = [self.name]
        result.extend([self.cells[col] for col in range(l)])
        return str(result)

    __repr__ = __str__

    def _dict2obj(self, dict):
        self.name = dict["name"]
        self.cells = dict["cells"]
        self.ttype = dict["ttype"]
        self.format = dict["format"]
        self.description = dict["description"]
        self.groupname = dict["groupname"]
        self.groupdescr = dict["groupdescr"]
        self.aggregateAction = dict["aggregateAction"]
        self.nrcols = dict["nrcols"]
        self.nrfloat = dict["nrfloat"]
        return self


class Sheet(j.code.classGetBase()):

    def __init__(self, name, nrcols=72, headers=[], period="M"):
        """
        @param period is M,Q or Y
        """
        self.name = name
        self.description = ""
        self.nrcols = nrcols
        self.remarks = ""
        self.period = period  # M, Q or Y

        if headers == []:
            self.headers = [item + 1 for item in range(nrcols)]
        else:
            self.headers = headers
            self.nrcols = len(self.headers)

        self.rows = {}
        self.rowNames = []

    # def _obj2dict(self):
        # ddict={}
        # ddict["name"]=self.name
        # ddict["headers"]=self.headers
        # ddict["nrcols"]=self.nrcols
        #ddict["rows"]=[item.obj2dict() for item in self.rows]
        # return ddict

    def _dict2obj(self, dict):
        self.name = dict["name"]
        self.headers = dict["headers"]
        self.nrcols = dict["nrcols"]
        slf.period = dict["period"]
        for key in dict["rows"].keys():
            item = dict["rows"][key]
            row = j.code.dict2object(Row(), item)
            self.rows[row.name] = row

    def addRow(self, name, ttype="float", aggregate="T", description="", groupname="", groupdescr="", nrcols=None, format="", values=[],
               defval=None, nrfloat=None):
        """
        @param ttype int,perc,float,empty,str
        @param aggregate= T,A,MIN,MAX
        @param values is array of values to insert
        @param defval is default value for each col
        @param round is only valid for float e.g. 2 after comma
        """
        if nrcols == None:
            nrcols = self.nrcols
        if ttype == "float" and nrfloat == None:
            nrfloat = 2
        row = Row(name, ttype, nrcols, aggregate, description=description, groupname=groupname,
                  groupdescr=groupdescr, format=format, defval=defval, nrfloat=nrfloat)
        self.rows[name] = row
        self.rowNames.append(name)
        if values != []:
            for x in range(nrcols):
                self.setCell(name, x, values[x])
        return self.rows[name]

    # def renting(self,row,interest,nrmonths):
    # DOES NOT WORK, JUST COPY PASTE TO START DOING IT
        #"""
        #@param row is the row in which we need to fill in
        #@param start value to start with at month 0 (is first month)
        #@param churn 2 means 2% churn
        #@param delay is different beween selling & being active
        #"""
        # print "churn:%s" % churn
        # if churn=="1000%":
            # row.setDefaultValue(0.0)
            # return row
        # delay=int(round(delay,0))
        # for delaynr in range(0,delay):
            # row.cells[delaynr]=start
        # for colid in range(0,int(self.nrcols)):
            # nractive=float(start)
            # if (colid-int(nrmonths))<0:
                # start2=0
            # else:
                # start2=colid-int(nrmonths)
            # for monthprevid in range(start2,colid+1):
                # nractive+=float(self.cells[monthprevid])*((1-float(churn)/12)**(colid-monthprevid))
            # if colid+delay<row.nrcols:
                # row.cells[colid+delay]=nractive

        # row.round()
        # return row

    def aggregate(self, rownames=[], period="Y"):
        """
        @param rownames names of rows to aggregate
        @param period is Q or Y (Quarter/Year)
        """
        rows = []
        header = [""]
        headerDone = False
        if rownames == []:
            rownames = self.rowNames

        for rowName in rownames:
            row = [rowName]
            row2 = self.getRow(rowName)
            result = row2.aggregate(period)
            for key in range(len(result)):
                if headerDone == False:
                    if period == "Y":
                        hid = "Y%s" % int(key + 1)
                    else:
                        year = j.tools.numtools.roundDown(float(key) / 4)
                        Q = "Q%s" % int(j.tools.numtools.roundDown(float(key - 1 - year * 4)) + 2)
                        year = "Y%s" % int(year + 1)
                        hid = "%s %s" % (year, Q)
                    header.append(hid)
                row.append(result[key])
            headerDone = True
            rows.append(row)

        return rows, header

    def copyFrom(self, sheets, sheetname, rowname, newRowName, newGroupName):
        """
        @param sheets if None then this sheetobject
        """
        if sheets == None:
            sheetfrom = self
        else:
            sheetfrom = sheets.sheets[sheetname]
        rowfrom = sheetfrom.rows[rowname]
        newrow = self.addRow(newRowName, groupname=newGroupName)
        newrow.aggregateAction = rowfrom.aggregateAction
        newrow.nrfloat = rowfrom.nrfloat
        # newrow.groupname=rowfrom.groupname
        newrow.ttype = rowfrom.ttype
        newrow.format = rowfrom.format
        for x in range(0, rowfrom.nrcols):
            newrow.cells[x] = rowfrom.cells[x]
        return newrow

    def getSheetAggregated(self, period="Y"):
        """
        @param period is Q or Y (Quarter/Year)
        """
        rows, headers = self.aggregate(period=period)
        lenx = len(headers) - 1
        sheet2 = j.tools.sheet.new(self.name, self.nrcols, headers)
        sheet2.description = self.description
        sheet2.remarks = self.remarks
        sheet2.period = period
        for row in rows:
            roworg = roworg = self.getRow(row[0])
            rownew = sheet2.addRow(roworg.name, roworg.ttype, roworg.aggregateAction, roworg.description, roworg.groupname, roworg.groupdescr, lenx,
                                   roworg.format, nrfloat=roworg.nrfloat)
            if roworg.ttype == "float":
                rownew.ttype = "int"
                rownew.nrfloat = 0

            rownew.description = roworg.description
            for x in range(0, lenx):
                rownew.cells[x] = row[x + 1]
            rownew.round()
        return sheet2

    def getRow(self, rowName):
        if rowName not in self.rows:
            raise RuntimeError("Cannot find row with name %s" % rowName)
        return self.rows[rowName]

    def getCell(self, rowName, month):
        row = self.getRow(rowName)
        return row.cells[int(month)]

    def setCell(self, rowName, month, value):
        if month > self.nrcols - 1:
            raise ValueError("max month = %s, %s given" % (self.nrcols - 1, month))
        row = self.getRow(rowName)

        row.cells[month] = value

    def addCell(self, rowName, month, value):
        if month > self.nrcols - 1:
            raise ValueError("max month = %s, %s given" % (self.nrcols - 1, month))
        row = self.getRow(rowName)
        row.cells[month] += value

    def interpolate(self, rowname):
        row = self.getRow(rowname)
        row.interpolate()
        return row

    # def delay(self,rowName,delay=0,defValue=0.0,copy2otherRowName=None):
        # delay=int(delay)
        #out=[0.0 for item in range(self.nrcols)]
        # nrmax=self.nrcols
        # for i in range(delay):
            # out[i]=defValue
        # i=delay
        # row=self.getRow(rowName)
        # for cell in row.cells:
            # if i<nrmax:
                # out[i]=cell
            # else:
                # break
            # i+=1
        # i=0
        # if copy2otherRowName<>None:
            # check if row already exists
            # if not self.rows.has_key(copy2otherRowName):
                # self.addRow(copy2otherRowName,"float")
            # dest=copy2otherRowName
        # else:
            # dest=rowName

        # for month in range(self.nrcols):
            # self.setCell(dest,month,out[month])

        # return self.rows[dest]

    def accumulate(self, rowNameInput, rowNameDest):
        """
        add previous month on top of current and keep on adding (accumulating)
        @param rowNameInput is name of row we would like to aggregate
        @param rowNameDest if empty will be same as rowNameInput1
        """
        previous = 0
        for colnr in range(self.nrcols):
            input = self.getCell(rowNameInput, colnr)
            self.setCell(rowNameDest, colnr, input + previous)
            previous = self.getCell(rowNameDest, colnr)
        return self.rows[rowNameDest]

    def setDefaultValue(self, rowNameInput, defval=0.0):
        """
        add previous month on top of current and keep on adding (accumulating)
        @param rowNameInput is name of row we would like to aggregate
        """
        previous = 0
        for colnr in range(self.nrcols):
            input = self.getCell(rowNameInput, colnr)
            if input == None:
                self.setCell(rowNameInput, colnr, defval)
        return self.rows[rowNameInput]

    def applyFunction(self, rowNames, method, rowNameDest="", params={}):
        """
        @param rowNames is array if names of row we would like to use as inputvalues
        @param rowNameDest if empty will be same as first rowName
        @param method is python function with params (sheet,**input) returns the result
            input is dict with as key the arguments & the keys of params (so all collapsed in same input dict)
        """
        if rowNameDest == "":
            rowNameDest = rowNames[0]
        if rowNameDest not in self.rows:
            self.addRow(rowNameDest, "float")
        for colnr in range(self.nrcols):
            input = {}
            for name in rowNames:
                input[name] = self.getCell(name, colnr)
                if input[name] == None:
                    input[name] = 0.0
            for key in params:
                input[key] = params[key]
            self.setCell(rowNameDest, colnr, method(**input))
        return self.rows[rowNameDest]

    def getColumnsWidth(self):
        def getwidth(value):
            width = 0
            if value < 0:
                width += 1
                valuepos = -value
            else:
                valuepos = value
            if valuepos < 1000:
                pass
            elif valuepos < 1000000:
                width += 1
            elif valuepos < 1000000000:
                width += 2
            elif valuepos < 1000000000000:
                width += 3
            if valuepos < 1 and round(valuepos) != valuepos:
                width += 3
            elif valuepos < 10 and round(valuepos) != valuepos:
                width += 2
            valueposround = int(round(valuepos))
            width += len(str(valueposround))
            return width

        cols = {}
        for key in self.rows.keys():
            row = self.rows[key]
            for colnr in range(0, len(row.cells)):
                if colnr not in cols:
                    cols[colnr] = 0
                w = getwidth(row.cells[colnr])
                if w > cols[colnr]:
                    cols[colnr] = w
        return cols

    def addRows(self, rows2create, aggregation):
        """
        @para rows2create {groupname:[rownames,...]}
        """
        for group in rows2create.keys():
            rownames = rows2create[group]
            for rowname in rownames:
                if rowname in aggregation:
                    aggr = aggregation[rowname]
                else:
                    aggr = "T"
                rowx = self.addRow(rowname, description="", nrfloat=1, aggregate=aggr)
                rowx.groupname = group

    def applyFunctionOnValuesFromRows(self, rownames, method, rowDest, params={}):
        """
        @param rows is array if of rows we would like to use as inputvalues
        @param rowDest if empty will be same as first row
        @param method is python function with params (values,params) values are inputvalues from the rows
        """
        for colnr in range(rowDest.nrcols):
            input = []
            for rowname in rownames:
                val = self.getCell(rowname, colnr)
                if val == None:
                    val = 0.0
                input.append(val)

            rowDest.cells[colnr] = method(input, params)
        return rowDest

    def sumRows(self, rownames, newRow):
        """
        make sum of rows
        @param rownames is list of rows to add specified by list or rownames
        @param newRow is the row where the result will be stored (can also be the name of the new row then row will be looked for)
        """
        if j.basetype.string.check(newRow):
            newRow = self.getRow(newRow)

        def summ(values, params):
            total = 0.0
            for value in values:
                total += value
            return total
        newRow = self.applyFunctionOnValuesFromRows(rownames, summ, newRow)
        return newRow

    def multiplyRows(self, rownames, newRow):
        """
        make procuct of rows
        @param rownames is list of rows to add specified by list or rownames
        @param newRow is the row where the result will be stored (can also be the name of the new row then row will be looked for)
        """
        if j.basetype.string.check(newRow):
            newRow = self.getRow(newRow)

        def mult(values, params):
            total = 1.0
            for value in values:
                total = total * value
            return total

        newRow = self.applyFunctionOnValuesFromRows(rownames, mult, newRow)
        return newRow

    def __str__(self):
        result = ""
        for row in self.rows:
            result += "%s\n" % row
        return result

    __repr__ = __str__


class SheetFactory():

    def new(self, name, nrcols=72, headers=[], period="M"):
        """
        @param period is M,Q or Y
        """
        return Sheet(name, nrcols=nrcols, headers=headers, period=period)

    def getSheetsCollection(self):
        return Sheets()
