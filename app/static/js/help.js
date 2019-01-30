$(document).ready(function() {
	$("#help").click(function() {
		$.get("/help?url="+encodeURIComponent(document.location.href),function(rsp) {
			$( "#ohjeikkuna" ).text(rsp).dialog();
		});
	});
});	
