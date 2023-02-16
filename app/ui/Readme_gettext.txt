Created on 16.2.2023
@author: JMä


Using language dependent phrases

	Python code:
		from flask_babelex import _
		
	Common syntax in flask:
		gettext() is aliased as _()


New style gettext make formatting part of the call,
and behind the scenes enforce more consistency.

Usage in templates:
	
	{{ gettext("Hello, World!") }}
	{{ gettext("Hello, %(name)s!", name=name) }}
	{{ ngettext("%(num)d apple", "%(num)d apples", apples|count) }}
	{{ pgettext("greeting", "Hello, World!") }}
	{{ npgettext("fruit", "%(num)d apple", "%(num)d apples", apples|count) }}


Usage in messages.po:

# Basic
msgid "{}between {} … {}"
msgstr "{}välillä {} … {}"

#, python-format
msgid "Removed %(cnt)d nodes"
msgstr "Poistettu %(cnt)d nodea"

#, python-format
msgid "count=%(num)d, line %(lines)s"
msgid_plural "count=%(num)d, lines %(lines)s"
msgstr[0] "%(num)d kpl, rivillä %(lines)s"
msgstr[1] "%(num)d kpl, riveillä %(lines)s"
