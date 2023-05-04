let submitButton = document.getElementById("submit")
let form = document.getElementById("request-form")

let statusSelect = document.getElementById("nsf-fos")
statusSelect.addEventListener("change", (e) => {
    if(e.target.value == "na"){
        document.getElementById("questions-for-the-nsf").hidden = true
    } else {
        document.getElementById("questions-for-the-nsf").hidden = false
    }
})

function bodyFunction (form, metadata) {
    const formData = getFormData(form)

    // Build the description text
    let description = Object.entries(formData).reduce((previousValue, [k, v]) => {
        if(!['h-captcha-response', 'g-recaptcha-response'].includes(k) && !k.includes(".") && "label" in v){
            previousValue += `<h4>\n${v['label']}\n</h4>\n`
            previousValue += `<p>\n${v['value']}\n</p>\n`
        }
        return previousValue
    }, "")

    description += creditRequestPage.ensembleNodeContainer.html

    description += `<h4>Ensemble JSON</h4>\n<code>${JSON.stringify(creditRequestPage.ensembleNodeContainer.json)}</code>`

    const body = {
        ...formData,
        ...metadata,
        email: formData['email']['value'],
        name: formData['full-name']['value'],
        description: description
    }

    return JSON.stringify(body)
}

submitButton.addEventListener(
    "click",
    (e) => {
        let metadata = {
            subject: "PATh User - Credit Request"
        }

        submitForm(e, form, "/api/v1/freshdesk/ticket", callback, metadata, bodyFunction)
    }
)

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

class CreditCalculator {

    /**
     *
     * @param cpu
     * @param memory
     * @param gpu
     * @param walltime
     * @param runs
     * @returns {Object}
     */
    static calculateCost = ({cpu, memory, gpu, walltime, runs}) => {
        cpu = isInt(cpu) ? parseInt(cpu) : NaN
        memory = isInt(memory) ? parseInt(memory) : NaN
        gpu = isInt(gpu) ? parseInt(gpu) : NaN
        walltime = parseFloat(walltime)
        runs = isInt(runs) ? parseInt(runs) : NaN

        // Report if a task is invalid for calculating
        if([cpu, memory, walltime, runs].filter(x => isNaN(x)).length > 0){
            return {
                gpu: 0,
                cpu: 0,
                errors: "Missing or Invalid Input: Integers allowed for all, Disk and Walltime allow decimals."
            }
        }

        const creditMultiplier = walltime * runs

        if(gpu > 0){
            let gpuCredits = CreditCalculator.calculateGpuCost({gpu, cpu, memory})

            if(typeof gpuCredits === "string"){
                return {
                    gpu: 0,
                    cpu: 0,
                    errors: gpuCredits
                }
            } else {
                return {
                    gpu: gpuCredits * creditMultiplier,
                    cpu: 0,
                    errors: ""
                }
            }

        } else {
            let cpuCredits = CreditCalculator.calculateCpuCost({cpu, memory})

            if(typeof cpuCredits === "string"){
                return {
                    gpu: 0,
                    cpu: 0,
                    errors: cpuCredits
                }
            } else {
                return {
                    gpu: 0,
                    cpu: cpuCredits * creditMultiplier,
                    errors: ""
                }
            }
        }
    }

    static calculateCpuCost = ({cpu, memory}) => {
        const cpuCost = CreditCalculator.cpu(cpu)
        const cpuMemoryCost = CreditCalculator.cpuMemory(memory, cpu)

        // Check for Error Strings Returned
        let errorStrings = [cpuCost, cpuMemoryCost].filter(x => typeof x == "string")
        if(errorStrings.length !== 0){
            return errorStrings.join("\n")
        }

        return cpuCost + cpuMemoryCost
    }

    static calculateGpuCost = ({gpu, cpu, memory}) => {

        let gpuCost = CreditCalculator.gpus(gpu)
        let gpuCpuCost = CreditCalculator.gpuCpus(gpu, cpu)
        let gpuMemoryCost = CreditCalculator.gpuMemory(gpu, memory)


        let errorStrings = [gpuCost, gpuCpuCost, gpuMemoryCost].filter(x => typeof x == "string")
        if(errorStrings.length !== 0){
            return errorStrings.join("\n")
        }

        return  gpuCost + gpuCpuCost + gpuMemoryCost
    }

    static cpu = (cores) => {
        if(cores <= 1){
            return 1 * cores
        } else if(cores <= 8) {
            return 1.2 * cores
        } else if(cores <= 32) {
            return 1.5 * cores
        } else if(cores > 32) {
            return 2 * cores
        }
    }

    static cpuMemory = (memory, cores) => {
        const nominal = 2
        memory = memory - (cores*nominal)
        if(memory <= 0){
            return 0 * memory
        } else if(memory <= 6){
            return .125 * memory
        } else if(memory <= 30) {
            return .25 * memory
        } else if(memory <= 126) {
            return .375 * memory
        } else if(memory <= 512) {
            return .5 * memory
        } else {
            return "We are currently unable to fulfill memory requests greater then 512 GB"
        }
    }

    static gpus = (gpus) => {
        if(gpus === 1){
            return 1 * gpus
        } else if(gpus === 2){
            return 2 * gpus
        } else if(gpus === 3){
            return 1.5 * gpus
        } else if(gpus === 4){
            return 2 * gpus
        } else {
            return "We are currently unable to fulfill GPU requests greater then 4"
        }
    }

    static gpuCpus = (gpus, cpus) => {
        const nominal = 16
        cpus = cpus - (gpus * nominal)
        if(cpus <= 0){
            return 0 * cpus
        } else if(cpus <= 32) {
            return .125 * cpus
        } else if(cpus <= 48){
            return .2 * cpus
        } else {
            return "We are unable to fulfill requests for greater then 64 cpu cores per gpu"
        }
    }

    static gpuMemory = (gpus, memory) => {
        const nominal = 128
        memory = memory - (gpus * nominal)
        if(memory <= 0){
            return 0 * memory
        } else if(memory <= 256){
            return .012 * memory
        } else if(memory <= 384){
            return  .02 * memory
        } else {
            return "We are unable to fulfill requests for greater then 512 GB memory per gpu"
        }
    }
}

class NodeContainer {
    constructor({id, constructor, containerOptions = {}, nodeOptions = {}, buttonOptions = {}}) {

        // Private Attribute
        this._nodes = []

        // Set the internal data
        if(id){
            this.container = document.getElementById(id)
        } else {
            this.container = createNode({tagName: "div"})
        }
        this.nodeConstructor = constructor
        this.nodeOptions = { ...nodeOptions, container: this }

        // Create the interactive elements
        this.nodeContainer = createNode({tagName: "div", ...containerOptions})

        this.addNodeButton = createNode({tagName: "button",  innerText: `Add ${constructor.name} +`, type: "button", ...buttonOptions})
        this.addNodeButton.addEventListener("click", this.addNode.bind(this))
        this.addNodeButtonContainer = createNode({tagName: "div", children: [this.addNodeButton], className: "col-12"})

        this.buttonContainer = createNode({
            tagName: "div",
            children: [this.addNodeButtonContainer],
            className: "row mt-2"
        })

        for( const node of [this.nodeContainer, this.buttonContainer] ) {
            this.container.appendChild(node)
        }

        this.addNode()
    }
    get node() {
        return this.container
    }
    get nodes() {
        this._nodes = this._nodes.filter(x => x.node !== null)
        return this._nodes
    }
    get html() {
        return this.nodes.map(node => node.html).join("\n")
    }
    get json() {
        return this.nodes.map(node => node.json)
    }
    addNode() {
        let newNode = new this.nodeConstructor({id: this.nodes.length, ...this.nodeOptions})
        this.nodeContainer.appendChild(newNode.node)
        this.nodes.push(newNode)
    }
}

class Ensemble {
    constructor({ container, updateFunction }) {
        this.id = Math.random().toString().substring(2, 10); // Hope there isn't a collision
        this.container = container
        this.updateFunction = updateFunction

        // Set up the node so I can attach listeners
        this.node = this.createNode()
        this.name.node.addEventListener("change", this.updateTitle.bind(this))
    }

    get creditCost() {
        const taskCreditCost = this.tasks.nodes.reduce((pv, task) => {
            let {cpu, gpu} = task.creditCost
            return {
                cpu: pv['cpu'] += cpu,
                gpu: pv['gpu'] += gpu
            }
        }, {cpu: 0, gpu: 0})

        // Handle runs being set
        let runs = parseInt(this.runs.value)
        if(isNaN(runs)){
            this.errorNode.innerText = "Missing Required Ensemble Value [Runs]"
            runs = 0
        } else {
            this.errorNode.innerText = ""
        }

        return {
            cpu: taskCreditCost['cpu'] * runs,
            gpu: taskCreditCost['gpu'] * runs,
        }
    }

    get title() {
        if(this?.name?.value){
            return this.name?.value
        }
        return "<Ensemble Name>"
    }

    createNode(){
        this.name = new Input(`${this.id}.name`, {}, { innerText: "Name"}, { value: `Ensemble ${this.id.substring(0, 2)}`})
        this.titleNode = createNode({tagName: "h5", id: this.id, innerText: `Ensemble - ${this.title}`})
        this.closeButton = createNode({
            tagName: "img",
            src: "/static/index/images/x-square.svg",
            style: "height: 1.25rem; cursor: pointer;"
        })
        this.closeButton.addEventListener("click", this.delete.bind(this))
        this.topRow = createNode({
            tagName: "div",
            children: [this.titleNode, this.closeButton],
            className: "d-flex justify-content-between"
        })

        this.errorNode = createNode({tagName: "div", className: "text-danger"})

        // Set up the input nodes
        let inputOptions = {className: "credit-cost-component form-control", type: "number", value: "1", min: "0", step: "1", required: true}

        this.runs = new Input(`${this.id}.runs`, {}, { innerText: "Runs"}, inputOptions)
        this.runs.node.addEventListener("change", this.updateFunction)

        // Set up the tasks input
        this.tasksHeader = createNode({tagName: "h4", innerText: "Tasks", className: "text-info"})
        this.tasks = new NodeContainer({
            constructor: Task,
            nodeOptions: { ensemble: this },
            buttonOptions: { className: "border border-info form-control"}
        })

        // Set up the Shared Files input
        this.sharedFilesHeader = createNode({tagName: "h4", innerText: "Shared Files", className: "text-warning"})
        this.sharedFiles = new NodeContainer({
            constructor: SharedFile,
            nodeOptions: { ensemble: this },
            buttonOptions: { className: "border border-warning form-control"}
        })

        let node = createNode({
            tagName: "div",
            children: [
                this.topRow,
                this.errorNode,
                this.name.node,
                this.runs.node,
                this.tasksHeader,
                this.tasks.node,
                this.sharedFilesHeader,
                this.sharedFiles.node
            ],
            className: "border border-3 rounded p-2 mb-2"
        })

        return node
    }

    get html() {
        return `
        <div>
            <h4>Ensemble - ${this.name.value}</h4>
            <b>Runs: </b>${this.runs.value}<br>
            <h4>Shared Files</h4>
            ${this.sharedFiles.html}
            <h4>Tasks</h4>
            ${this.tasks.html}
        </div>
        `
    }

    get json() {
        return {
            name: this.name.value,
            runs: this.runs.value,
            tasks: this.tasks.json,
            sharedFiles: this.sharedFiles.json
        }
    }

    updateTitle() {
        this.titleNode.innerText = `Ensemble - ${this.title}`
        for(const innerObject of [...this.tasks.nodes, ...this.sharedFiles.nodes]){
            innerObject.updateTitle()
        }
    }

    delete() {
        this.node.remove()
        this.node = null
    }
}

class SharedFile {
    constructor({ensemble, container}) {
        // Record General Information
        this.id = Math.random().toString().substring(2, 10); // Hope there isn't a collision
        this.ensemble = ensemble
        this.container = container

        // Set up the node so I can attach listeners
        this.node = this.createNode()
    }

    static get name() {
        return "Shared File"
    }

    get title() {
        if(this?.name?.value){
            return this.ensemble.title + "." +  this.name?.value
        }
        return this.ensemble.title + ".<Shared File Name>"
    }

    updateTitle() {
        this.titleNode.innerText = `Shared File - ${this.title}`
    }

    createNode(){
        this.name = new Input(`${this.compositeId}.name`, {}, { innerText: "Name"}, { value: `Shared File ${this.id.substring(0, 2)}`})
        this.name.node.addEventListener("change", this.updateTitle.bind(this))

        // Create Top Row
        this.titleNode = createNode({tagName: "h5", id: this.id, innerText: `Shared File - ${this.title}`})
        this.closeButton = createNode({
            tagName: "img",
            src: "/static/index/images/x-square.svg",
            style: "height: 1.25rem; cursor: pointer;"
        })
        this.closeButton.addEventListener("click", this.delete.bind(this))
        this.topRow = createNode({
            tagName: "div",
            children: [this.titleNode, this.closeButton],
            className: "d-flex justify-content-between"
        })

        // Create the input nodes
        let inputOptions = {className: "credit-cost-component form-control", placeholder: "1.0 (Decimal)", required: true}

        this.size = new Input(`${this.compositeId}.size`, {}, { innerText: "Size ( in gigabytes )"}, inputOptions)

        // Create Parent Node
        let node = createNode({tagName: "div", className: "border border-warning rounded p-2 my-2"})
        node.appendChild(this.topRow)
        for(const input of this.inputs) {
            node.appendChild(input.node)
        }

        return node
    }

    get inputs() {
        return [this.name, this.size]
    }

    get compositeId() {
        return this.ensemble.id + ".sharedFile." +  this.id
    }

    get html() {
        return `
        <div>
            <b>Shared File - ${this.name.value}</b><br>
            <b>Size ( in GB ): </b>${this.size.value}<br>
        </div>
        `
    }

    get json() {
        return {
            name: this.name.value,
            runs: this.size.value
        }
    }

    delete() {
        this.node.remove()
        this.node = null
    }
}

class Task {
    constructor({ensemble, container}) {
        // Log General information
        this.id = Math.random().toString().substr(2, 10);
        this.ensemble = ensemble
        this.container = container

        // Set up the node so I can attach listeners
        this.node = this.createNode()
        this.name.node.addEventListener("change", this.updateTitle.bind(this))
    }

    get title() {
        if(this?.name?.value){
            return this.ensemble.title + "." +  this.name?.value
        }
        return this.ensemble.title + ".<Task Name>"
    }

    updateTitle() {
        this.titleNode.innerText = `Task - ${this.title}`
    }

    createNode(){
        // Create the name node ( Must be first so the title can use its value )
        this.name = new Input(`name-${this.compositeId}`, {}, { innerText: "Name"}, { value: `Task ${this.id.substring(0, 2)}`})

        // Create top bar
        this.titleNode = createNode({tagName: "h5", className: "mb-0", id: this.id, innerText: `Task - ${this.title}`})
        this.closeButton = createNode({
            tagName: "img",
            src: "/static/index/images/x-square.svg",
            style: "height: 1.25rem; cursor: pointer;"
        })
        this.closeButton.addEventListener("click", this.delete.bind(this))
        this.topRow = createNode({
            tagName: "div",
            children: [this.titleNode, this.closeButton],
            className: "d-flex justify-content-between"
        })
        this.errorNode = createNode({tagName: "div", className: "text-danger"})

        // Group these together so we can make the task more compact
        let parentOptions = {className: "col-6"}
        let inputOptions = {className: "credit-cost-component form-control", type: "number", min: "0", step: "1", placeholder: "1 (Integer)", required: true}

        this.runs = new Input(`${this.compositeId}.runs`, parentOptions, { innerText: "Unique Inputs/Simulations"}, inputOptions)
        this.cpuCores = new Input(`${this.compositeId}.cpu-cores`, parentOptions, { innerText: "CPU Cores"}, inputOptions)
        this.gpus = new Input(`${this.compositeId}.gpu`, parentOptions, { innerText: "GPUs"}, inputOptions)
        this.memory = new Input(`${this.compositeId}.memory`, parentOptions, { innerText: "Memory ( in gigabytes )"}, inputOptions)
        this.disk = new Input(`d${this.compositeId}.disk`, parentOptions, { innerText: "Disk ( in gigabytes )"}, {className: "credit-cost-component form-control", placeholder: "1.0 (Decimal)", required: true})
        this.walltime = new Input(`${this.compositeId}.name`, parentOptions, { innerText: "Walltime ( in hours )"}, {className: "credit-cost-component form-control", placeholder: "1.0 (Decimal)", required: true})
        this.taskInputContainer = createNode({
            tagName: "div",
            children: [this.runs.node, this.cpuCores.node, this.gpus.node, this.memory.node, this.disk.node, this.walltime.node],
            className: "row"
        })

        // Add listeners to the input nodes
        this.inputs.forEach(input => {
            input.node.addEventListener("change", this.ensemble.updateFunction)
        })

        // Create Parent Node
        let node = createNode({
            tagName: "div",
            children: [this.topRow, this.errorNode, this.name.node, this.taskInputContainer],
            className: "border border-info rounded p-2 my-2"
        })

        return node
    }

    get inputs() {
        return [this.name, this.runs, this.cpuCores, this.gpus, this.memory, this.disk, this.walltime]
    }

    get creditCost() {
        const creditCost = CreditCalculator.calculateCost({
            cpu: this.cpuCores.value,
            memory: this.memory.value,
            gpu: this.gpus.value,
            walltime: this.walltime.value,
            runs: this.runs.value
        })

        if(creditCost.errors){
            this.errorNode.innerText = creditCost.errors
        } else {
            this.errorNode.innerText = ""
        }

        return creditCost
    }

    get compositeId() {
        return this.ensemble.id + ".task." +  this.id
    }

    get html() {
        return `
        <div>
            <b>Task - ${this.name.value}</b><br>
            <b>Runs: </b>${this.runs.value}<br>
            <b>CPU Cores: </b>${this.cpuCores.value}<br>
            <b>GPUs: </b>${this.gpus.value}<br>
            <b>Memory ( in GB ): </b>${this.memory.value}<br>
            <b>Walltime ( in Hours ): </b>${this.walltime.value}<br>
            <b>Disk ( in GB ): </b>${this.disk.value}<br>
        </div>
        `
    }

    get json() {
        return {
            name: this.name.value,
            runs: this.runs.value,
            cpuCores: this.cpuCores.value,
            gpus: this.gpus.value,
            memory: this.memory.value,
            walltime: this.walltime.value,
            disk: this.disk.value
        }
    }

    delete() {
        this.node.remove()
        this.node = null
    }
}


class CreditRequestPage{
    constructor() {
        this.ensembleNodeContainer = new NodeContainer({
            id: "ensembles",
            constructor: Ensemble,
            nodeOptions: { updateFunction: this.updateCreditCost.bind(this) },
            buttonOptions: { type: "button", className: "border border-3 form-control"}
        })

        this.cpuCreditTotalNode = document.getElementById("cpu-credit-total")
        this.gpuCreditTotalNode = document.getElementById("gpu-credit-total")
    }

    updateCreditCost() {
        const ensembleCreditCost = this.ensembleNodeContainer.nodes.reduce((pv, ensemble) => {
            let {cpu, gpu} = ensemble.creditCost
            return {
                cpu: pv['cpu'] += cpu,
                gpu: pv['gpu'] += gpu
            }
        }, {cpu: 0, gpu: 0})

        this.cpuCreditTotalNode.value = Math.round(ensembleCreditCost['cpu'])
        this.gpuCreditTotalNode.value = Math.round(ensembleCreditCost['gpu'])
    }
}

const creditRequestPage = new CreditRequestPage();

