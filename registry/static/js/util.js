//
// General util functions used sitewide
//

let submitForm = async (e, form, endpoint, callback) => {

    e.preventDefault()

    const body = JSON.stringify(getFormData(form))

    const response = await fetch(endpoint, {
        method: "POST",
        body: body,
        headers: {
          'Content-Type': 'application/json'
        }
    })

    if(callback){
        callback(response.ok)
    }

    if(!response.ok){
        console.log(response.error)
    }
}

let getFormData = (form) => {
    // Grabs all the form data as a dictionary of input information key'd by name

    const FD = new FormData(form);
    return Array.from(FD).reduce((currentValue,[name, value]) => {
        let component = {
            name: name,
            value: value,
        }

        if(document.getElementById(name)){
            component["label"] = document.getElementById(name).labels[0].textContent.trim()
        }

        currentValue[name] = component

        return currentValue
    }, {})
}