/*  Isotammi Genealogical Service for combining multiple researchers' results.
    Copyright (C) 2016-2021  Juha Mäkeläinen, Jorma Haapasalo, Kari Kujansuu, 
                             Timo Nallikari, Pekka Valta
    See the LICENSE file.
*/
function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}

$(document).ready(function() {
	var language = $("#help").attr("language");
	var url = "wiki.isotammi.net/wiki/" + capitalizeFirstLetter(document.location.pathname.substring(1)) + "/" + language;
	var re = new RegExp("//","g");
	url = url.replace(re,"/");
	$("#help").attr("href","http://"+url);
});	
