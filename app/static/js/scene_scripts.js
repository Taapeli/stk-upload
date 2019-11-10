var gt = new Gettext({domain: 'gedcom_transformations'});
var _ = function(msgid,args) { return gt.strargs(gt.gettext(msgid),args); };
var ngettext = function(msgid, msgid_plural, n) { return gt.ngettext(msgid, msgid_plural, n); };
	
function jump(initial) {
	// Jump to given #id and scroll a bit back
	var elem = $("a[name="+initial+"]");
    var rect = elem.get(0).getBoundingClientRect();
	var y = rect.top;
	window.scroll(0,window.scrollY+y-30);
}


function citTable() {
	// Manage citations table and indexes "1a", ... for each.
	this.cTbl = [];

	this.getMark = function (s_id, c_id) {
		// Todo
	    return (s_id + 1) + "abcderfghijklmopqrstuvwxyzåäö"[c_id];
	}

	this.add = function(s_id, c_id) {
		// Adds a citation to source.
		// The lines of this.cTbl are arrays [source_id, [citation_id, ...]]
	    //this.mark = (s_id + 1) + "abcderfghijklmopqrstuvwxyzåäö"[c_id];
		var line;
		var l = this.cTbl.length;
		for (i = 0; i < l; i++) {
			line = this.cTbl[i];
			if (line[0] == s_id) {
				// Matching source
				var cits = line[1];
				var a = cits.indexOf(c_id);
				if (a < 0) {
					// No match; add a new citation to this source
					this.cTbl[i][1].push(c_id);
				}
				return this.cTbl[i];
			}
		}
		line = [s_id, [c_id]];
		this.cTbl.push(line);
	}

	this.lister = function(destination) {
		// Display citations table in destination element.

		var t = document.getElementById(destination);
		t.innerHTML = "<tr><th>source</th><th>citation</th></th><tr>";

		var l = this.cTbl.length;
		for (i = 0; i < l; i++) {
			line = this.cTbl[i];
			t.innerHTML += "<tr><td>" + line[0] + "</td><td>" 
				+ line[1] + "</td><tr>";
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
			    ret += ">" + a.id + '<br>';
			    var arr = a.id.split('-');
			    this.add(Number(arr[0]), Number(arr[1]));
			} else { ret += '<br>' }
		}
		document.getElementById(textDest).innerHTML = ret;	// Text result
		this.lister(tableDest)								// Table result
	}
}

