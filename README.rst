collective.autoqueryplan
====================

.. image:: https://secure.travis-ci.org/collective/collective.autoqueryplan.png
   :target: http://travis-ci.org/collective/collective.autoqueryplan

*collective.autoqueryplan* dumps a json version of all the zcatalogs queryplans
to a file on disk periodically. If this file is found during load then it is
used to prime the catalogs query plans instead of the queryplan specified in
```ZCATALOGQUERYPLAN``` or having an empty queryplan (zopes default).

The advantage of a queryplan is it can help speedup catalog searches and reduce
unneeded ZODB loads by knowing more about most common queries an instance is
making. ```ZCATALOGQUERYPLAN``` allows for a single snapshot applied across
all instances and has to be manually updated. Autoqueryplan allows for
different instances to have different queryplans overtime and doesn't
require any intervention. For example p.a.async worker instances can have
very different query patterns.

Minimal configuration:

.. code:: ini

    zope-conf-additional =
            <clock-server>
               method /@@dumpqueryplan
               period 3600
            </clock-server>


Advanced configuration
----------------------

By default the file is stored in ${client_home}/queryplan.json. You can override this with the environment variable:

``AUTOQUERYPLAN`` *(default=${client_home}/queryplan.json)*
    Where to dump and load queryplan json from
