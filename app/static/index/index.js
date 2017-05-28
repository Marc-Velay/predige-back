//alert("works!");

function selectedTag() {
    var selectBox = document.getElementById("tagBoxFlights");
    var selectedValue = selectBox.options[selectBox.selectedIndex].value;
    var base = window.location.href.split('?')[0];
    var flight = window.location.href.split('?')[1].split('&')[0];
    window.location.href = base+'?'+flight+'&tag='+selectedValue;
}