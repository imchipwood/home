"""Humidity Database

Contains specifics for database interaction for humidity sensors.
"""

import traceback
from db_home import DBHome


class DBHumidity(DBHome):
    sQuery = ""

    def __init__(self, f, bDebug=False):
        super(DBHumidity, self).__init__(f, bDebug)

###############################################################################

    """Format retrieved data

    Inputs:
        none
    Returns:
        nothing
    """
    def formatResults(self):
        dataFormatted = []
        if self.getDataRaw() != []:
            dataFormatted = []
            sSeparator = ("----------------------------"
                          "----------------------------")
            sHeader = ("Date       | Time     | Room     | Temperature | "
                       "Humidity")
            dataFormatted.append(sSeparator)
            dataFormatted.append(sHeader)
            dataFormatted.append(sSeparator)
            for i in reversed(xrange(len(self.getDataRaw()))):
                reading = self.getDataRaw()[i]
                date = "{}".format(reading[0])
                time = "{0:8s}".format(reading[1])
                room = "{0:8s}".format(reading[2])
                temp = "{0:11.1f}".format(reading[3])
                humi = "{0:0.1f}".format(reading[4]) + "%"
                sData = "{} | {} | {}".format(date, time, room)
                sData += " | {} | {}".format(temp, humi)
                dataFormatted.append(sData)
            dataFormatted.append(sSeparator)
        return dataFormatted

###############################################################################

    """Validate data to ensure no bad values are inserted into database

    Inputs:
        dData - dict of data with keys "humidity" and "temperature"
    Returns:
        True if data is valid, False otherwise
    """
    def __validateData(self, dData, bDebug=False):
        if 0 <= dData["humidity"] <= 100 and -100 <= dData["temperature"] <= 200:
            return True
        return False


###############################################################################

    """Insert data into the database

    Inputs:
        dData - dict of data with keys "temperature" and "humidity"
    Returns:
        True if data insertion was successful, False otherwise
    """
    def insertData(self, dData, insert=True, bDebug=False):
        if self.bDebug:
            bDebug = True

        if self.__validateData(dData, bDebug):
            sColumns = ", ".join(self._DBHome__conf["columns"])
            # I hate long strings
            self.dbcmd = (
                "INSERT INTO {0} ({1}) values(CURRENT_DATE(), NOW(), '{2}', "
                "{3:0.1f}, {4:0.1f})".format(self._DBHome__conf["table"],
                                             sColumns,
                                             self._DBHome__conf["room"],
                                             dData["temperature"],
                                             dData["humidity"])
            )
            if bDebug:
                print "-d- DBHumidity: Insert Command\n\t{}".format(self.dbcmd)
            if insert:
                try:
                    if bDebug:
                        "-d- DBHumidity: attempting insertion"
                    self.executeCmd(self.dbcmd, "insert")
                except Exception as E:
                    print "-E- DBHumidity: Error while inserting data into db."
                    traceback.print_exc()
                    return False
            return True
        else:
            if bDebug:
                print "-e- DBHumidity: Data invalid - check sensor connections"
            return False

###############################################################################

    """Verify Date Format for queries

    Private function to ensure SQL date queries are valid

    Inputs:
        sDate - date as a string "year-month-day"
    Returns:
        Nothing - raises an exception if format is incorrect
    """
    def __verifyDateFormat(self, sDate):
        sDateSplit = sDate.split("-")
        dDate = {"year": sDateSplit[0],
                 "month": sDateSplit[1],
                 "day": sDateSplit[2]}
        valid = True
        if len(dDate["year"]) != 4:
            print ("-E- DBHumidity: Date entered incorrectly -"
                   "year should be 4 digits. Year: {}".format(dDate["year"])
                   )
            valid = False
        if len(dDate["month"]) != 2:
            print ("-E- DBHumidity: Date entered incorrectly -"
                   "month should be 2 digits. Month: {}".format(dDate["month"])
                   )
            valid = False
        if len(dDate["day"]) != 2:
            print ("-E- DBHumidity: Date entered incorrectly -"
                   " day should be 2 digits. Day: {}".format(dDate["day"])
                   )
            valid = False
        return valid

###############################################################################

    """Create Google Charts Javascript table

    Inputs:
        None
    Returns:
        dataFormatted - array of strings formatted for Google Charts
            Javascript: ['datetime', temperature, humidity]
    """
    # TODO: Handle formatting when multiple rooms have been requested
    def formatDataForGoogleCharts(self):
        dataFormatted = ""
        dataFormattedArray = []
        if self.getDataRaw() != []:
            # build all table rows
            for i in reversed(xrange(len(self.getDataRaw()))):
                reading = self.getDataRaw()[i]
                sDateTime = "{} {}".format(reading[0], reading[1])
                sTime = "{}".format(reading[1])   # time only
                sTemp = "{0:0.1f}".format(reading[3])
                sHumi = "{0:0.4f}".format(float(reading[4])/100.)
                sRow = "['{0}', {1}, {2}],\n".format(sTime, sTemp, sHumi)
                dataFormattedArray.append(sRow)

            # remove extra comma from final row
            dataFormattedArray[-1] = dataFormattedArray[-1].replace("],", "]")
            # convert array into string
            for line in dataFormattedArray:
                dataFormatted += line
        return dataFormatted
