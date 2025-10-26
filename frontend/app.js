const menu=document.querySelector('#mobile-menu');
const menuLinks = document.querySelector('.navbar__menu');

menu.addEventListener('click', function() {
    menu.classList.toggle('is-active');
    menuLinks.classList.toggle('active');
});

document.getElementById("assignments-btn").addEventListener("click", function() {
    focusView("assignments");
});

document.getElementById("scratch-pad-btn").addEventListener("click", function() {
    focusView("scratch-pad");
})

function focusView(viewId) {
    let views = document.getElementsByClassName("full-screen-page");
    for (let i = 0; i < views.length; i++) {
        views[i].style.opacity = "0";
        views[i].style.pointerEvents = "none";
    }
    let targetView = document.getElementById(viewId);
    targetView.style.opacity = "1";
    targetView.style.pointerEvents = "auto";
}