const menu=document.querySelector('#mobile-menu');
const menuLinks = document.querySelector('.navbar__menu');

menu.addEventListener('click', function() {
    menu.classList.toggle('is-active');
    menuLinks.classList.toggle('active');
});

document.getElementById("assignments-btn").addEventListener("click", function() {
    let assignmentsView = document.getElementById("assignments-view");
    assignmentsView.style.display = "block";

    let scratchPad = document.getElementById("scratch-pad");
    scratchPad.style.display = "none";
    
    let assignmentView = document.getElementById("assignment-view");
    assignmentView.style.display = "none";``
});