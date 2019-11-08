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

function showTable() {
	// Display cit_tbl table
	var t = document.getElementById("demo");
	t.innerHTML = "<tr><th>cists type is " + typeof cit_tbl + "</th><tr>";
	for (i = 0; i < cit_tbl.length; i++) { 
		t.innerHTML += "<tr><td>rivi x</td><td>" + cit_tbl[i] + "</td><tr>";
	}
	console.log("cists=" + cit_tbl);
}
showTable()