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


// --------- Manage Source Citations by citTable object ----------

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
		var sups = document.getElementsByTagName("sup");
		var i, j, node, nodes, ret = "";
		for (i = 0; i < sups.length; i++) {
			nodes = sups[i].childNodes;
			for (j = 0; j < nodes.length; j++) {
				node = nodes[j];
				if (node.nodeName == "A" && node.id != "" ) {
					// <sup><a id="{{obj[cr].source_id}}-{{obj[cr].uniq_id}}">*</a>
				    var arr = node.id.split('-');
				    // Store source and citation ids
				    mark = this.add(Number(arr[0]), Number(arr[1]));
				    node.href = "#sref" + mark;
				    node.innerText = mark;
				    ret += mark + ">" + node.id + '<br>';
				}
			}
		}
		if (textDest) {
			document.getElementById(textDest).innerHTML = ret;
		}
		if (tblDest) {
			// Show citation refeference table
			this.listCitations(tblDest);
		}
	}


	this.sourceReferences = function(destination) {
		//
		// Display the Source / Citations reference table.
		//
		var t = document.getElementById(destination);
		var source_id;
		var cita_id;
		var citas;	// List of citation ids for current source
		var mark;	// citation index like "1a"

		var sObj;	// Source from database
		var cObj;	// Citation from database
		var i, j;

		for (i = 0; i < this.cTbl.length; i++) {
			// line is [source_id, [cita_id, ...]], one line per each source
			line = this.cTbl[i];

			// Next Source

			// 	sources[312820] = { id:"S0408", note_ref:[], repositories:[316840],
			//		sauthor:"", spubinfo:"", stitle:"Askainen kuolleet 1888-1890", 
			//		uuid:"f83d3ff5c5cb49f1a71060b9456ab59e" };
			//
	        // <a href="/scene/source=208153" class="inlink" title="[C0866] Lähteen S1418 tiedot">
	        //    Taivassalon seurakunnan syntyneiden ja kastettujen luettelot 1790-1850 (I C:4)</a>
			source_id = line[0];
			sObj = sources[source_id];
			if ( !(sObj instanceof Object) ) {
				console.log("ERROR No data for source " + source_id);
				break;
			}

			var nodeSource = document.createElement("DIV");
			nodeSource.setAttribute("class", "sourceDesc");
			//nodeSource.style.color = "green";
			t.appendChild(nodeSource);

			var nodeSourceA = document.createElement("A");
			nodeSourceA.href = '/scene/source=' + source_id;
			nodeSourceA.setAttribute("class", "inlink");
			nodeSourceA.setAttribute("title", "Lähteen " + sObj.id + " tiedot");
			var textnode = document.createTextNode(sObj.stitle);
			nodeSourceA.appendChild(textnode);
			nodeSource.appendChild(nodeSourceA);
			nodeSource.appendChild(document.createTextNode(' – '));
			
			// Todo: citation.source_medium:"book" siirrettävä Source-nodeen?
			// 	– <span class="typedesc">kirja</span>
			var nodeMedium = document.createElement("SPAN");
			nodeMedium.setAttribute("class", "typedesc");
			textnode = document.createTextNode("(medium)");
			nodeMedium.appendChild(textnode);
			nodeSource.appendChild(nodeMedium);
			
			// Todo: repository <i>Taivassalon seurakunnan arkisto</i>
			var nodeRepo = document.createElement("I");
			textnode = document.createTextNode(" (arkisto)");
			nodeSource.appendChild(textnode);

			citas = line[1];	// = this.cTbl[i,j]
			//console.log("Citations "+ citas +" of source " + source_id);
			for (j = 0; j < citas.length; j++) {
				cita_id = citas[j];

				// Next citation

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
	
				mark = this.getMark(i, j);
				cObj = citations[cita_id];
				if ( !(sObj instanceof Object) ) {
					console.log("ERROR No data for citation "+ cita_id +" of source " + source_id);
					break;
				}
				//console.log("Citation[" + i + "," + j + "] " + cObj.id);

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

				if (cObj.note_ref) {
					var text = " ► note " + cObj.note_ref + " ";
					nodeCitaDiv.appendChild(document.createTextNode(text));

					var nodeNoteA = document.createElement("A");
					nodeNoteA.setAttribute("class", "inlink");
					nodeNoteA.setAttribute("target", "_blank");
					nodeNoteA.setAttribute("href", "#");
					nodeNoteA.appendChild(document.createTextNode("(example.org)"));
					nodeCitaDiv.appendChild(nodeNoteA);
				}

			}
			line = undefined;
		}
	} // sourceReferences()

}

