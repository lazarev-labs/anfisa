var sCurSetup = "base";
var sEvalData = null;
var sCurItem = null;
var sItemsContents = null;
var sCurItemNode = null;

var sNodeHotEvalDetails = null;
var sNodeItemParam = null;

/*************************************/
function setupHotEvalCtrl() {
    if (sNodeHotEvalDetails != null)
        return;
    sNodeHotEvalDetails = document.getElementById("hot-ws-details");
    sNodeItemParam = document.getElementById("hi----param");
    loadEvalData();
}

/*************************************/
function loadEvalData() {
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            var info = JSON.parse(this.responseText);
            setupHotEvalData(info);
        }
    };
    xhttp.open("POST", "hot_eval_data", true);
    xhttp.setRequestHeader("Content-type", 
        "application/x-www-form-urlencoded");
    xhttp.send("ws=" + sWorkspaceName + "&m=" + encodeURIComponent(sAppModes)); 
}

function setupHotEvalData(info) {
    sCurSetup = info["setup"];
    var col_rep = [];
    sItemsContents = {};
    columns = info["columns"];
    for (idx = 0; idx < columns.length; idx++) {
        col_name = columns[idx][0];
        sItemsContents[col_name] = columns[idx][1];
        col_rep.push('<div id="hi--' + col_name + '" class="hot-eval-item" ' +
          'onclick="hotItemSel(\'' + col_name + '\');">' + 
          col_name + '</div>');
    }
    sItemsContents["--param"] = info["params"];
    document.getElementById("hot-eval-columns").innerHTML =
        col_rep.join('\n');
    sNodeItemParam.className = "hot-eval-item";

    /* temporary */
    document.getElementById("hot-ws-det").disabled = true;
    
    sCurItem = null;
    sCurItemNode = null;
    hotItemSel("--param");
}

/*************************************/
function hotItemSel(item) {
    hideWsDetails();
    if (sCurItem == item) 
        return;
    var new_it_el = document.getElementById("hi--" + item);
    if (new_it_el == null) 
        return;
    if (sCurItemNode != null) {
        sCurItemNode.className = sCurItemNode.className.replace(" cur", "");
    }
    sCurItem = item;
    sCurItemNode = new_it_el;
    sCurItemNode.className = sCurItemNode.className + " cur";
    hotItemReset();
    document.getElementById("hot-item-modify").disabled = 
        (sCurItem != "--param");
    document.getElementById("hot-item-reset").disabled = 
        (sCurItem != "--param");
    document.getElementById("hot-eval-item-content").disabled = 
        (sCurItem != "--param");
}

/*************************************/
function hotItemModify() {
    if (sCurItem != "--param")
        return;
    new_content = document.getElementById("hot-eval-item-content").value;
    if (new_content == sItemsContents[sCurItem])
        return;
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            var info = JSON.parse(this.responseText);
            setupItemChange(info);
        }
    };
    xhttp.open("POST", "hot_eval_modify", true);
    xhttp.setRequestHeader("Content-type", 
        "application/x-www-form-urlencoded");
    xhttp.send("ws=" + sWorkspaceName + "&setup=" + sCurSetup + 
        "&m=" + encodeURIComponent(sAppModes) + 
        "&it=" + encodeURIComponent(sCurItem) + 
        "&cnt=" + encodeURIComponent(new_content));
}

function hotItemReset() {
    document.getElementById("hot-eval-item-content").value =
        sItemsContents[sCurItem];
    document.getElementById("hot-eval-item-errors").innerHTML = "";
}

function setupItemChange(info) {
    if (info["status"] == "OK") {
        hotEvalModOff();
        updateCurFilter(sCurFilterName, true);
        loadStat();
    } else {
        document.getElementById("hot-eval-item-errors").innerHTML =
            info["error"]; 
    }
}

/*************************************/
function hotWsChange() {
}

function hotWsClone() {
}

function hotWsDelete() {
}

function hotWsDetails() {
    if (sNodeHotEvalDetails.style.display == "none") 
        sNodeHotEvalDetails.style.display = "block";
    else
        sNodeHotEvalDetails.style.display = "none";
}

function hideWsDetails() {
    sNodeHotEvalDetails.style.display = "none";
}
