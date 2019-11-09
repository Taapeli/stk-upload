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


var cit_tbl = [];	//Table of citations (for person.html etc)

function listCitations(tbl) {
	// Display cit_tbl table
	var t = document.getElementById(tbl);
	t.innerHTML = "<tr><th>mark</th><th>source</th><th>citation</th></th><tr>";
	for (i = 0; i < cit_tbl.length; i++) {
		if (cit_tbl[i].length == 3) {
			t.innerHTML += "<tr><td>" + cit_tbl[i][2] + "</td><td>" 
				+ cit_tbl[i][0] + "</td><td>" + cit_tbl[i][1] + "</td><tr>";
		} else {
			t.innerHTML += "<tr><td>rivi x</td><td>" + cit_tbl[i] + "</td><tr>";
		}
	}
	console.log("Citation table=" + cit_tbl);
}

function getCitations(tbl) {
	var x = document.getElementsByTagName("sup");
	var i;
	var ret = "";
	for (i = 0; i < x.length; i++) {
	    ret += " " + x[i].innerText;
		a = x[i].firstElementChild;
		if (a.nodeName == "A") {
		    ret += ">" + a.id;
		}
	}
	document.getElementById("demo").innerHTML = ret;
	listCitations(tbl)
}

function setCitation(cits, sou) {
	// Finds or creates mark symbol for given citation
	ret = []
	for (cit in cits) {
		mark = "1a"
		cit_tbl.append([mark, cit, sou])
		ret.append(mark)
	}
}