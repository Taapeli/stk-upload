var gt = new Gettext({domain: 'gedcom_transformations'});
var _ = function(msgid) { return gt.gettext(msgid); };
var ngettext = function(msgid, msgid_plural, n) { return gt.ngettext(msgid, msgid_plural, n); };
	
function hide_all() {
    $("div.gedcom").hide();
}

$(document).ready( function() {
    console.log("ready");

    $(document).on({
        ajaxStart: function() { $("body").addClass("loading");  },
        ajaxStop: function() { $("body").removeClass("loading"); },    
        ajaxError: function() { $("#errors").text(_('Server error')).show(); }    
    });
    
    $("#transforms").click(function() {
        hide_all();
        $("#div_transforms").show();
    });
    $("#versions").click(function() {
        hide_all();
        $.get("/gedcom/versions/" + gedcom , function(versions) {
            $("#versions_list").empty();
            $.each(versions, function(i,version) {
            	//$("#versions_list").append("<li>"+version+"</li>");
            	var row = $("<tr><td>" +
            	"<input type=radio name=v1>" +
            	"<input type=radio name=v2>" +
            	"<td><a href=/gedcom/download/"+version+">"+version+"</a></tr>");
            	row.data("version",version);
            	$("#versions_list").append(row);
            });
            $("#versions_list tr:nth-last-child(2) input[name=v1]").prop("checked",true);
            $("#versions_list tr:nth-last-child(1) input[name=v2]").prop("checked",true);
            $("#div_versions").show();
        });
    });
    $("a.transform").click(function(e) {
        $.get("/gedcom/transform/" + gedcom + "/" + $(e.target).attr("data-transform"), function(rsp) {
            $("#div_transform_params1").html(rsp);
            $("#div_transform_params").show();
        });
    });
    $("#delete").click(function() {
        var ok = confirm(_('Are you sure?'));
        if (ok) {
        	$.get("/gedcom/delete/" + gedcom ,function() {
        		window.location.replace("/gedcom/list");
        	});
        }
    });
    $("#update_desc").click(function() {
        $.post("/gedcom/update_desc/" + gedcom , {desc:$("#desc").val()},function(rsp) {
        	console.log(rsp);
    	});
    });
    $("input,a").click(function() {
    	 $("#errors").hide();
    });
    $("#palauta").click(function() {
		var version = $("#oldname").text();
        $.get("/gedcom/revert/" + gedcom + "/" + version, function(rsp) {
            	$("#div_oldname").hide();
        });
    	 
    });
    $("#compare").click(function() {
    	var row1 = $("input[name=v1]:checked").parent().parent();
    	var gedcom1 = row1.data("version");
    	var row2 = $("input[name=v2]:checked").parent().parent();
    	var gedcom2 = row2.data("version");
    	$.get("/gedcom/compare/" + gedcom1 + "/" + gedcom2,function(rsp) {
        	$("#difftable").html(rsp.diff);
        	$("button.palauta_button").hide();
        	$("#palauta1").text(_('Revert to %(gedcom)s', gedcom1)).data("gedcom",gedcom1);
        	$("#palauta2").text(_('Revert to %(gedcom)s', gedcom2)).data("gedcom",gedcom2);
        	if (!gedcom1.match(/\.ged$/)) $("#palauta1").show();
        	if (!gedcom2.match(/\.ged$/)) $("#palauta2").show();
        	$("#div_compare").show();
    	});
    });
	$("button.palauta_button").click(function(rsp) {
		var version = $(this).data("gedcom");
        $.get("/gedcom/revert/" + gedcom + "/" + version, function(rsp) {
	        $("#versions").click(); 
            alert(_('%(gedcom)s renamed to %(newname)s', gedcom, rsp.newname ) + "\n" +
            	  _('%(version)s renamed to %(gedcom)s', version, gedcom ));
        });
	});
	$("#save_result").click(function(rsp) {
		var gedcom = "" + gedcom ;
        $.get("/gedcom/save/" + gedcom , function(rsp) {
	        var msg  = _('%(gedcom)s renamed to %(newname)s', gedcom, rsp.newname ); 
        	$("#oldname").text(rsp.newname);
        	$("#div_oldname").show();
        	$("#div_save").hide();
        });
	});
    hide_all();

    $("#transform").off("click");
    $("#transform").click(function() {
    	$("#output").hide();
    	$("#output_log").empty();
    	$("#error_log").empty();
        $.post("/gedcom/transform/" + gedcom + "/" + transform, $("#form").serialize(), function(rsp) {
            $("#output_log").text(rsp.stdout);
            if (rsp.stderr) 
            	$("#error_log").text(_('Errors:') + "\n" + rsp.stderr);
            if (rsp.oldname) {
            	$("#oldname").text(rsp.oldname);
            	$("#div_oldname").show();
            	$("#div_save").hide();
        	}
        	else {
            	$("#div_oldname").hide();
            	$("#div_save").show();
        	}
            $("#output").show();
        });
        return false;
    });

});


