# putConfluence

## Setup

1. Add Basic Authentification information to your putConfluence.conf file
2. Ready!

## Usage Examples

```
./putConfluence.py get SPLUNK cisas.conf
./putConfluence.py -c ./putConfluence.conf get SPLUNK cisas.conf
./putConfluence.py put -p "Konfigurierte Logfiles" SPLUNK cisas.conf cisas.html
cat cisas.html | ./putConfluence.py put -p "Konfigurierte Logfiles" SPLUNK cisas.conf
./putConfluence.py put -p "Konfigurierte Logfiles" SPLUNK cisas.conf < cisas.html
```

where

* `SPLUNK` is the Space
* `cisas.conf` is the name of the page
* `cisas.html` is the file with the desired content
* `putconfluence.conf` is a valid configuration file of format seen in next chapter


## Configuration File Specification sofar

```
# The auth stanza contains login information of the technical user
[auth]
username=<username>
password=<password>

# The request stanza contains information on how the connection should be built
[request]
truststore=<path to truststore>
# If a valid path to a truststore was set, the ssl connection to the Confluence
# webserver will be verified. If no truststore was set, the connection will not
# be verified. This is the standard behaviour.

# The confluence stanza contains connection information for confluence
[confluence]
restapi=https://confluence.example.com/rest/api/content
```

## Daily Update

Make a Cronjob like this:

```bash
0 6 * * * /opt/splunk/bin/doPutConfluence.sh -c
```

The script `doPutConfluence.sh` may be found in the `src` directory of this repository.

## Known Issues

* Special Characters can't be sent by POST or PUT
* Error occurs when updating a page without `-p` option, when it was created with `-p` option
* Can't use -x option in conjunction with STDIN file

## References

### Confluence REST API & Examples

* https://docs.atlassian.com/confluence/REST/latest/
* https://developer.atlassian.com/confdev/confluence-server-rest-api
* https://developer.atlassian.com/confdev/confluence-server-rest-api/confluence-rest-api-examples
* https://developer.atlassian.com/static/connect/docs/latest/scopes/confluence-rest-scopes.html

### Python ArgParse

* https://docs.python.org/3/library/argparse.html
* https://docs.python.org/3/howto/argparse.html

### Python File Object

* https://docs.python.org/2/tutorial/inputoutput.html

### Python Configuration Parser

* https://docs.python.org/2/library/configparser.html

### Python Requests

* http://docs.python-requests.org/en/latest/index.html

### JSON Formatter

* http://jsonviewer.stack.hu/
