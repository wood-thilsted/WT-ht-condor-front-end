//
// Code for application page form submission
//

let submitButton = document.getElementById("submit")
let form = document.getElementById("consultation-form")

submitButton.addEventListener("click", (e) => submitForm(e, form, "/api/v1/freshdesk/ticket", callback))

let statusSelect = document.getElementById("status")
statusSelect.addEventListener("change", (e) => {
    if(e.target.value == "awarded"){
        document.getElementById("questions-for-the-awarded").hidden = false
    } else {
        document.getElementById("questions-for-the-awarded").hidden = true
    }
})

let callback = (submissionSuccess, json) => {
    if(submissionSuccess){
        submissionSuccessCallback(json)
    } else {
        console.log(json)
        submissionFailureCallback()
    }
}

let submissionSuccessCallback = (json) => {
    const successModalNode = document.getElementById("success-modal")
    const successModal = new bootstrap.Modal(successModalNode)

    const userEmail = document.getElementById("user-email")
    userEmail.textContent = json?.email?.value

    successModal.show()
}

let submissionFailureCallback = () => {
    const failureModalNode = document.getElementById("failure-modal")
    const failureModal = new bootstrap.Modal(failureModalNode)

    const formInformationNode = document.getElementById("form-information")
    const formData = getFormData(form)
    const formInformation = Object.keys(formData)
        .filter(key => ['h-captcha-response', 'g-recaptcha-response'].indexOf(key) === -1)
        .reduce((currentValue, key) => {
            currentValue.push(`${formData[key]['label']}\r\n${formData[key]['value']}\r\n`)
            return currentValue
        }, [])
        .join('\r\n')
    formInformationNode.textContent = formInformation

    failureModal.show()
}
