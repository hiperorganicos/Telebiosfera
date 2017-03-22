#!/bin/sh
#FreeDNS updater script

wget -q --read-timeout=0.0 --waitretry=5 --tries=2 --background http://freedns.afraid.org/dynamic/update.php?[UPDATE-KEY] -O /dev/null
