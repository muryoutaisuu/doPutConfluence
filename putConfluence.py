#!/usr/bin/env python2

# imports
import argparse
import logging
import os
import pprint
import sys
import datetime

import json
import requests
import getpass
import ConfigParser

# variables
# RESTAPI
APPLICATION = "putConfluence"
CONFIGFILE = "./putConfluence.conf"
# CONFLUENCE_USER_NAME
# CONFLUENCE_USER_PASSWORD
HEADERS = {
    "Content-Type": "application/json",
}
VERIFY = False
QUIET = False


# login setup
def setup_logging():
    """ initialize the logging handler """
    logger = logging.getLogger('logger.' + APPLICATION)
    LOGGING_DEFAULT_CONFIG_FILE = "/mgmt/etc/log.cfg"
    # LOGGING_LOCAL_CONFIG_FILE = "/mgmt/etc/log-local.cfg"
    LOGGING_STANZA_NAME = 'python'
    BASE_LOG_PATH = "/var/log"
    LOGGING_FILE_NAME = APPLICATION + ".log"
    LOGGING_FORMAT = "%(asctime)s loglevel=%(levelname)-s\tlogger=%(module)s\tline=%(lineno)d:\t%(message)s"
    log_handler = logging.handlers.RotatingFileHandler(os.path.join(BASE_LOG_PATH, LOGGING_FILE_NAME), mode='a')
    log_handler.setFormatter(logging.Formatter(LOGGING_FORMAT))
    logger.addHandler(log_handler)
    return logger


# logger = setup_logging()
# logger.info("logger is setup")


# argument parsing
def setup_args():
    parser = argparse.ArgumentParser()
    # parser.add_argument("-t", "--type", choices=['json', 'html'])
    parser.add_argument("-x", "--authentication", action="store_true",
                        help="defaults to technical account, can be used to override")
    parser.add_argument("-c", "--configfile", help="use provided configfile")
    parser.add_argument("-q", "--quiet", action="store_true", help="do not output informational data")
    subparsers = parser.add_subparsers(title='Subcommands')

    subparser_get = subparsers.add_parser('get')
    subparser_get.add_argument("space", help="space which contains the page")
    subparser_get.add_argument("page", help="page which should be handled")
    subparser_get.set_defaults(mode="get")

    subparser_put = subparsers.add_parser('put')
    subparser_put.add_argument("space", help="space which contains the page")
    subparser_put.add_argument("page", help="page which should be handled")
    subparser_put.add_argument("file", type=argparse.FileType('r'), help="file containing html code", default=sys.stdin,
                               nargs='?')
    subparser_put.add_argument("-p", "--parent", help="add as child of parent")
    # subparser_put.add_argument("-r", "--remove", help="remove the old, unused Version")
    subparser_put.set_defaults(mode="put")

    subparser_version = subparsers.add_parser('version')
    subparser_version.set_defaults(mode="version")

    args = parser.parse_args()
    return args, parser


def setup_config():
    config = ConfigParser.RawConfigParser()
    config.read(CONFIGFILE)

    try:
        global CONFLUENCE_USER_NAME
        global CONFLUENCE_USER_PASSWORD
        CONFLUENCE_USER_NAME = config.get('auth', 'username')
        CONFLUENCE_USER_PASSWORD = config.get('auth', 'password')
    except ConfigParser.NoSectionError as e:
        doError('ERROR: message="Section not found" section=auth')
        sys.exit(1)
    except ConfigParser.NoOptionError as e:
        doError('ERROR: message="Option not found" section=auth option=passwd')
        sys.exit(1)

    try:
        global VERIFY
        truststore = config.get('request', 'truststore')
        if (type(truststore) == str and os.path.isfile(truststore)):
            VERIFY = truststore
        else:
            doError('ERROR: message="Not a valid file" file={0} fallback="no ssl verification"'.format(truststore))
    except ConfigParser.NoSectionError as e:
        doError('ERROR: message="Section not found" section=request fallback="no ssl verification"')
    except ConfigParser.NoOptionError as e:
        doError('ERROR: message="Option not found" section=request option=truststore fallback="no ssl verification"')
    except:
        doError('ERROR: message="any other config parsing error" section=request option=truststore')

    try:
        global RESTAPI
        RESTAPI = config.get('confluence', 'restapi')
    except ConfigParser.NoSectionError as e:
        doError('ERROR: message="Section not found" section=confluence')
        sys.exit(1)
    except ConfigParser.NoOptionError as e:
        doError('ERROR: message="Option not found" section=confluence option=restapi')
        sys.exit(1)
    except:
        doError('Error: message="any other config parsing error" section=confluence option=restapi')


# doInfo if not QUIET
def doInfo(message):
    if not QUIET:
        print(str(datetime.datetime.now()) + " " + message)
    return 0


# doError
def doError(message):
    #print(str(datetime.datetime.now()) + " " + message)
    sys.stderr.write(str(datetime.datetime.now()) + " " + message + "\n")
    return 0


# doPrettyPrint if not QUIET
def doPrettyPrint(message):
    if not QUIET:
        pprint.pprint(message)
    return 0


# get JSON data by space and page
def getPayload(space, page):
    query = "{0}".format(RESTAPI)
    params = {
        "expand": "body.storage,version,body.storage.content.space",
        "space": space,
        "title": page
    }
    payload = getData(query, params)
    return payload, payload['size'] > 0


def pagesIdentical(currentContent, newContent):
    # print("current:")
    # print(currentContent.rstrip())
    # print("NewContent:")
    # print(newContent.rstrip())
    # print(currentContent.rstrip() == newContent.rstrip())
    # exit(99)
    #print(make_unicode(currentContent.rstrip()) == make_unicode(newContent.rstrip())) # somehow still throws error
    currentContent = make_unicode(currentContent)
    newContent = make_unicode(newContent)
    return (currentContent.rstrip() == newContent.rstrip())

def make_unicode(astring):
    if type(astring) != type(u'unicodestring'):
        astring = astring.decode('utf-8')
    return astring


# getVersion from payload
def getVersionByPayload(payload):
    return payload['results'][0]['version']['number']


# getID from payload
def getIdByPayload(payload):
    return payload['results'][0]['id']


# getSpace form payload
def getSpaceByPayload(payload):
    return payload['results'][0]['body']['storage']['content']['space']['name']


# getTitle from payload
def getTitleByPayload(payload):
    return payload['results'][0]['title']


# get ID from page by space and name
def getId(space, page):
    payload = getPayload(space, page)
    return getIdByPayload(payload)


# get authentification information
def getAuthenticationInformation():
    username = input("Enter username: ")
    userpw = getpass.getpass()
    return username, userpw


# get all meta data
def getMetadataByPayload(payload):
    id = getIdByPayload(payload)
    version = getVersionByPayload(payload)
    return id, version


# get data
def getData(query, params):
    query = "{0}".format(RESTAPI)
    myparams = params
    r = requests.get(
        query,
        auth=(CONFLUENCE_USER_NAME, CONFLUENCE_USER_PASSWORD),
        verify=VERIFY,
        params=myparams)
    payload = "";
    # noinspection PyBroadException
    try:
        payload = json.loads(r.text)
    except:
        pass
    return payload


# post data (create)
def postData(query, data):
    r = requests.post(query,
                      headers=HEADERS,
                      data=data,
                      verify=VERIFY,
                      auth=(CONFLUENCE_USER_NAME, CONFLUENCE_USER_PASSWORD))
    return r


# put data (update)
def putData(query, data):
    r = requests.put(query,
                     headers=HEADERS,
                     data=data,
                     verify=VERIFY,
                     auth=(CONFLUENCE_USER_NAME, CONFLUENCE_USER_PASSWORD))
    return r


# delete data (delete)
def deleteData(query):
    r = requests.delete(query,
                        headers=HEADERS,
                        verify=VERIFY,
                        auth=(CONFLUENCE_USER_NAME, CONFLUENCE_USER_PASSWORD))
    return r


def createPage(space, page, content, parent_id=None):
    query = "{0}".format(RESTAPI)
    data = {
        "type": "page",
        "title": page,
        "space": {
            "key": space,
        },
        "body": {
            "storage": {
                "value": content,
                "representation": "storage"
            }
        }
    }
    if parent_id is not None:
        ancestors = [{'id': parent_id}]
        data['ancestors'] = ancestors
    doInfo("Putting data for space={0} page={1} ...".format(space, page))
    return postData(query, json.dumps(data))


def updatePage(payload, newContent):
    currentContent = payload['results'][0]['body']['storage']['value']
    doInfo("comparing for identical content...")
    if not pagesIdentical(currentContent, newContent):
        doInfo("Content not identical, will put new content")
        query = "{0}/{1}".format(RESTAPI, getIdByPayload(payload))
        data = {
            "id": str(getIdByPayload(payload)),
            "type": "page",
            "title": getTitleByPayload(payload),
            "version": {
                "number": str(getVersionByPayload(payload) + 1),
            },
            "body": {
                "storage": {
                    "representation": "storage",
                    "value": newContent,
                }
            }
        }
        doInfo("Putting data for page={0}".format(getTitleByPayload(payload)))
        doInfo("data={0}".format(json.dumps(data)))
        return putData(query, json.dumps(data))
    else:
        doInfo("currentContent identical with newContent, will not update page!")
        return False


def deletePageByPayload(payload):
    query = "{0}/{1}".format(RESTAPI, getIdByPayload(payload))
    doInfo("Deleting page={0} ...".format(getTitleByPayload(payload)))
    return deleteData(query)


def getHistory(page_id):
    query = "{0}/{1}/version".format(RESTAPI, page_id);  # TODO: Natii: For the new Confluence Version
    params = {
        # "expand": "previousVersion",
        # "space": space,
        # "title": page
    }
    doInfo("Getting History of page_id={0} query={1}".format(page_id, query))
    return getData(query, params)


# MAIN
if __name__ == "__main__":
    # parse arguments
    args, parser = setup_args()
    # output version
    if (args.mode == 'version'):
        print(VERSION)
        sys.exit(0)
    # setup space and page
    space = args.space
    page = args.page
    if args.quiet:
        QUIET = True
        devnull = open(os.devnull,'w')
        sys.stdout = devnull

    # set correct configfile if is set
    if type(args.configfile) == str and os.path.isfile(args.configfile):
        CONFIGFILE = args.configfile
    # get configuration parameters from config file
    setup_config()
    # get non-standard user information if given
    if (args.authentication):
        CONFLUENCE_USER_NAME, CONFLUENCE_USER_PASSWORD = getAuthenticationInformation()
    # get payload and id
    doInfo("Getting payload of space={0} page={1} ...".format(space, page))
    payload, pageAlreadyExists = getPayload(space, page)
    if pageAlreadyExists:
        page_id, page_version = getMetadataByPayload(payload)
        doInfo("Page does already exist: space={0} page={1}, page_id={2}, page_version={3} ...".format(space, page,
                                                                                                       page_id,
                                                                                                       page_version))

    # print(payload);
    # print (page_id);
    # print(getHistory(page_id));
    # sys.exit(2)

    # do action based on get/put
    if args.mode == 'get':
        if pageAlreadyExists:
            print(payload['results'][0]['body']['storage']['value'])
        else:
            doError('message="Page not found" space={0} page={1}'.format(space, page))
            sys.exit(1)
    elif args.mode == 'put':

        # check whether file exists
        file = args.file
        if file is file:
            pass
        elif file is str and not os.path.isfile(file):
            doError('message="Not a valid file" file={0}'.format(file))
            sys.exit(1)
        elif file is str and os.path.isfile(file):
            file = open(file)
        else:
            doError('message="Not a valid file" file={0}'.format(file))
            sys.exit(1)

        # read content from file
        content = file.read()
        file.close()

        # check whether pages needs creation or update
        if pageAlreadyExists:  # page needs update
            r = updatePage(payload, content)
            # doPrettyPrint(json.loads(r.text))
            if type(r) is not type(False):
                # only if request is done, else it will contain False (identical content, no update needed)
                # check is done this strangely because of strangely behaviour, see end of script (1)
                text = json.loads(r.text)
                if "statusCode" in text and text['statusCode'] == 500 and "message" in text and text['message'] == "java.lang.IllegalArgumentException: Property with name sync-rev is not a String":
                    doInfo("Bug workaround for space={0} page={1} message=\"{2}\" workaround=\"Delete page and create from anew\"".format(space,page,text['message']))
                    r = deletePageByPayload(payload)
                    if type(r) is not type(False):
                        doInfo(r.text)
                    parent_payload,parentPageAlreadyExists = getPayload(space, args.parent)
                    parent_id, parent_version = getMetadataByPayload(parent_payload)
                    r = createPage(space,page,content,parent_id)
                    if type(r) is not type(False):
                        doInfo(r.text)
        else:  # page needs creation
            # set parentid if parentid given
            parentPageAlreadyExists = False
            parent = None
            parent_id, parent_version = None, None
            if args.parent is not None:
                parent = args.parent
                doInfo("Getting payload of parent space={0} page={1}".format(space, args.parent))
                parent_payload, parentPageAlreadyExists = getPayload(space, args.parent)
                parent_id, parent_version = getMetadataByPayload(parent_payload)
                if not parentPageAlreadyExists:
                    doError('message="Parent page does not exist" space={0} page={1}'.format(space, args.parent))
            if parentPageAlreadyExists:  # page has ancestor
                r = createPage(space, page, content, parent_id)
                doPrettyPrint(json.loads(r.text))
            else:  # page has no ancestor
                r = createPage(space, page, content)
                doPrettyPrint(json.loads(r.text))
        pass

    else:
        pass

    # exit
    sys.exit(0)

###
# Out of Code Explanations
#
### (1)
# >>> r = False
# >>> type(r)
# <type 'bool'>
# >>> r is bool
# False
# >>> type(r) == type(False)
# True
#
###
