# bug workaround; https://github.com/pypa/setuptools/issues/523
pip install setuptools==34.00

mkdir translations || echo "translations directory ok"
pybabel extract -F babel.cfg -k _l -o messages.pot .
if ! test -e translations/fi
then
   pybabel init -i messages.pot -d translations -l fi
fi
if ! test -e translations/en 
then
   pybabel init -i messages.pot -d translations -l en
fi
if ! test -e translations/sv
then
   pybabel init -i messages.pot -d translations -l sv
fi
pybabel update -i messages.pot --ignore-obsolete -d translations

cp -p translations/fi/LC_MESSAGES/messages.po static/translations/fi.po
cp -p translations/sv/LC_MESSAGES/messages.po static/translations/sv.po
cp -p translations/en/LC_MESSAGES/messages.po static/translations/en.po
