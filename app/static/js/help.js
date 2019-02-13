function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}

$(document).ready(function() {
	var language = $("#help").attr("language");
	var url = "isotammi.referata.com/wiki/" + capitalizeFirstLetter(document.location.pathname.substring(1)) + "/" + language;
	var re = new RegExp("//","g");
	url = url.replace(re,"/");
	$("#help").attr("href","http://"+url);
});	
