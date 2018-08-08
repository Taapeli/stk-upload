/* 
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */

function info(id, nimi, ammatti, paikka, karaja, aika, sig) {
    var str="<h3>Kohteet</h3><ul class='info'>";
    str += "<li><b>Person</b> {id=" + id + ", nimi='" + nimi + "' ";
    if (ammatti !== "") { str += ", ammatti='" + ammatti + "' "; }
    str += "}<br />&nbsp;</li>";
    var kid = "?";  /* Ei tietysti ole joka rivillä eri! */
    str += "<li><b>Event</b> {type='Käräjät', id=" + kid 
            + ", nimi='" + karaja + " " + aika + "'}</li>";
        str += "<li><i>" + " Person -[Osallistuu]-> Event</i><br />&nbsp;</li>";
    if (paikka !== "") {
        var lid = "?";  
        str += "<li><b>" + "Place</b> {id = " + lid + ", nimi='" + paikka + "'}</li>";
        var ajat = aika.split(" … ");
        str += "<li><i>" + " Person -[Asuu {date:" + ajat[0] + "}]-> Place</i><br />&nbsp;</li>";
    }
    
    /* Lähdetiedot */
    var parts = sig.split("/");
    if (parts.length === 3) {
        str += "<li><b>Lainaus</b> {sivu " 
                + parts[1] + " kohta " + parts[2] + "}</li>";
        str += "<li><b>Lähde</b> {" + karaja + " käräjät " + aika + "}</li>";
        str += "<li><b>Arkisto</b>{Tuomiokirjat " + parts[0] + "}";
    }
    document.getElementById("tiedot").innerHTML = str + "</ul>";
}

