/*  Isotammi Genealogical Service for combining multiple researchers' results.
    Copyright (C) 2016-2021  Juha Mäkeläinen, Jorma Haapasalo, Kari Kujansuu, 
                             Timo Nallikari, Pekka Valta
    See the LICENSE file.
*/
var gt = new Gettext({domain: 'gedcom_transformations'});
var _ = function(msgid,args) { return gt.strargs(gt.gettext(msgid),args); };
var ngettext = function(msgid, msgid_plural, n) { return gt.ngettext(msgid, msgid_plural, n); };
	
var TOOLARGE =  _("The file is too large (max %1 MB)", Math.round(maxsize/1000000) );
	
function hide_all() {
    $("div.gedcom").hide();
    $("#div_show_info").show();
}

function show(id) {
    var rect = $(id).show().get(0).getBoundingClientRect();
	var y = rect.top;
	window.scroll(0,y-50);
}

function add_gedcom_links() {
    $("a.gedcomlink").click(function(e) {
        var linenum = $(e.target).text();
    	$.get("/gedcom/get_excerpt/" + gedcom + "/" + linenum,function(rsp) {
    	    $("#excerpt").html(rsp);
    	    $("#div_excerpt").dialog({title: gedcom, width:500});
    	    return false;
    	});
    });
    $("#div_excerpt button").click(function(e) {
	    $("#div_excerpt").dialog("close");
    });
}

function clear_others() {
	if (this.checked) { // uncheck other options, clear text input
		$("input.transform_option[type=checkbox]").prop("checked", false);
		$("input.transform_option[type=text]").val("");
	}
}

function checkFileSize() {
 	try {
	 	var input = document.getElementById('file');
 	 	var file = input.files[0];
 	 	if (file.size > maxsize) {
			alert(TOOLARGE);
			return false;
 	 	}
 	}
 	catch (err) {
 	}
	return true;
}

$(document).ready( function() {
    console.log("ready");

    $(document).on({
        ajaxStart: function() { $("body").addClass("loading");  },
        ajaxStop: function() { $("body").removeClass("loading"); },    
        ajaxError: function() { $("#errors").text(_('Server error')).show(); }    
    });


    $('#upload').click( function() {
        // from https://stackoverflow.com/questions/166221/how-can-i-upload-files-asynchronously   
        if (!checkFileSize()) return; 
        var gedcom_name = $("#file").val();
        gedcom_name = gedcom_name.replace(/^C:\\fakepath\\/,"");
        $.get("/gedcom/check/" + encodeURIComponent(gedcom_name), function(rsp){
            if (rsp == "does not exist") {
                $.ajax({
                    // Your server script to process the upload
                    url: '/gedcom/upload',
                    type: 'POST',

                    // Form data
                    data: new FormData($('#upload_form')[0]),

                    // Tell jQuery not to process data or worry about content-type
                    // You *must* include these options!
                    cache: false,
                    contentType: false,
                    processData: false,

                    // Custom XMLHttpRequest
                    xhr: function() {
                        var myXhr = $.ajaxSettings.xhr();
                        if (myXhr.upload) {
                            // For handling the progress of the upload
                            myXhr.upload.addEventListener('xprogress', function(e) {
                                if (e.lengthComputable) {
                                    $('progress').attr({
                                        value: e.loaded,
                                        max: e.total,
                                    });
                                    if (e.loaded == e.total) {
                                        $("progress").hide();
                                        //document.location.href= "/gedcom/list";
                                    }
                                }
                            } , false);
                        }
                        myXhr.done = function() { alert("done1"); };
                        $("progress").show();
                        return myXhr;
                    }, // xhr
                    
                    complete: function() { console.log("complete"); },
                    error: function() { 
                    	console.log("error");
                    	console.log(this);
                 	},
                    statusCode: {
					    413: function() {
					      alert(TOOLARGE);
					    }
					},
                    success: function() { 
                       console.log("success"); 
                       document.location.href= "/gedcom/info/" + gedcom_name;
                    }
                }) // $.ajax
                .done( function() { console.log("done"); });
            } // does not exist
            else { // exists
                alert(_("File already exists"));
            } // exists
        }); // $.get
    });
    
    $("#show_info").click(function() {
        $("#info").show();
        $("#div_show_info").hide();
    });
    
    $("#analyze").click(function() {
        hide_all();
    	$.get("/gedcom/analyze/" + gedcom ,function(rsp) {
    	    $("#results").html(rsp);
    	    show("#div_results");
            add_gedcom_links();
    	});
    });


    $("#transforms").click(function() {
        hide_all();
        $("#div_transforms").show();
    });

    $("#versions").click(function() {
        hide_all();
        $.get("/gedcom/versions/" + gedcom , function(versions) {
            $("#versions_list").empty();
            $.each(versions, function(i,versioninfo) {
            	//$("#versions_list").append("<li>"+version+"</li>");
            	var version_number = versioninfo[0];
            	var version = versioninfo[1];
            	var displayname = versioninfo[2];
            	var modtime = versioninfo[3];
            	var row = $("<tr><td>" +
            	"<input type=radio name=v1>" +
            	"<input type=radio name=v2>" +
            	"<td><a href=/gedcom/download/"+version+">"+ modtime+" "+displayname+ "</a></tr>");
            	row.data("version",version);
            	$("#versions_list").append(row);
            });
            $("#versions_list tr:nth-last-child(2) input[name=v1]").prop("checked",true);
            $("#versions_list tr:nth-last-child(1) input[name=v2]").prop("checked",true);
            if (versions.length < 2) {
                $("#compare").prop('disabled', true);
                $("#delete_old_versions").prop('disabled', true);
	            //$("#versions_list tr:nth-last-child(1) input[name=v1]").prop("checked",true);
                $("#compare").hide();
                $("#delete_old_versions").hide();
                $("#no_versions").show();
            } else {
                $("#compare").prop('disabled', false);
                $("#delete_old_versions").prop('disabled', false);
                $("#compare").show();
                $("#delete_old_versions").show();
                $("#no_versions").hide();
            }
            $("#div_versions").show();
        });
    });

    $("a.transform").click(function(e) {
        $("#div_transforms").hide();
        $.get("/gedcom/transform/" + gedcom + "/" + $(e.target).attr("data-transform"), function(rsp) {
            $("#div_transform_params1").html(rsp);
            $("input.clear_others").click(clear_others);
            $("#div_transform_params").show();
			$("#check_all").click(function(rsp) {
				var checked = $("#check_all").is(":checked");
				$(".transform_option").prop("checked",checked);
			});
        });
    });

    $("#delete").click(function() {
        var ok = confirm(_('Are you sure?'));
        if (ok) {
        	$.get("/gedcom/delete/" + gedcom ,function() {
        		window.location.replace("/gedcom");
        	});
        }
    });

    $("#delete_old_versions").click(function() {
        var ok = confirm(_('Are you sure?'));
        if (ok) {
        	$.get("/gedcom/delete_old_versions/" + gedcom ,function() {
        	    $("#div_compare").hide();
        	    $("#div_versions").hide();
        	});
        }
    });

    $("#show_history").click(function() {
        hide_all();
    	$("#difftable").empty();
        $.get("/gedcom/history/" + gedcom , function(rsp) {
            $("#history").text(rsp);
            show("#div_history");
        });
    });

    $("#update_desc").click(function() {
        $.post("/gedcom/update_desc/" + gedcom , {desc:$("#desc").val()},function(rsp) {
        	console.log(rsp);
    	});
    });

    $("#view_permission").click(function() {
        var value = $("#view_permission").is(":checked");
        $.get("/gedcom/update_permission/" + gedcom + "/" + value,function(rsp) {
        	$("#permission_message").show();
        	$("#permission_message").fadeOut(2000);
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
        	$("#palauta1").text(_('Revert to %1', [gedcom1])).data("gedcom",gedcom1);
        	$("#palauta2").text(_('Revert to %1', [gedcom2])).data("gedcom",gedcom2);
        	if (!gedcom1.match(/\.ged$/)) $("#palauta1").show();
        	if (!gedcom2.match(/\.ged$/)) $("#palauta2").show();
            show("#div_compare");
    	});
    });

	$("button.palauta_button").click(function(rsp) {
		var version = $(this).data("gedcom");
        $.get("/gedcom/revert/" + gedcom + "/" + version, function(rsp) {
	        $("#versions").click(); 
            alert(_('%1 renamed to %2', [gedcom, rsp.newname] ) + "\n" +
            	  _('%1 renamed to %2', [version, gedcom] ));
        });
	});

	$("#save_result").click(function(rsp) {
        $.get("/gedcom/save/" + gedcom , function(rsp) {
	        var msg  = _('%1 renamed to %2', [gedcom, rsp.newname] ); 
        	$("#oldname").text(rsp.newname);
        	$("#div_oldname").show();
        	$("#div_save").hide();
        });
	});

    hide_all();

    $("#transform").off("click");

    $("#transform").click(function() {
        $("#errors").hide();
    	$("#output").hide();
    	$("#output_log_pre").empty();
    	$("#output_log").empty();
    	$("#error_log").empty();
        $.post("/gedcom/transform/" + gedcom + "/" + transform, $("#form").serialize(), function(rsp) {
            if (rsp.plain_text)
                $("#output_log_pre").text(rsp.stdout);
            else
                $("#output_log").html(rsp.stdout);
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
            add_gedcom_links();
            show("#output");
        });
        return false;
    });

});


