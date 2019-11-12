coverage run --source app/bp/gedcom -m pytest -vv  -k test_gedcom
coverage report

#coverage run --source app/bp/start -m pytest -vv -k test_start  
#coverage report

coverage html 