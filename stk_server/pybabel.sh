# bug workaround; https://github.com/pypa/setuptools/issues/523
pip install setuptools==34.00

mkdir translations
pybabel extract -F babel.cfg -k _l -o messages.pot .
if ! test -e translations/en 
then
   pybabel init -i messages.pot -d translations -l en
fi
if ! test -e translations/sv
then
   pybabel init -i messages.pot -d translations -l sv
fi
pybabel update -i messages.pot -d translations
