const menu=document.querySelector('#mobile-menu');
const menuLinks = document.querrySelector('.navbar__menu');

MediaElementAudioSourceNode.addEventListener('click', function(){
    menu.classList.toggle('is-active');
    menuLinks.classList.toggle('active');
});