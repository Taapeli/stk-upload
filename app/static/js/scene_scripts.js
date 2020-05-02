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
	// Returns stars ★★☆☆ according to value 0..4, where 2 = normal
	var ret = '';
	var x = parseInt(value);
	for (i = 0; i < 4; i++) {
		if (x > i) 	{ ret += '★' }
		else 		{ ret += '☆' }
	}
	return ret;
}


// --------- Manage Source Citations and Notes by refTable object ----------

function refTable() {
	// Manage citations table and indexes "1a", ... for each.
	// Manage notes table and indexes "i", "ii", ... for each.
	this.cTbl = [];
	this.nTbl = [];

	this.getCiteMark = function (i, j) {
		// Create mark "1a" for given cTbl line and citation column
	    return (i + 1) + "abcderfghijklmopqrstuvwxyzåäö"[j];
	}

	this.getNoteMark = function (i) {
		// Create mark "1" for given nTbl row
	    return "" + (i + 1);
	}


	this.addC = function(s_id, c_id) {
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
				return this.getCiteMark(i, j);
			}
		}
		line = [s_id, [c_id]];
		this.cTbl.push(line);
		return this.getCiteMark(this.cTbl.length - 1, 0)
	}

	this.addNote = function(noteId, url, text, rType) {
		// Adds a note reference.
		// Table this.nTbl rows has 4 elements: [uniq_id, url, text, rType]
		var line;
		var l = this.nTbl.length;
		for (i = 0; i < l; i++) {
			// Browse Notes
			line = this.nTbl[i];
			if (line[0] == noteId) {
				return this.getNoteMark(i, line);
			}
		}
		// No match; add a new note reference
		line = [noteId, url, text, rType]
		this.nTbl.push(line);
		return this.getNoteMark(this.nTbl.length - 1)
	}


	this.listCitations = function(destination) {
		// Display citations table in destination element.

		var t = document.getElementById(destination);
		var line;
		t.innerHTML = "<tr><th>mark</th><th>source</th><th>citation (a,b,…)</th><tr>";

		var l = this.cTbl.length;
		for (i = 0; i < l; i++) {
			line = this.cTbl[i];
			t.innerHTML += "<tr><td>" + (i + 1) + "x</td><td>" + 
				line[0] + "</td><td>" + line[1] + "</td><tr>";
		}
		console.log("Citation table=" + this.cTbl);
	}


	this.listNotes = function(destination) {
		// Display notes table in destination element.

		var t = document.getElementById(destination);
		var line;
		t.innerHTML = "<tr><th>mark</th><th>id</th><th>url</th><th>text</th><th>type</th><tr>";

		var l = this.nTbl.length;
		for (i = 0; i < l; i++) {
			//noteId, url, text, rType = this.nTbl[i];
			line = this.nTbl[i];
			console.log("Notes["+i+"]=" + this.nTbl[i]);
			t.innerHTML += "<tr><td>" + (i + 1) + "</td><td>" + line[0] + 
				"</td><td>" + line[1] + "</td><td>" + line[2] + "</td><td>" + line[3] + "</td><tr>";
		}
	}


	this.findReferences = function(textDest,tblCita,tblNote) {
		// Search html <sup> tags and add the citations to this.cTbl and notes to nTbl.
		//
		// If textDst is present, dipslay list of all sups found
		// If tblCita is present, display result: table of sources and their citations
		// If tblNote is present, display result: table of notes
		var sups = document.getElementsByTagName("sup");
		var i, j, node, nodes, ret = "";
		for (i = 0; i < sups.length; i++) {
			nodes = sups[i].childNodes;
			for (j = 0; j < nodes.length; j++) {
				node = nodes[j];
				if (node.nodeName == "A" && node.id != "" ) {
					if (node.id[0] == "N") {
					    // Store note id
						// <sup><a id="N428950">https://example.com/GRid=385555
						//			<i>Maria Borgin hautakivi Ahvenistolla</i></a></sup>
						var noteId, parts, part, text, rType, u, url;
						noteId = Number(node.id.substr(1));
						parts = node.childNodes;
						for (k = 0; k < parts.length; k++) {
							part = parts[k];
							if (part.nodeName == "#text" ) {
								u = part.data.replace(/ \n/, "");
								if (u) {
									url = part.data;
								}
							} else if (part.nodeName == "I") {
								text = part.innerText;
							} else if (part.nodeName == "B") {
								rType = part.innerText;
							}
						}
					    mark = this.addNote(noteId, url, text, rType);
					    node.href = "#sref" + mark;
					    node.innerText = mark;
					    ret += mark + ">" + node.id + '<br>';
					} else {
					    // Store source and citation ids
						// <sup><a id="{{obj[cr].source_id}}-{{obj[cr].uniq_id}}">*</a>
					    var arr = node.id.split('-');
					    mark = this.addC(Number(arr[0]), Number(arr[1]));
					    node.href = "#sref" + mark;
					    node.innerText = mark;
					    ret += mark + ">" + node.id + '<br>';
					}
				}
			}
		}
		if (textDest) {
			// Show citations and notes found from  sup > a elements
			document.getElementById(textDest).innerHTML = ret;
		}
		if (tblCita) {
			// Show citation refeference table
			this.listCitations(tblCita);
		}
		if (tblNote) {
			// Show citation refeference table
			this.listNotes(tblNote);
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
		var i, j, k;

		for (i = 0; i < this.cTbl.length; i++) {
			// line is [source_id, [cita_id, ...]], one line per each source
			line = this.cTbl[i];

			// Next Source

			// 	sources[312820] = { id:"S0408", note_ref:[], repositories:[316840],
			//		sauthor:"", spubinfo:"", stitle:"Askainen kuolleet 1888-1890", 
			//		uuid:"f83d3ff5c5cb49f1a71060b9456ab59e" };
			//
	        // <a href="/scene/source?uuid=f83d3ff5c5cb49f1a71060b9456ab59e" class="inlink" title="[C0866] Lähteen S1418 tiedot">
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
			nodeSourceA.href = '/scene/source?uuid=' + sObj.uuid;
			nodeSourceA.setAttribute("class", "inlink");
			nodeSourceA.setAttribute("title", "Lähteen " + sObj.id + " tiedot");
			var textnode = document.createTextNode(sObj.stitle);
			nodeSourceA.appendChild(textnode);
			nodeSource.appendChild(nodeSourceA);
			
			// A source may have references to multiple repositories
			var rObj;
			for (k = 0; k < sObj.repositories.length;  k++) {

				rObj = repositories[sObj.repositories[k]];
				textnode = document.createTextNode(" – ");
				nodeSource.appendChild(textnode);
				
				// Medium:– <span class="typedesc">kirja</span>
				var nodeMedium = document.createElement("SPAN");
				nodeMedium.setAttribute("class", "typedesc");
				textnode = document.createTextNode(rObj.medium);
				nodeMedium.appendChild(textnode);
				nodeSource.appendChild(nodeMedium);
				
				// Repository: <i>Taivassalon seurakunnan arkisto</i>
				var nodeRepo = document.createElement("I");
				textnode = document.createTextNode(" " + rObj.rname);
				nodeSource.appendChild(textnode);

			}
			if (sObj.repositories.length == 0) {
				var nodeRepo = document.createElement("B");
				textnode = document.createTextNode(" Arkistotieto puuttuu!");
				nodeRepo.appendChild(textnode);
				nodeSource.appendChild(nodeRepo)
			}
			this.viewCitaNotes(nodeSource, sObj.note_ref);
			if (rObj) {
				this.viewCitaNotes(nodeSource, rObj.notes)
			}

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
	
				mark = this.getCiteMark(i, j);
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
				if (cObj.confidence < "2") {
					nodeCitaSpan.style.color = "red";
				}

				var nodeCitaB = document.createElement("B");
				nodeCitaB.appendChild(document.createTextNode(mark + ' '));
				nodeCitaSpan.appendChild(nodeCitaB);
				var text = cObj.page + " " + stars(cObj.confidence);
				nodeCitaSpan.appendChild(document.createTextNode(text));
				nodeCitaDiv.appendChild(nodeCitaSpan);

				this.viewCitaNotes(nodeCitaDiv, cObj.note_ref)
			}
			line = undefined;
		}
	} // sourceReferences()

	
	this.viewCitaNotes = function(htmlObject, note_ref) {
		// Display the Note texts and links in htmlObject.
		// Text is reprenseted as italics and split to lines vy '¤' character
		// Url link is named by the url's domain name
		var k, l, note, text;
		for (k = 0; k < note_ref.length; k++) {
			note = notes[note_ref[k]]
			if (note.url || note.text) {
				var lines = note.text.split("¤");
				htmlObject.appendChild(document.createTextNode(" –► "));
				var nodeI = document.createElement("I");
				nodeI.appendChild(document.createTextNode(lines[0] + " "));
				for (l=1; l < lines.length; l++) {
					if (lines[l].length > 0) {
						nodeI.appendChild(document.createElement("BR"));
						nodeI.appendChild(document.createTextNode(lines[l]));
					}
				}
				nodeI.appendChild(document.createTextNode(' '));
				htmlObject.appendChild(nodeI);
			}
			if (note.url) {
				var nodeNoteA = document.createElement("A");
				nodeNoteA.setAttribute("class", "outlink");
				nodeNoteA.setAttribute("target", "_blank");
				nodeNoteA.setAttribute("href", note.url);
				text = nodeNoteA.hostname;
				nodeNoteA.appendChild(document.createTextNode(text));
				htmlObject.appendChild(nodeNoteA);
			}
		}

	}

	this.noteReferences = function(destination) {
		//
		// Display the foot notes by stored (place) notes.
		//
		var t = document.getElementById(destination);
		var noteId, url, text, rType;
		var mark;	// note index like "1"
		var line, i, j, k;

		if (this.nTbl.length) {
			// Show title and the notes
			t.style.display = "block";
		}

		for (i = 0; i < this.nTbl.length; i++) {

			// Next Note: noteId, url, text, rType

			line = this.nTbl[i];
			noteId = line[0];
			url = line[1].trim();
			text = line[2];
			rType = line[3];

			// line = [428951, "https://example.com/us.htm", "Note text here", "viite"]
			// Result:
	        // <p> 1) <span class="typedesc">viite</span>
			// <a href="http://example.com/us.htm" class="outlink" target="_blank">example.com</a> –
	        //  <i>Note text here</i>
			// </p>
		    
			var nodeP = document.createElement("P");
			//nodeSource.setAttribute("class", "sourceDesc");
			//nodeSource.style.color = "green";
			t.appendChild(nodeP);
			nodeP.append(document.createTextNode((i + 1) + ") "));
			
			var nodeType = document.createElement("SPAN");
			nodeType.setAttribute("class", "typedesc");
			nodeType.setAttribute("id", "sref" + (i + 1));
			nodeType.appendChild(document.createTextNode(rType + "  "));
			nodeP.appendChild(nodeType);

			if (url) {
				var nodeLink = document.createElement("A");
				nodeLink.href = url.trim();
				nodeLink.setAttribute("target", "_blank");
				nodeLink.setAttribute("class", "outlink");
				nodeLink.appendChild(document.createTextNode(nodeLink.hostname));
				nodeP.appendChild(nodeLink);
			}

			if (text) {
				var nodeText = document.createElement("I");
				nodeText.appendChild(document.createTextNode(text));
				nodeP.appendChild(nodeText);
			}
		}
		line = undefined;
	} // noteReferences()

}

