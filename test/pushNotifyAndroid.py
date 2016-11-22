#!/usr/bin/python
import os
import requests


def main():
    sConfFile = "server.txt"

    sHomeDBPath = "/".join(os.path.dirname(os.path.realpath(__file__)).split("/")[:-1])
    sConfFilePath = sHomeDBPath+"/conf/"+sConfFile

    code = getConfig(sConfFilePath)
    if code != False:
        print "code: '{}'".format(code)
        requests.post("https://api.simplepush.io/send", data={"key": code,
                                                              "title": "Test",
                                                              "msg": "Notification"})
    else:
        print "code not right. {}".format(code)
    return


def getConfig(f):
    with open(f, "r") as inf:
        for line in inf:
            line = line.rstrip().split("=")
            if line[0] == "code":
                return line[1]
    return False

if __name__ == "__main__":
    main()
