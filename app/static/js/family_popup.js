/*!
 * Method for displaying Family information in a popup-window
 */

function parseSortname(name) {
	// Returns [surname,firstname,patronyme]
	return name.split("#");
}

function htmlSortname(name) {
	// Parses a sortname to html representation
	var a = name.split('#');
	if (a.length != 3)  return name;
	return a[1]+" <i>"+a[2]+"</i> <b>"+a[0];
}

function datesStr(dates,first=false) {
	// Parses a DateRange list format object (<int>, <str> [,<str>])
	if (!dates) return '';
	if (dates.length < 2) return '';
	if (first) return dateLocal(dates[1]);
	if (dates.length == 3) {
		return dateLocal(dates[1]) + ' ... ' + dateLocal(dates[2]);
	} else return dateLocal(dates[1]);
	return name.split("#");
}

function dateLocal(date) {
	// Parses ISO style date 1820-12-03 to local 3.12.1820
	var a = date.split('-');
	if (a.length == 1) return date;
	if (a[1].startsWith('0'))   a[1] = a[1].substr(1,1);
	if (a.length == 2) return a[1]+'.'+a[0];
	if (a[2].startsWith('0'))   a[2] = a[2].substr(1,1);
	if (a.length == 3) return a[2]+'.'+a[1]+'.'+a[0];
	return "?"
}

/* --------------------------------- Vue ----------------------------------- */

var vm = new Vue({
	el: '#popup_app',
	delimiters: ['${', '}'],
	data: {
		message: 'Not yet run',
		person_uuid: 'a7388323a535424a8dca5730408628bf', // 'paste here',
		uuid: '?',
		families: [],
		currentIndex: 0,	// 1..n, 0 = no familiy selected
		status: ''
		// ,isShow: false
	},
	computed: {
		current: function () {
			// currentIndex = 1,2,...
			if (vm.currentIndex <= vm.families.length && vm.currentIndex > 0)
				return vm.families[vm.currentIndex-1];
			console.log("Exit currentIndex "+ vm.currentIndex);
			return false;
		}
	},
	methods: {
		showPopup(uuid, event) {
			// When the user clicks, open the popup window
			var popup = document.getElementById("pop-window");
			//console.log("showPopup for person "+uuid);
			//popup.classList.toggle("show");
			// Get vm.families
			vm.getFamilies(uuid);
			console.log("Got",vm.families.length,"families")
			vm.changeFamily(0);
			// Set popup position near clicked icon
			var x = event.target.offsetLeft + 14;
			var y = event.target.offsetTop - 35;
			var pop = document.getElementById('pop-window');
			pop.style.left = x+"px";
			pop.style.top = y+"px";
			if (vm.families.length == 0) {
				console.log("No families:", vm.families, vm.message, vm.currentIndex);
				event.target.innerHTML = "&ndash;";
			}
		},
		changeFamily(index, event) {
			// No 0 (=false) is allowed in currentIndex
			if (vm.families.length > 0){
				console.log("changeFamily: katsotaan "+vm.families[index].id);
				vm.currentIndex = index+1;
			} else {
				console.log("changeFamily: ei perheitä");
				vm.currentIndex = 1;
			}
		},

		getFamilies(q_uuid) {
			// Asks for data for all families of given person
			console.log("families for person "+q_uuid);
			axios.post("/scene/json/families", {uuid:q_uuid})
			.then (function(rsp) {
				vm.families = [];
				vm.status = "Status code: "+String(rsp.status);
				//console.log("stk result: "+rsp.data.statusText);
				vm.message=rsp.data.statusText;
				if (rsp.data.records.length == 0) {
					// No families found
					return;
				}
				for (rec of rsp.data.records) {
					//console.log(rec);
					var fam = {};
					if (rec) {
						fam.id = rec.id;
						fam.rel_type = rec.rel_type;
						fam.dates = datesStr(rec.dates, first=true);
						fam.role = rec.role;
						fam.href = "/scene/family?uuid="+rec.uuid;
						fam.parents = [];
						fam.children = [];
						fam.title = "Perhe "+fam.id;

						for (parent of rec.parents) {
							var p = {};
							p.uuid = parent.uuid;
							p.is_self = (p.uuid == q_uuid);
							p.name = parseSortname(parent.sortname);
							p.role = parent.role;
							p.href = "/scene/person?uuid="+parent.uuid
							p.birth = datesStr(parent.dates, first=false);
							fam.parents.push(p);
						}
						//var gentext = ['Lapsi','Poika','Tytär'];
						for (child of rec.children) {
							fam.has_children = true;
							var c = {uuid:child.uuid};
							c.is_self = (c.uuid == q_uuid);
							c.name = parseSortname(child.sortname);
							c.href = "/scene/person?uuid="+child.uuid
							c.gender = child.sex;
							c.birth = datesStr(child.dates, first=false);
							fam.children.push(c);
						}
						vm.families.push(fam);
						console.log("got family ",vm.families.length,fam.id)
					}
				}
			})
		}
	}
})
