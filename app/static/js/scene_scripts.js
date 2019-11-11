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

	this.lister = function(destination) {
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

	this.findCitations = function(textDest, tableDest) {
		// Search html <sup> tags and display the citations in textDest and
		// table in tableDest.
		// + Add citations to citTable.
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
		this.lister(tableDest)								// Table result
	}
}

