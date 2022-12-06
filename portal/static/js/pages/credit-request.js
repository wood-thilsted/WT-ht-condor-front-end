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

submitButton.addEventListener(
    "click",
    (e) => {
        let metadata = {
            subject: "PATh User - Credit Request"
        }

        submitForm(e, form, "/api/v1/freshdesk/ticket", callback, metadata)
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
        cpu = parseInt(cpu)
        memory = parseInt(memory)
        gpu = parseInt(gpu)
        walltime = parseInt(walltime)
        runs = parseInt(runs)

        // Report if a task is invalid for calculating
        if([cpu, memory, walltime, runs].filter(x => isNaN(x)).length > 1){
            return {
                gpu: 0,
                cpu: 0,
                errors: "Missing Required Value [Runs, CPU, Memory, Walltime, Disk]"
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
        memory = nominal - (cores*nominal)
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
    constructor({id, label, constructor, containerOptions = {}, nodeOptions = {}, buttonOptions = {}}) {

        // Set the internal data
        if(id){
            this.container = document.getElementById(id)
        } else {
            this.container = createNode({tagName: "div"})
        }
        this.nodes = []
        this.nodeConstructor = constructor
        this.nodeOptions = nodeOptions

        // Create the interactive elements
        this.nodeContainer = createNode({tagName: "div", ...containerOptions})

        this.removeNodeButton = createNode({tagName: "button",  innerText: "-", type: "button", ...buttonOptions})
        this.removeNodeButton.addEventListener("click", this.removeNode.bind(this))
        this.removeNodeButtonContainer = createNode({tagName: "div", children: [this.removeNodeButton], className: "col-6"})

        this.addNodeButton = createNode({tagName: "button",  innerText: "+", type: "button", ...buttonOptions})
        this.addNodeButton.addEventListener("click", this.addNode.bind(this))
        this.addNodeButtonContainer = createNode({tagName: "div", children: [this.addNodeButton], className: "col-6"})

        this.buttonContainer = createNode({
            tagName: "div",
            children: [this.removeNodeButtonContainer, this.addNodeButtonContainer],
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
    addNode() {
        let newNode = new this.nodeConstructor({id: this.nodes.length, ...this.nodeOptions})
        this.nodeContainer.appendChild(newNode.node)
        this.nodes.push(newNode)
    }
    removeNode(){
        this.nodeContainer.removeChild(this.nodeContainer.lastChild)
        this.nodes.pop()
    }
}

class Ensemble {
    constructor({ id, updateFunction }) {
        this.id = id
        this.updateFunction = updateFunction

        // Set up the node so I can attach listeners
        this.node
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
        return this.id
    }

    updateTitle() {
        this.titleNode.innerText = `Ensemble ${this.title}`
        for(const innerObject of [...this.tasks.nodes, ...this.sharedFiles.nodes]){
            innerObject.updateTitle()
        }
    }

    get node() {
        if(!this._node){
            this.titleNode = createNode({tagName: "h5", id: this.id, innerText: `Ensemble - ${this.title}`})
            this.errorNode = createNode({tagName: "div", className: "text-danger"})

            // Set up the input nodes
            let inputOptions = {className: "credit-cost-component form-control", type: "number", min: "0", step: "1"}

            this.name = new Input(`name-${this.id}`, {}, { innerText: "Name"})
            this.runs = new Input(`runs-${this.id}`, {}, { innerText: "Runs"}, inputOptions)
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

            this._node = createNode({tagName: "div", className: "border border-3 rounded p-2 mb-2"})
            for(const node of [this.titleNode, this.name.node, this.runs.node, this.tasksHeader, this.tasks.node, this.sharedFilesHeader, this.sharedFiles.node]){
                this._node.appendChild(node)
            }
        }
        return this._node
    }
}

class SharedFile {
    constructor({id, ensemble}) {
        // Record General Information
        this.id = id
        this.ensemble = ensemble

        // Set up the node so I can attach listeners
        this.node
        this.name.node.addEventListener("change", this.updateTitle.bind(this))
    }

    get title() {
        if(this?.name?.value){
            return this.ensemble.title + "." +  this.name?.value
        }
        return this.ensemble.title + "." +  this.id
    }

    updateTitle() {
        this.titleNode.innerText = `Shared File ${this.title}`
    }

    get node() {
        if(!this._node){
            this.titleNode = createNode({tagName: "h5", id: this.id, innerText: `Shared File - ${this.title}`})

            // Create the input nodes
            let inputOptions = {className: "credit-cost-component form-control", type: "number", min: "0", step: "1"}

            this.name = new Input(`name-${this.compositeId}`, {}, { innerText: "Name"})
            this.size = new Input(`size-${this.compositeId}`, {}, { innerText: "Size ( in gigabytes )"}, inputOptions)

            // Create Parent Node
            this._node = createNode({tagName: "div", className: "border border-warning rounded p-2 my-2"})
            this._node.appendChild(this.titleNode)
            for(const input of this.inputs) {
                this._node.appendChild(input.node)
            }
        }
        return this._node
    }

    get inputs() {
        return [this.name, this.size]
    }

    get compositeId() {
        return this.ensemble.id + ".sharedFile." +  this.id
    }

    get json() {
        return {
            name: this.name.json,
            runs: this.size.json
        }
    }
}

class Task {
    constructor({id, ensemble}) {
        // Log General information
        this.id = id
        this.ensemble = ensemble

        // Set up the node so I can attach listeners
        this.node
        this.name.node.addEventListener("change", this.updateTitle.bind(this))
    }

    get title() {
        if(this?.name?.value){
            return this.ensemble.title + "." +  this.name?.value
        }
        return this.ensemble.title + "." +  this.id
    }

    updateTitle() {
        this.titleNode.innerText = `Task ${this.title}`
    }

    get node() {
        if(! this._node){
            // Create the input nodes
            this.titleNode = createNode({tagName: "h5", id: this.id, innerText: `Task - ${this.title}`})
            this.errorNode = createNode({tagName: "div", className: "text-danger"})
            this.name = new Input(`name-${this.compositeId}`, {}, { innerText: "Name"})

            // Group these together so we can make the task more compact
            let parentOptions = {className: "col-6"}
            let inputOptions = {className: "credit-cost-component form-control", type: "number", min: "0", step: "1"}

            this.runs = new Input(`runs-${this.compositeId}`, parentOptions, { innerText: "Runs"}, inputOptions)
            this.cpuCores = new Input(`cpu-cores-${this.compositeId}`, parentOptions, { innerText: "CPU Cores"}, inputOptions)
            this.gpus = new Input(`gpu-${this.compositeId}`, parentOptions, { innerText: "GPUs"}, inputOptions)
            this.memory = new Input(`memory-${this.compositeId}`, parentOptions, { innerText: "Memory ( in gigabytes )"}, inputOptions)
            this.disk = new Input(`disk-${this.compositeId}`, parentOptions, { innerText: "Disk ( in gigabytes )"}, inputOptions)
            this.walltime = new Input(`walltime-${this.compositeId}`, parentOptions, { innerText: "Walltime ( in hours )"}, inputOptions)
            this.taskInputContainer = createNode({
                tagName: "div",
                children: [this.runs.node, this.cpuCores.node, this.gpus.node, this.memory.node, this.disk.node, this.walltime.node],
                className: "row"
            })

            // Create Parent Node
            this._node = createNode({
                tagName: "div",
                children: [this.titleNode, this.errorNode, this.name.node, this.taskInputContainer],
                className: "border border-info rounded p-2 my-2"
            })

            // Add listeners to the input nodes
            this.inputs.forEach(input => {
                input.node.addEventListener("change", this.ensemble.updateFunction)
            })
        }

        return this._node
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

    get json() {
        return {
            name: this.name.json,
            runs: this.runs.json,
            cpuCores: this.cpuCores.json,
            gpus: this.gpus.json,
            memory: this.memory.json,
            walltime: this.walltime.json
        }
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

