//
// General util functions used sitewide
//

let submitForm = async (e, form, endpoint, callback, metadata, bodyFunction) => {

    e.preventDefault()

    if(!validateForm(form)){ return; } // Validate the form

    let body = bodyFunction(form, metadata)

    let response;
    let json;
    try {
        response = await fetch(endpoint, {
            method: "POST",
            body: body,
            headers: {
              'Content-Type': 'application/json'
            }
        })
        json = await response.json()
    } catch (e) {
        console.error(e)
    }

    if(!response?.ok){
        console.log(json)
    }

    if(callback){
        callback(response?.ok, getFormData(form))
    }
}

let validateForm = (form) => {

    const errorNode = document.getElementById("form-error")

    // Check that all input validity
    for (const el of form.querySelectorAll("[required]")) {
      if (isVisible(el) && !el.reportValidity()) {
        errorNode.textContent = "Please fill out all elements in the form, if not applicable you can write 'NA'.";
        errorNode.hidden = false;
        return false;
      }
    }

    // Check that the h captcha is populated
    const formData = getFormData(form)
    if( !formData['h-captcha-response']['value'] ){
        errorNode.textContent = "Complete the hCaptcha";
        errorNode.hidden = false;
        return false;
    }

    // Form is valid
    return true;
}



/**
 * Grabs all the form data as a dictionary of input information key'd by name
 * @param form - Form element
 * @returns {{}}
 */
let getFormData = (form) => {

    // Create default inputs for elements that are not reported if values are none
    let defaults = Array.from(form.getElementsByTagName("input")).reduce((currentValue, element) => {
        console.log(element)
        if(element.type == "checkbox"){
            currentValue.push([element.name, "off"])
        }
        return currentValue
    }, [])

    const formData = new FormData(form);
    const formDataAndDefaults = defaults.concat(Array.from(formData)) // Order important, defaults should be overwritten

    let namesAndInputs = formDataAndDefaults.reduce((currentValue,[name, value]) => {
        currentValue[name] = {
            name: name,
            value: value
        }

        let element = document.getElementById(name)

        if(element?.tagName === "SELECT"){
            currentValue[name]["value"] = document.querySelectorAll(`option[value=${value}]`)[0].textContent.trim()
        }

        if(isVisible(element)){
            currentValue[name]["label"] = document.getElementById(name).labels[0].textContent.trim()
        }

        return currentValue
    }, {})

    // Convert 'off' and 'on' check values to bools
    Object.keys(namesAndInputs).forEach((k,i) => {
        if(['off', 'on'].includes(namesAndInputs[k].value)){
            namesAndInputs[k].value = namesAndInputs[k].value === "off" ? "False" : "True";
        }
    })

    return namesAndInputs
}

let formDataToHtml = (formData) => {
    const html = Object.entries(formData).reduce((previousValue, [k, v]) => {
        if(!['h-captcha-response', 'g-recaptcha-response'].includes(k) && !k.includes(".") && "label" in v){
            previousValue += `<h4>\n${v['label']}\n</h4>\n`
            previousValue += `<p>\n${v['value']}\n</p>\n`
        }
        return previousValue
    }, "")

    return html
}

let isVisible = (htmlElement) => {
    try {
        return htmlElement.offsetParent !== null
    } catch (e) {
        console.error(e)
        return false
    }
}

function isInt(v){
    return parseInt(v) === parseFloat(v)
}

/**
 *
 * @param tagName
 * @param children {Array}
 * @param options
 * @returns {HTMLElement}
 */
let createNode = ({tagName, children = [], ...options}) => {
    let node = document.createElement(tagName)

    Object.entries(options).forEach(([k, v]) => {
        node.setAttribute(k, v);
        node[k] = v;
    })
    children.forEach(n => node.appendChild(n))
    return node
}

/** Creates an input element
 *
 * @param id
 * @param parentOptions
 * @param labelOptions
 * @param inputOptions
 * @returns {HTMLElement}
 */
let createInput = (id, parentOptions, labelOptions, inputOptions) => {
    let parentNode = createNode({tagName: "div", ...parentOptions})
    let labelNode = createNode({tagName: "label", ...labelOptions})
    let inputNode = createNode({tagName: "input", ...inputOptions})
    parentNode.appendChild(labelNode)
    parentNode.appendChild(inputNode)
    return parentNode
}

class Input {
    constructor(id, parentOptions = {}, labelOptions = {}, inputOptions = {}) {
        this.id = id
        this.parentNode = createNode({tagName: "div", ...parentOptions})
        this.labelNode = createNode({
            tagName: "label",
            for: id,
            ...labelOptions
        })
        this.inputNode = createNode({
            tagName: "input",
            id: id,
            name: id,
            className: "form-control",
            ...inputOptions
        })
        this.parentNode.appendChild(this.labelNode)
        this.parentNode.appendChild(this.inputNode)
    }

    get node() {
        return this.parentNode
    }

    get value() {
        return this.inputNode.value
    }

    get json() {
        return {
            value: this.value,
            label: this.labelNode.innerText,
            name: this.id
        }
    }
}

