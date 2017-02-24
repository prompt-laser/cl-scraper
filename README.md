# cl-scraper

This will look for it's config file in the directory the script is running in. It's looking for a file called 'settings'

This will look for the URLs in the file specified by the 'cities=' config line.

This will look for the search terms in the file specified by the 'search=' config line.

It will write the results to 'index.html' at the path specified by the 'doc_root=' attribute of the settings file. It will overwrite any file called 'index.html'.

NOTE: If the doc_root is in a folder that requires escalated privileges to write to, the script will have to be run with sudo or as root.
