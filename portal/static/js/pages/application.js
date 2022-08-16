//
// Code for application page form submission
//

let submitButton = document.getElementById("submit")
let form = document.getElementById("consultation-form")

submitButton.addEventListener("click", (e) => submitForm(e, form, "/api/v1/freshdesk/ticke", callback))

let callback = (submissionSuccess, json) => {
    if(submissionSuccess){
        submissionSuccessCallback(json)
    } else {
        submissionFailureCallback()
    }
}

let submissionSuccessCallback = (json) => {
    const successModalNode = document.getElementById("success-modal")
    const successModal = new bootstrap.Modal(successModalNode)

    const userEmail = document.getElementById("email")
    userEmail.textContent = json?.email

    successModal.show()
}

let submissionFailureCallback = () => {
    const failureModalNode = document.getElementById("failure-modal")
    const failureModal = new bootstrap.Modal(failureModalNode)

    const formInformationNode = document.getElementById("form-information")
    const formData = getFormData(form)
    const formInformation = formData.keys().reduce((currentValue, key) => {
        currentValue.append(`${formData[key]['label']}\n${formData[key]['value']}\n`)
    }, []).join('\n')
    formInformationNode.textContent = formInformation

    failureModal.show()
}
