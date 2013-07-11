from OpenWizzy import o
import numpy

class NumTools:
    def __init__(self):
        self.currencies={}

    def _getYearFromMonthId(self,monthid,startyear=0):
        """
        @param monthid is an int representing a month over a period of time e.g. month 24, is the 24th month
        """
        year=numpy.floor(float(monthid)/12)+startyear
        return int(round(year))

    def getMonthsArrayForXYear(self,X,initvalue=None):
        """
        return array which represents all months of X year, each value = None
        """
        #create array for 36 months
        months=[]
        for i in range (X*12+1):
            months.append(initvalue)
        return months

    def getYearAndMonthFromMonthId(self,monthid,startyear=0):
        """
        @param monthid is an int representing a month over a period of time e.g. month 24, is the 24th moth
        @return returns year e.g. 1999 and month in the year
        """
        monthid=monthid-1
        year=self._getYearFromMonthId(monthid)
        month=monthid-year*12
        year+=startyear
        return [year,month+1]

    def roundDown(self,value,floatnr=0):
        value=value*(10**floatnr)
        return round(numpy.floor(value)/(10**floatnr),floatnr)

    def roundUp(self,value,floatnr=0):
        value=value*(10**floatnr)
        return round(numpy.ceil(value)/(10**floatnr),floatnr) 

    def interpolateList(self,tointerpolate,left=0,right=None,floatnr=None):
        """
        interpolates a list (array)
        if will fill in the missing information of an array
        each None value in array will be interpolated
        """
        xp=[]
        fp=[]
        x=[]
        isint=True
        allNone=True
        
        for x2 in tointerpolate:
            if x2<>None:
                allNone=False
        if allNone:
            tointerpolate=[0.0 for item in tointerpolate]
                
        for xpos in range(len(tointerpolate)):
            if not tointerpolate[xpos]==None and not o.basetype.integer.check(tointerpolate[xpos]):
                isint=False
            if tointerpolate[xpos]==None:
                x.append(xpos)
            if tointerpolate[xpos]<>None:
                xp.append(xpos)
                fp.append(tointerpolate[xpos])	
        if len(x)>0 and len(xp)>0:
            result=numpy.interp(x,xp,fp,left,right)	
                
            result2={}
            for t in range(len(result)):
                result2[x[t]]=result[t]
            result3=[]
            for xpos in range(len(tointerpolate)):
                if result2.has_key(xpos):
                    result3.append(result2[xpos])
                else:
                    result3.append(tointerpolate[xpos])
            if isint:
                result3=[int(round(item,0)) for item in result3]
            else:
                if floatnr<>None:
                    result3=[round(float(item),floatnr) for item in result3]
                else:
                    result3=[float(item) for item in result3]
        else:
            result3=tointerpolate

        return result3

    def collapseDictOfArraysOfFloats(self,dictOfArrays):
        """
        format input {key:[,,,]}
        """
        result=[]
        for x in range(len(dictOfArrays[keys()[0]])):
            result[x]=0.0
            for key in dictOfArrays.keys():
                result[x]+=dictOfArrays[key][x]
        return result

    def collapseDictOfDictOfArraysOfFloats(self,data):
        """
        format input {key:{key:[,,,]},key:{key:[,,,]},...}
        """
        result={}
        key1=data.keys()[0] #first element key
        key2=data[key1].keys()[0]
        nrX=len(data[key1][key2])

        for x in range(nrX):
            for key in data.keys(): #the keys we want to ignore (collapse)
                datasub=data[key]
                for keysub in datasub.keys():
                    if not result.has_key(keysub):
                        result[keysub]=[]
                        for y in range(0,nrX):
                            result[keysub].append(0.0)
                    result[keysub][x]+=datasub[keysub][x]
        return result

    def setMinValueInArray(self,array,minval):
        result=[]
        for item in array:
            if item<minval:
                result.append(minval)
            else:
                result.append(item)
        return result

    def _initCurrencies(self):
        if self.currencies=={}:
            path=o.system.fs.joinPaths("cfg","currencies.cfg")
            if o.system.fs.exists(path):
                ini=o.tools.inifile.open(path)
                if ini.checkSection("eur"):
                    for cur in ini.getSectionAsDict("eur").keys():
                        self.currencies[cur]=ini.getFloatValue("eur",cur)

    def text2val(self,value):
        """
        value can be 10%,0.1,100,1m,1k  m=million 
        USD/EUR/CH/EGP/GBP are also understood
        all gets translated to eur
        e.g.: 10%
        e.g.: 10EUR or 10 EUR (spaces are stripped)
        e.g.: 0.1mEUR or 0.1m EUR or 100k EUR or 100000 EUR        
        """
        if not o.basetype.string(value):
            raise RuntimeError("value needs to be string in text2val, here: %s" % value)
        if value.lower().find("eur")<>-1:
            value=value.replace("eur","").strip()
        self._initCurrencies()          
        cur=1.0
        for cur2 in self.currencies.keys():
            if value.find(cur2)<>-1:
                value=value.replace(cur2,"").strip()
                cur=self.currencies[cur2]
        if value.find("k")<>-1:
            value=float(value.replace("k","").strip())*1000
        elif value.find("m")<>-1:
            value=float(value.replace("m","").strip())*1000000
        elif value.find("%")<>-1:
            value=float(value.replace("%","").strip())/100
        value=float(value)*cur
        return value
        

        
        
        
