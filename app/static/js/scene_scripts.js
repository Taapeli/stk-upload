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

	this.findCitations = function(textDest,tblDest) {
		// Search html <sup> tags and add the citations to this.cTbl.
		var x = document.getElementsByTagName("sup");
		var i;
		var ret = "";
		for (i = 0; i < x.length; i++) {
			var a = x[i].firstElementChild;
			if (a != null) {
			    ret += " " + x[i].innerText;
				if (a.nodeName == "A" && a.id != "" ) {
					// <sup><a id="{{obj[cr].source_id}}-{{obj[cr].uniq_id}}">*</a>
				    var arr = a.id.split('-');
				    mark = this.add(Number(arr[0]), Number(arr[1]));
				    a.href = "#sref" + mark;
				    a.innerText = mark;
				    ret += mark + ">" + a.id + '<br>';
				} else { ret += '<br>' }
			}
		}
		document.getElementById(textDest).innerHTML = ret;
		// Show citation refeference table
		this.listCitations(tblDest);
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
				// Show new Source
				// 	sources[312820] = { id:"S0408", note_ref:[], repositories:[316840],
				//		sauthor:"", spubinfo:"", stitle:"Askainen kuolleet 1888-1890", 
				//		uuid:"f83d3ff5c5cb49f1a71060b9456ab59e" };
				//
		        // <a href="/scene/source=208153" class="inlink" title="[C0866] Lähteen S1418 tiedot">
		        //    Taivassalon seurakunnan syntyneiden ja kastettujen luettelot 1790-1850 (I C:4)</a>
				source_id = line[0];
				var sObj = sources[source_id];

				var nodeSource = document.createElement("DIV");
				nodeSource.setAttribute("class", "sourceDesc");
				//nodeSource.style.color = "green";
				t.appendChild(nodeSource);

				var nodeA = document.createElement("A");
				nodeA.href = '/scene/source=' + source_id;
				nodeA.setAttribute("class", "inlink");
				nodeA.setAttribute("title", "Lähteen " + sObj.id + " tiedot");
				var textnode = document.createTextNode(sObj.stitle);
				nodeA.appendChild(textnode);
				nodeSource.appendChild(nodeA);
				nodeSource.appendChild(document.createTextNode(' – '));
				
				// Todo: citation.source_medium:"book" siirrettävä Source-nodeen?
				// 	– <span class="typedesc">kirja</span>
				var nodeMedium = document.createElement("SPAN");
				nodeMedium.setAttribute("class", "typedesc");
				textnode = document.createTextNode("(medium)");
				nodeMedium.appendChild(textnode);
				nodeSource.appendChild(nodeMedium);
				
				// Todo: repository
				// <i>Taivassalon seurakunnan arkisto</i>
				var nodeRepo = document.createElement("I");
				var textnode = document.createTextNode(" (arkisto)");
				nodeSource.appendChild(textnode);

//			    <div class="sourceDesc">	<!-- Source {{ clist.grouper }} -->
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

			// Show Citations defined by
			// 	citations[395801] = { confidence:"2", dates:"–", id:"C0867", 
			//		note_ref:[442899], page:"sivu 115", source_id:312820, 
			//		source_medium:"Book",uuid:"5eab898287ed42289890d5b9020ec2e3"};
			//
			// <div class="citaDesc" id="sref 2b">
            //   <span title="[C0866] normaali luottamustaso (2)">
            //     <b> 2b</b> Sivu: Vigde år 1828 October 28 &nbsp; ★★☆☆☆
			//   </span> 
            //   &nbsp;►&nbsp;<a href="http://digi.narc.fi/digi/view.ka?kuid=5364234"
            //     class="outlink" target="_blank">digi.narc.fi</a> –
			// </div>
			for (j=0; j<line[1].length; j++) {
				var mark = this.getMark(i, j);
				cita_id = line[1][j];
				var cObj = citations[cita_id];

				var nodeCitaDiv = document.createElement("DIV");
				nodeCitaDiv.setAttribute("id", "sref" + mark);
				nodeCitaDiv.setAttribute("class", "citaDesc");
				nodeSource.appendChild(nodeCitaDiv);
				
				var nodeCitaSpan = document.createElement("SPAN");
				nodeCitaSpan.setAttribute("title", cObj.id + " luottamustaso " + cObj.confidence);
				
				var nodeCitaB = document.createElement("B");
				nodeCitaB.appendChild(document.createTextNode(mark + ' '));
				nodeCitaSpan.appendChild(nodeCitaB);
				var text = cObj.page + " " + stars(cObj.confidence);
				nodeCitaSpan.appendChild(document.createTextNode(text));
				nodeCitaDiv.appendChild(nodeCitaSpan);

				if (cObj['note_ref']) {
					text = " ► note " + cObj.note_ref + " ";
					nodeCitaDiv.appendChild(document.createTextNode(text));
					
					var nodeNoteA = document.createElement("A");
					nodeNoteA.setAttribute("class", "inlink");
					nodeNoteA.setAttribute("target", "_blank");
					nodeNoteA.setAttribute("href", "#");
					nodeNoteA.appendChild(document.createTextNode("(example.org)"));
					nodeCitaDiv.appendChild(nodeNoteA);
				}
			}
		}
	}
}

function stars(value) {
	// Returns stars ★★☆☆☆ according to value 0..4
	var ret = '';
	var x = parseInt(value);
	for (i = 0; i < 5; i++) {
		if (x > i) 	{ ret += '★' }
		else 		{ ret += '☆' }
	}
	return ret;
}
