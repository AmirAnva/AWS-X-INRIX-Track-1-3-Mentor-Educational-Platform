const menu=document.querySelector('#mobile-menu');
const menuLinks = document.querySelector('.navbar__menu');

let editor = new OverType(".editor", {
    toolbar: true, 
})

let submissionEditor = new OverType(".student-submission-overtype", {
    toolbar: false, 
    padding: '0px',
})
// submissionEditor[0].textarea.style.padding = "0px !important";

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

let newAssignmentForm = document.getElementById("new-assignment-form");
newAssignmentForm.addEventListener("submit", function(event) {
    event.preventDefault();
    
    let formData = new FormData(newAssignmentForm);
    fetch('/api/v1/create_assignment', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        console.log('New assignment response:', data);
        if (data.status === "success") {
            // After creating the assignment, go back to assignments view
            focusView("assignments");
        }
    })
})

let currentAssignmentId = null;
let submitAssignmentBtn = document.getElementById("submit-assignment-btn");
submitAssignmentBtn.addEventListener("click", function() {
    let formData = new FormData();
    formData.append("assignment_id", currentAssignmentId);
    formData.append("content", editor[0].textarea.value);
    loadHomePage();
    fetch('/api/v1/submit_assignment', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        console.log('Submit assignment response:', data);
        if (data.status === "success") {

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
        mentorChat.style.display = "flex";
    } else {
        mentorChat.style.display = "none";
    }
}


let IS_MENTOR = false; // will be set later
function loadHomePage() {
    fetch('/api/v1/home').then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    }).then(data => {
        console.log('Homepage data:', data);

        if (data.user_type == 1) {
            IS_MENTOR = true;
        }

        if (data.is_paired == null) {
            if (!IS_MENTOR) {
                focusView("no-pairing-student", false)
            } else { // A mentor
                focusView("no-pairing-teacher", false)
            }
        } else {
            focusView("assignments");
            if (IS_MENTOR) {
                let newAssignmentBtn = document.getElementById("new-assignment-btn");
                newAssignmentBtn.style.display = "block";
            }
            loadAssignments(data.assignments);
        }
    })
}

function htmlToObject(htmlString) {
    let template = document.createElement('template');
    template.innerHTML = htmlString.trim();
    return template.content.firstChild;
}

function loadAssignments(assignments) {
    let assignmentList = document.getElementById("assignment-list");

    // drop all chuldren with class assignment
    let children = assignmentList.getElementsByClassName("assignment");
    while (children.length > 0) {
        children[0].parentNode.removeChild(children[0]);
    }

    for (let i = 0; i < assignments.length; i++) {
        let assignment = assignments[i];
        let html = `<div class="assignment" style="border-color: rgb(98, 162, 102)">
            <p class="assignment-type">Asynchronous Lecture</p>
            <h2>${assignment.title}</h2>
            <p class="assignment-description">${assignment.description}</p>
            <p class="assignment-due-date">Due ${assignment.due_date}</p>
        </div>`;
        let obj = htmlToObject(html);

        obj.addEventListener("click", function() {
            loadAssignment(assignment);
        })

        assignmentList.appendChild(obj);
    }
}

function loadAssignment(assignmentData) {
    if (!IS_MENTOR) {
        console.log("Loading assignment data:", assignmentData);
        let assignmentTitle = document.getElementById("assignment-title-full");
        let assignmentDescription = document.getElementById("assignment-description-full");
        let assignmentDueDate = document.getElementById("assignment-due-date-full");

        currentAssignmentId = assignmentData.id;

        console.log("Setting assignment title and description");
        console.log("Title:", assignmentData.title);
        console.log("Description:", assignmentData.description);

        console.log(assignmentTitle);
        console.log(assignmentDescription);

        assignmentTitle.textContent = assignmentData.title;
        assignmentDescription.textContent = assignmentData.description;
        assignmentDueDate.textContent = "Due Date: " + assignmentData.due_date;

        let lectureVideo = document.getElementById("lecture-video");
        lectureVideo.src = "/api/v1/assignment_file/" + assignmentData.id;

        focusView("assignment");
    } else {
        // fill in overtype textarea
        submissionEditor[0].setValue(assignmentData.submission.data || "");
        
        let aiKnowledgeGapText = document.getElementById("ai-knowledge-gaps")
        aiKnowledgeGapText.textContent = assignmentData.submission.ai_review || "No AI review available.";

        focusView("assignment-feedback")

    }
    
}


loadHomePage();