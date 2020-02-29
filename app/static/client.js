var el = x => document.getElementById(x);
var orig_img ;
function showPicker() {
    el("file-input").click();
}

function showPicked(input) {
    el("upload-label").innerHTML = input.files[0].name;
    var reader = new FileReader();
    reader.onload = function(e) {
        el("image-picked").src = e.target.result;
        orig_img = e.target.result;
        el("image-picked").className = "";
    };
    reader.readAsDataURL(input.files[0]);
    el("result-label").innerHTML = "" ;

}

function analyze() {
    var uploadFiles = el("file-input").files;
    if (uploadFiles.length !== 1) alert("Please select image to analyze!");

    el("analyze-button").innerHTML = "Analyzing...";
    el("result-label").innerHTML = "" ;
    var xhr = new XMLHttpRequest();
    var loc = window.location;
    xhr.open("POST", `${loc.protocol}//${loc.hostname}:${loc.port}/analyze`,
        true);

    xhr.responseType = 'arraybuffer';

    xhr.onerror = function() {
        alert(xhr.responseText);
    };
    xhr.onload = function(e) {
        if (this.readyState === 4) {
            var arrayBufferView = new Uint8Array( e.target.response );
            var blob = new Blob( [ arrayBufferView ], { type: "image/jpeg" } );
            var urlCreator = window.URL || window.webkitURL;
            var imageUrl = urlCreator.createObjectURL( blob );
            var img = document.querySelector( "#image-picked" );
            img.src = imageUrl;
        }
        el("analyze-button").innerHTML = "Analyze";
        el("result-label").innerHTML = "Click on the image to cycle through x-ray and the segmentation" ;
    };

    var fileData = new FormData();
    fileData.append("file", uploadFiles[0]);
    xhr.send(fileData);
}


function cycle_image() {
    aux=el("image-picked").src;
    el("image-picked").src = orig_img ;
    orig_img=aux;
}


