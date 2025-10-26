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

// teacher pairing button
let pairStudentForm = document.getElementById("pair-student-form");
pairStudentForm.addEventListener("submit", function(event) {
    event.preventDefault(); 

    let formData = new FormData(pairStudentForm);
    
    fetch('/api/v1/pair_user', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        console.log('Pairing response:', data);
        if (data.status === "success") {
            // reload the homepage to reflect pairing
            loadHomePage();
        } else {
            const errorText = document.getElementById("pair-error-text");
            errorText.style.opacity = "1";
            errorText.textContent = data.error;
        }
    })

})
function focusView(viewId, showMentorChat=true) {
    let views = document.getElementsByClassName("full-screen-page");
    for (let i = 0; i < views.length; i++) {
        views[i].style.opacity = "0";
        views[i].style.pointerEvents = "none";
    }
    let targetView = document.getElementById(viewId);
    targetView.style.opacity = "1";
    targetView.style.pointerEvents = "auto";

    let mentorChat = document.getElementById("chat-sidebar");
    console.log(mentorChat)
    if (showMentorChat) {
        mentorChat.style.display = "block";
    } else {
        mentorChat.style.display = "none";
    }
}

function loadHomePage() {
    fetch('/api/v1/home').then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    }).then(data => {
        console.log('Homepage data:', data);
        if (data.is_paired == null) {
            if (data.user_type == 0) { // A student
                focusView("no-pairing-student", false)
            } else { // A mentor
                focusView("no-pairing-teacher", false)
            }
        }


    })
}

loadHomePage();