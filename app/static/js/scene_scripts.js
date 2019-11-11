var gt = new Gettext({domain: 'gedcom_transformations'});
var _ = function(msgid,args) { return gt.strargs(gt.gettext(msgid),args); };
var ngettext = function(msgid, msgid_plural, n) { return gt.ngettext(msgid, msgid_plural, n); };
	
function jump(initial) {
	// Jump to a #id address and scroll a little back (for person_list.html etc)
	var elem = $("a[name="+initial+"]");
    var rect = elem.get(0).getBoundingClientRect();
	var y = rect.top;
	window.scroll(0,window.scrollY+y-30);
};

var cit_tbl = ["rivi1", "rivi2"];
//Table of citations (for person.html etc)

function citTable() {
	// Manage citations table and indexes "1a", ... for each.
	this.cTbl = [];

	this.getMark = function (i, j) {
		// Create mark "1a" for given cTbl line and citation column
	    return (i + 1) + "abcderfghijklmopqrstuvwxyzåäö"[j];
	}

	this.add = function(s_id, c_id) {
		// Adds a citation to source.
		// The lines of this.cTbl are arrays [source_id, [citation_id, ...]]
	    //this.mark = (s_id + 1) + "abcderfghijklmopqrstuvwxyzåäö"[c_id];
		var line;
		var l = this.cTbl.length;
		var j = -1;	// Index of selected citation
		for (i = 0; i < l; i++) {
			// Browse sources
			line = this.cTbl[i];
			if (line[0] == s_id) {
				var cits = line[1];
				var j = cits.indexOf(c_id);
				if (j < 0) {
					// No match; add a new citation to this source
					var z = this.cTbl[i][1]
					j = z.length
					z.push(c_id);
				}
				return this.getMark(i, j);
			}
		}
		line = [s_id, [c_id]];
		this.cTbl.push(line);
		return this.getMark(this.cTbl.length - 1, 0)
	}

	this.listCitations = function(destination) {
		// Display citations table in destination element.

		var t = document.getElementById(destination);
		t.innerHTML = "<tr><th>mark</th><th>source</th><th>citation (a,b,…)</th></th><tr>";

		var l = this.cTbl.length;
		for (i = 0; i < l; i++) {
			line = this.cTbl[i];
			t.innerHTML += "<tr><td>" + (i + 1) + "x</td><td>" + 
				line[0] + "</td><td>" + line[1] + "</td><tr>";
		}
		console.log("Citation table=" + this.cTbl);
	}

	this.findCitations = function(textDest) {
		// Search html <sup> tags and add the citations to this.cTbl.
		var x = document.getElementsByTagName("sup");
		var i;
		var ret = "";
		for (i = 0; i < x.length; i++) {
		    ret += " " + x[i].innerText;
			var a = x[i].firstElementChild;
			if (a.nodeName == "A" && a.id != "" ) {
				// <sup><a id="{{obj[cr].source_id}}-{{obj[cr].uniq_id}}">*</a>
			    var arr = a.id.split('-');
			    mark = this.add(Number(arr[0]), Number(arr[1]));
			    a.href = "#sref" + mark;
			    a.innerText = mark;
			    ret += mark + ">" + a.id + '<br>';
			} else { ret += '<br>' }
		}
		document.getElementById(textDest).innerHTML = ret;	// Text result
	}

	this.sourceReferences = function(destination) {
		// Display citations table in destination element.

		var t = document.getElementById(destination);
		this.cTbl.sort(function(a, b){return a[0]-b[0]});
		
		var l = this.cTbl.length;
		var source_id = -1;
		for (i = 0; i < l; i++) {
			line = this.cTbl[i];
			if (line[0] != source_id) {
				// New Source
				source_id = line[0];
				var nodeA = document.createElement("A");
				var textnode = document.createTextNode(" Lähde " + source_id);
				nodeA.href = '/scene/source=' + source_id;
				nodeA.appendChild(textnode);
				var nodeSource = document.createElement("DIV");
				nodeSource.setAttribute("class", "sourceDesc");
				nodeSource.style.color = "green";
				nodeSource.appendChild(nodeA);
				t.appendChild(nodeSource);

//			    <div class="sourceDesc"><!-- Source {{ clist.grouper }} -->
//		        {% set c = clist.list[0] %}
//		        {% if c.source_id %}{% set source = obj[c.source_id] %}
//		                   <a href="/scene/source={{source.uniq_id}}" class="inlink"
//		                      title="[{{c.id}}] {{ _('See source %(name)s details', name=source.id) }}">
//		                      {{source.stitle}}</a>
//			            <!-- Repository -->
//			            {% if source.repositories %} –
//			               <span class="typedesc">{{ c.source_medium|transl('medium') }}</span>
//			               <i>{{obj[source.repositories[0]].rname}}</i>
//		                   {% if source.repositories|length > 1 %}<b> JA MUITA ARKISTOJA</b>{% endif %}
//			            {% else %}  <b title="{{source}}">{{ _("No archive information!") }}</b>
//			            {% endif %}
//		        {% else %}<b title="{{c}}">{{ _("No source information!") }}</b>
//		        {% endif %}
			}
			// Show Citations
			for (j=0; j<line[1].length; j++) {
				var mark = this.getMark(i, j);
				var nodeB = document.createElement("B");
				var textnode = document.createTextNode(mark + ' ');
				nodeB.appendChild(textnode);
				
				var nodeA = document.createElement("SPAN");
				nodeA.appendChild(nodeB);
				var textnode = document.createTextNode("Page X");
				nodeA.appendChild(textnode);

				var nodeB = document.createElement("DIV");
				nodeB.setAttribute("class", "citaDesc");
				nodeB.id = "sref" + mark;
				nodeB.appendChild(nodeA);

				nodeSource.appendChild(nodeB);
				
//			 <div class="citaDesc" id="sref{{ cita.mark|trim }}" ...>
//	            <span title="[{{cita.id}}] {{cita.confidence|transl("conf")}} {{ _('confidence') }} ({{cita.confidence}})">
//	                <b>{{ cita.mark }}</b> {{ _("Page") }}: {{cita.page}} &nbsp; {{ macro.stars(conf) }}
//	            </span> {{ cita.noteref }}
//	          {% for nref in cita.note_ref %} &nbsp;►&nbsp;{{ macro.notelink(obj[nref]) }}
//	          {% endfor %}
//	         </div>;
			}
		}
		console.log("Citation table=" + this.cTbl);
	}
}

