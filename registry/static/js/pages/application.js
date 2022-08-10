//
// Code for application page form submission
//

let submitButton = document.getElementById("submit")
let form = document.getElementById("consultation-form")

submitButton.addEventListener("click", (e) => submitForm(e, form, "/api/v1/freshdesk/ticket", callback))

let callback = (submissionSuccess) => {
    if(submissionSuccess){
        submissionSuccessCallback()
    } else {
        submissionFailureCallback()
    }
}

let submissionSuccessCallback = () => {
    let successModalNode = document.getElementById("success-modal")
    let successModal = new bootstrap.Modal(successModalNode)
    successModal.show()
}

let submissionFailureCallback = () => {
    let failureModalNode = document.getElementById("failure-modal")
    let failureModal = new bootstrap.Modal(failureModalNode)
    failureModal.show()
}
