/*  Isotammi Genealogical Service for combining multiple researchers' results.
    Copyright (C) 2016-2021  Juha Mäkeläinen, Jorma Haapasalo, Kari Kujansuu, 
                             Timo Nallikari, Pekka Valta
    See the LICENSE file.
*/
/*!
 * Methods for displaying Family information in a popup-window
 */

function parseSortname(name) {
	// Returns [surname,firstname,patronyme]
	return name.split("#");
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
		status: '',
		translations: {},
		isShow: false,
		touched: false
	},
	computed: {
		current: function () {
			// currentIndex = 1,2,...
			if (vm.currentIndex <= vm.families.length && vm.currentIndex > 0)
				return vm.families[vm.currentIndex-1];
			console.log("Exit currentIndex "+ vm.currentIndex);
			return false;
		},
	},
	methods: {
		showPopup(uuid, event) {
			// When the user clicks, open the popup window

			// Set popup position near clicked icon
			var x = event.target.offsetLeft + 14;
			var y = event.target.offsetTop - 35;
			var pop = document.getElementById('pop-window');
			pop.style.left = x+"px";
			pop.style.top = y+"px";
			//console.log("showPopup for person "+uuid);

			// Get vm.families
			vm.getFamilies(uuid);
		},
		hidePopup() {
			isShow = false;
		},

		changeFamily(index, ev) {
/*			Selecting family tab.
			Current family index in 1..n; value 0 means no family.
			On touchpad device, there comes 2 events:
				1) touch -> mouseover
				2) click -> ignore
*/
			var ev_type = (ev !== null ? ev.type : "-");
//			vm.message = vm.message + " <br>" 
//				+ ev_type 
//				+ (vm.touched ? " T": "");
//			console.log(vm.message);
//			if (vm.touched) {
//				vm.touched = false;
//				return; }
			if (ev_type == "touchstart") {
				vm.touched = true;
				console.log("touchstart");
			} else console.log('event ', ev_type);
			if (vm.families.length > 0){
				console.log("changeFamily: show " + vm.families[index].id);
				vm.currentIndex = index+1;
			} else {
				console.log("changeFamily: no families");
				vm.currentIndex = 0;
			}
		},

		datesStr(dates) {
			// Show DateRange as full text.
			if (!dates) return '';
			return dates['as_str'];
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
				vm.translations=rsp.data.translations;

				for (rec of rsp.data.records) {
					//console.log(rec);
					var fam = {};
					if (rec) {
						fam.id = rec.id;
						fam.rel_type = rec.rel_type_lang;
						fam.dates = rec.dates;
						fam.role = rec.role;
						fam.role_lang = rec.role_lang;
						fam.href = "/scene/family?uuid="+rec.uuid;
						fam.parents = [];
						fam.children = [];
						fam.title = "Perhe "+fam.id;

						for (parent of rec.parents) {
							var p = {};
							p.uuid = parent.uuid;
							p.is_self = (p.uuid == q_uuid);
							p.name = parseSortname(parent.sortname);
							p.role = parent.role_lang;
							p.href = "/scene/person?uuid="+parent.uuid;
							if (parent.event_birth) {
								p.birth_date = parent.event_birth.dates;
							} else p.birth_date = null;
							fam.parents.push(p);
						}
						for (child of rec.children) {
							fam.has_children = true;
							var c = {uuid:child.uuid};
							c.is_self = (c.uuid == q_uuid);
							c.name = parseSortname(child.sortname);
							c.href = "/scene/person?uuid="+child.uuid
							c.gender = child.role_lang; // Clear text in user language
							if (child.event_birth) {
								c.birth_date = child.event_birth.dates;
							} else {
								c.birth_date = null;
							}
								
							fam.children.push(c);
						}
						vm.families.push(fam);
						//console.log("got family ",vm.families.length,fam.id)
					} // if rec
				} // for
				vm.changeFamily(0, null);
				console.log("Got",vm.families.length, "families, current=", vm.currentIndex)
				vm.isShow = true;
			}) // axios then
			.catch(function (error) {
				console.log('Axios error:',error);
				vm.message = error;
				vm.isShow = true;
			}) // axios catch
		} // getFamilies
	} // methods
}) // Vue vm
