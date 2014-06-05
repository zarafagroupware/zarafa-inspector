Zarafa Inspector
================

Zarafa Inspector is a GUI application which can be used to "look into" Zarafa. It's similiar to OutlookSpy and MFCMAPI but it's Zarafa specific. (This program isn't actively supported by Zarafa)

![Zarafa-Inspector](https://raw.githubusercontent.com/zarafagroupware/zarafa-inspector/master/images/zarafa-inspector.png "Zarafa-inspector example usage")

Features
========

The Zarafa Inspector supports:

* Listing all users on a Zarafa Server
* Viewing the UserStore of a user
* Viewing the properties of a folder
* Viewing the properties of a record
* Showing the attachmenttable of a record
* Exporting an attachment
* Exporting an email as EML
* Exporting a folder as MBOX

Dependencies
============

Zarafa-Inspector depends on a few Python libraries:

* pyqt4
* [python-mapi](http://download.zarafa.com/community/final/7.1/7.1.9-44333/)
* [python-zarafa](https://github.com/zarafagroupware/python-zarafa.git)

Apart from these Python dependencies the tool only works running zarafa-server.

Usage
=====

    git clone https://github.com/zarafagroupware/zarafa-inspector.git 
    cd zarafa-inspector
    make (Needed to generate Python code from the Qt ui file)
    python zinspector.py (requires root permissions to connect to the socket for an system session)

Connet to remote server
=======================

    python zinspector.py  -s https://serverip:237/zarafa -k /etc/zarafa/ssl/server.pem -p password
