var ids = ['two', 'cars', 'buses', 'lgvs', 'hgvs']
var vals = [1.0, 1.0, 1.0, 1.0, 1.0, 65.1, 10, true, 0, 100]
var origVals = [1.0, 1.0, 1.0, 1.0, 1.0, 65.1, 10, true, 0, 100]

window.onload = function () {
    ids.forEach(addListeners)
    updateVals()

    function addListeners(id) {
        document.getElementById(id+"-slider").oninput = function() {
            document.getElementById(id+"-val").innerHTML = parseFloat(this.value).toFixed(1);
            vals[ids.indexOf(id)] = parseFloat(this.value);
        }
    }
    document.getElementById("engine-slider").oninput = function() {
        document.getElementById("petrol-val").innerHTML = parseFloat(this.value).toFixed(1) + "%";
        document.getElementById("diesel-val").innerHTML = parseFloat(100 - this.value).toFixed(1) + "%";
        vals[5] = parseFloat(this.value);
    }
    document.getElementById("temperature").oninput = function() { vals[6] = parseFloat(this.value); }
    document.getElementById("draw").oninput = function() { vals[7] = this.checked; }
    document.getElementById("lower").onchange = function() { vals[8] = parseFloat(this.value); }
    document.getElementById("upper").onchange = function() { vals[9] = parseFloat(this.value); }
};

function downloadNetwork(zip_file) {
    modifierStr = getModifierStr();
    window.location.href="http://localhost:8000/download/"+zip_file+"/"+modifierStr;
}

function submitEditForm() {
    document.getElementById('ls-msg').innerHTML = "Modifying the network..."
    document.getElementById('ls-go').classList.add('ls-fadeIn');
    document.getElementById('edit-form').submit();
}

function resetEditor() {
    for (var i=0; i <ids.length; i++) {
        document.getElementById(ids[i]+"-slider").value = 1.0;
        document.getElementById(ids[i]+"-val").innerHTML = '1.0';
    }
    document.getElementById("engine-slider").value = 65.1;
    document.getElementById("petrol-val").innerHTML = "65.1%";
    document.getElementById("diesel-val").innerHTML = "34.9%";
    document.getElementById("diesel-val").innerHTML = "34.9%";
    document.getElementById("temperature").value = parseInt('10');
    document.getElementById("draw").checked = true;
    document.getElementById("lower").value = parseInt('0');
    document.getElementById("upper").value = parseInt('100');
}

function redirectTo(url) {
    ls = document.getElementById('ls-go')
    setTimeout(function(){ls.classList.add('ls-fadeIn');location.replace("http://localhost:8000/"+url+"/")}, 500);
}

function inspect(segID) {
    var x = document.getElementById('inspector');
    if (segID != 0) {
        modifierStr = getModifierStr();
        console.log("http://localhost:8000/inspector/"+segID+"/"+modifierStr)
        setTimeout(makeInspectorRequest("http://localhost:8000/inspector/"+segID+"/"+modifierStr), 1000);
    } else {
        x.classList.add('slideOut')
        setTimeout(function() {x.style.display = 'none'; x.classList.remove('slideOut')}, 1000)
    }
}

function makeInspectorRequest(url) {
    x = document.getElementById("inspector");
    x.innerHTML = "";
    $( "#inspector" ).load( url );
    x.style.display = "block";
}

function showSidebar() {
    var x = document.getElementById("sidebar");
    if (x.style.display === "none") {
        x.style.display = "table-cell";
        document.getElementById("sidebar-btn-show").style.display = "none";
    } else {
        x.style.display = "none";
        document.getElementById("sidebar-btn-show").style.display = "block";
    }
}

function togglePanel(panelID) {
    var x = document.getElementById(panelID);
    if (x.classList.contains('visible')) { 
        x.classList.remove('visible');
        x.classList.add('hidden');
        document.getElementById(panelID+"-hide").style.display = "none";
        document.getElementById(panelID+"-show").style.display = "block";
    } else {
        x.classList.add('visible');
        x.classList.remove('hidden');
        document.getElementById(panelID+"-show").style.display = "none";
        document.getElementById(panelID+"-hide").style.display = "block";
    }
}

function toggleAbout() {
    var x = document.getElementById('shadow-screen');
    if (x.style.display === "" || x.style.display === "none") {
        x.style.display = "block";
    } else {
        x.style.display = "none";
    }
}

function getModifierStr() {
    modifierStr = ""
    for (var i=0; i < vals.length; i++) {
        modifierStr += origVals[i]+","
    }
    return modifierStr.slice(0, -1);
}

function updateVals() {
    for (var i=0; i<ids.length; i++) {
        val = document.getElementById(ids[i]+"-slider").value;
        vals[i] = parseFloat(val);
        document.getElementById(ids[i]+"-val").innerHTML = parseFloat(val).toFixed(1);
    }
    vals[5] = parseFloat(document.getElementById("engine-slider").value);
    document.getElementById("temperature").value = parseFloat(document.getElementById("temperature").value)
    document.getElementById("lower").value = parseFloat(document.getElementById("lower").value)
    document.getElementById("upper").value = parseFloat(document.getElementById("upper").value)
    vals[6] = parseFloat(document.getElementById("temperature").value);
    vals[7] = document.getElementById("draw").checked;
    vals[8] = parseFloat(document.getElementById("lower").value);
    vals[9] = parseFloat(document.getElementById("upper").value);
    origVals = vals.slice()
}