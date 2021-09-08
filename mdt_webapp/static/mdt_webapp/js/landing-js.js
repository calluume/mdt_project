window.onscroll = function() {
    var arrow = document.getElementById("homescreen-scroll");
    if (window.pageYOffset > 0) {
        arrow.style.bottom = "-24px";
        arrow.style.opacity= "0";
    } else {
        arrow.style.bottom = "30px";
        arrow.style.opacity= "1";
    }
}

function redirectTo(url) {
    ls = document.getElementById('ls-go')
    setTimeout(function(){ls.classList.add('ls-fadeIn');location.replace("http://localhost:8000/"+url+"/")}, 500);
}