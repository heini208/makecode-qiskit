namespace microQiskitRuntime {
    const ONE_OVER_SQRT_TWO = 0.70710678118
    const PI = 3.141592653589793
    const MAX_QUBITS = 8
    const MAX_SHOTS = 2048
    const IBM_REPLY_TIMEOUT_TENTHS = 50
    const IBM_RESULT_TIMEOUT_TENTHS = 6000

    class Gate {
        kind: string
        qubit: number
        target: number
        theta: number
        real: number[]
        imaginary: number[]

        constructor(kind: string) {
            this.kind = kind
            this.qubit = 0
            this.target = 0
            this.theta = 0
            this.real = []
            this.imaginary = []
        }
    }

    class Circuit {
        id: string
        name: string
        numQubits: number
        numClbits: number
        data: Gate[]

        constructor(id: string, numQubits: number, numClbits: number) {
            this.id = id
            this.name = ""
            this.numQubits = numQubits
            this.numClbits = numClbits
            this.data = []
        }
    }

    class QuantumState {
        real: number[]
        imaginary: number[]

        constructor(size: number) {
            this.real = []
            this.imaginary = []

            for (let i = 0; i < size; i++) {
                this.real.push(0)
                this.imaginary.push(0)
            }

            this.real[0] = 1
        }
    }

    class Job {
        id: string
        circuitId: string
        shots: number
        source: string
        status: string
        remoteJobId: string
        backend: string
        error: string
        statusResponseCounter: number
        resultResponseCounter: number
        memory: string[]
        countLabels: string[]
        counts: number[]
        probabilityLabels: string[]
        probabilities: number[]
        stateReal: number[]
        stateImaginary: number[]

        constructor(id: string, circuitId: string, shots: number) {
            this.id = id
            this.circuitId = circuitId
            this.shots = shots
            this.source = "local"
            this.status = "done"
            this.remoteJobId = ""
            this.backend = ""
            this.error = ""
            this.statusResponseCounter = 0
            this.resultResponseCounter = 0
            this.memory = []
            this.countLabels = []
            this.counts = []
            this.probabilityLabels = []
            this.probabilities = []
            this.stateReal = []
            this.stateImaginary = []
        }
    }

    let circuits: Circuit[] = []
    let jobs: Job[] = []
    let nextCircuitId = 1
    let nextJobId = 1
    let lastError = ""
    let ibmSerialInitialized = false

    function setError(message: string): void {
        lastError = message
    }

    function clearError(): void {
        lastError = ""
    }

    function powerOfTwo(exponent: number): number {
        return Math.pow(2, exponent)
    }

    function copyNumberArray(values: number[]): number[] {
        let copy: number[] = []

        for (let i = 0; i < values.length; i++) {
            copy.push(values[i])
        }

        return copy
    }

    function copyStringArray(values: string[]): string[] {
        let copy: string[] = []

        for (let i = 0; i < values.length; i++) {
            copy.push(values[i])
        }

        return copy
    }

    function copyGate(gate: Gate): Gate {
        const copy = new Gate(gate.kind)
        copy.qubit = gate.qubit
        copy.target = gate.target
        copy.theta = gate.theta
        copy.real = copyNumberArray(gate.real)
        copy.imaginary = copyNumberArray(gate.imaginary)
        return copy
    }

    function findCircuitIndex(circuitId: string): number {
        for (let i = 0; i < circuits.length; i++) {
            if (circuits[i].id == circuitId) {
                return i
            }
        }

        return -1
    }

    function findJobIndex(jobId: string): number {
        for (let i = 0; i < jobs.length; i++) {
            if (jobs[i].id == jobId) {
                return i
            }
        }

        return -1
    }

    function getCircuit(circuitId: string): Circuit {
        const index = findCircuitIndex(circuitId)

        if (index < 0) {
            setError("Circuit not found: " + circuitId)
            return null
        }

        return circuits[index]
    }

    function getJob(jobId: string): Job {
        const index = findJobIndex(jobId)

        if (index < 0) {
            setError("Job not found: " + jobId)
            return null
        }

        return jobs[index]
    }

    function validQubit(circuit: Circuit, qubit: number): boolean {
        if (
            qubit < 0 ||
            qubit >= circuit.numQubits ||
            qubit != Math.floor(qubit)
        ) {
            setError("Qubit index out of range: " + qubit)
            return false
        }

        return true
    }

    function validClassicalBit(circuit: Circuit, classicalBit: number): boolean {
        if (
            classicalBit < 0 ||
            classicalBit >= circuit.numClbits ||
            classicalBit != Math.floor(classicalBit)
        ) {
            setError("Classical bit index out of range: " + classicalBit)
            return false
        }

        return true
    }

    function appendSingleQubitGate(
        circuitId: string,
        kind: string,
        qubit: number,
        theta: number = 0
    ): void {
        clearError()
        const circuit = getCircuit(circuitId)

        if (!circuit || !validQubit(circuit, qubit)) {
            return
        }

        const gate = new Gate(kind)
        gate.qubit = qubit
        gate.theta = theta
        circuit.data.push(gate)
    }

    function appendControlledGate(
        circuitId: string,
        kind: string,
        control: number,
        target: number,
        theta: number = 0
    ): void {
        clearError()
        const circuit = getCircuit(circuitId)

        if (
            !circuit ||
            !validQubit(circuit, control) ||
            !validQubit(circuit, target)
        ) {
            return
        }

        if (control == target) {
            setError("Control and target qubits must be different")
            return
        }

        const gate = new Gate(kind)
        gate.qubit = control
        gate.target = target
        gate.theta = theta
        circuit.data.push(gate)
    }

    function bitAt(value: number, bit: number): number {
        return Math.floor(value / powerOfTwo(bit)) % 2
    }

    function basisLabel(value: number, width: number): string {
        let label = ""

        for (let bit = width - 1; bit >= 0; bit--) {
            label = label + bitAt(value, bit)
        }

        return label
    }

    function randomFraction(): number {
        return randint(0, 1000000) / 1000001
    }

    function stateNorm(state: QuantumState): number {
        let norm = 0

        for (let i = 0; i < state.real.length; i++) {
            norm +=
                state.real[i] * state.real[i] +
                state.imaginary[i] * state.imaginary[i]
        }

        return norm
    }

    function buildState(circuit: Circuit): QuantumState {
        const size = powerOfTwo(circuit.numQubits)
        const state = new QuantumState(size)

        for (let gateIndex = 0; gateIndex < circuit.data.length; gateIndex++) {
            const gate = circuit.data[gateIndex]

            if (gate.kind == "initialize") {
                if (gate.real.length != size || gate.imaginary.length != size) {
                    setError("Initial state has the wrong number of amplitudes")
                    return null
                }

                state.real = copyNumberArray(gate.real)
                state.imaginary = copyNumberArray(gate.imaginary)
            } else if (gate.kind == "measure") {
                // MicroQiskit treats measurements as final readout mappings.
            } else if (
                gate.kind == "x" ||
                gate.kind == "h" ||
                gate.kind == "rx" ||
                gate.kind == "rz"
            ) {
                const targetStep = powerOfTwo(gate.qubit)

                for (let b0 = 0; b0 < size; b0++) {
                    if (bitAt(b0, gate.qubit) != 0) {
                        continue
                    }

                    const b1 = b0 + targetStep
                    const xReal = state.real[b0]
                    const xImaginary = state.imaginary[b0]
                    const yReal = state.real[b1]
                    const yImaginary = state.imaginary[b1]

                    if (gate.kind == "x") {
                        state.real[b0] = yReal
                        state.imaginary[b0] = yImaginary
                        state.real[b1] = xReal
                        state.imaginary[b1] = xImaginary
                    } else if (gate.kind == "h") {
                        state.real[b0] = ONE_OVER_SQRT_TWO * (xReal + yReal)
                        state.imaginary[b0] = ONE_OVER_SQRT_TWO * (xImaginary + yImaginary)
                        state.real[b1] = ONE_OVER_SQRT_TWO * (xReal - yReal)
                        state.imaginary[b1] = ONE_OVER_SQRT_TWO * (xImaginary - yImaginary)
                    } else if (gate.kind == "rx") {
                        const cosine = Math.cos(gate.theta / 2)
                        const sine = Math.sin(gate.theta / 2)
                        state.real[b0] = xReal * cosine + yImaginary * sine
                        state.imaginary[b0] = xImaginary * cosine - yReal * sine
                        state.real[b1] = yReal * cosine + xImaginary * sine
                        state.imaginary[b1] = yImaginary * cosine - xReal * sine
                    } else {
                        const cosine = Math.cos(gate.theta / 2)
                        const sine = Math.sin(gate.theta / 2)
                        state.real[b0] = xReal * cosine + xImaginary * sine
                        state.imaginary[b0] = xImaginary * cosine - xReal * sine
                        state.real[b1] = yReal * cosine - yImaginary * sine
                        state.imaginary[b1] = yImaginary * cosine + yReal * sine
                    }
                }
            } else if (gate.kind == "cx" || gate.kind == "crx") {
                const targetStep = powerOfTwo(gate.target)

                for (let b0 = 0; b0 < size; b0++) {
                    if (bitAt(b0, gate.qubit) != 1 || bitAt(b0, gate.target) != 0) {
                        continue
                    }

                    const b1 = b0 + targetStep
                    const xReal = state.real[b0]
                    const xImaginary = state.imaginary[b0]
                    const yReal = state.real[b1]
                    const yImaginary = state.imaginary[b1]

                    if (gate.kind == "cx") {
                        state.real[b0] = yReal
                        state.imaginary[b0] = yImaginary
                        state.real[b1] = xReal
                        state.imaginary[b1] = xImaginary
                    } else {
                        const cosine = Math.cos(gate.theta / 2)
                        const sine = Math.sin(gate.theta / 2)
                        state.real[b0] = xReal * cosine + yImaginary * sine
                        state.imaginary[b0] = xImaginary * cosine - yReal * sine
                        state.real[b1] = yReal * cosine + xImaginary * sine
                        state.imaginary[b1] = yImaginary * cosine - xReal * sine
                    }
                }
            } else {
                setError("Unsupported gate: " + gate.kind)
                return null
            }
        }

        return state
    }

    function probabilitiesFromState(state: QuantumState): number[] {
        let probabilities: number[] = []

        for (let i = 0; i < state.real.length; i++) {
            probabilities.push(
                state.real[i] * state.real[i] +
                state.imaginary[i] * state.imaginary[i]
            )
        }

        return probabilities
    }

    function applyMeasurementNoise(
        probabilities: number[],
        numQubits: number,
        noiseModel: number[]
    ): boolean {
        if (noiseModel.length == 0) {
            return true
        }

        if (noiseModel.length != numQubits) {
            setError("Noise list must contain one probability per qubit")
            return false
        }

        const size = probabilities.length

        for (let qubit = 0; qubit < numQubits; qubit++) {
            const errorProbability = noiseModel[qubit]

            if (errorProbability < 0 || errorProbability > 1) {
                setError("Noise probabilities must be between 0 and 1")
                return false
            }

            const step = powerOfTwo(qubit)

            for (let b0 = 0; b0 < size; b0++) {
                if (bitAt(b0, qubit) != 0) {
                    continue
                }

                const b1 = b0 + step
                const p0 = probabilities[b0]
                const p1 = probabilities[b1]
                probabilities[b0] = (1 - errorProbability) * p0 + errorProbability * p1
                probabilities[b1] = (1 - errorProbability) * p1 + errorProbability * p0
            }
        }

        return true
    }

    function measurementMap(circuit: Circuit): number[] {
        let map: number[] = []
        let measurementSeen = false
        let measurementCount = 0

        for (let i = 0; i < circuit.numClbits; i++) {
            map.push(-1)
        }

        for (let i = 0; i < circuit.data.length; i++) {
            const gate = circuit.data[i]

            if (gate.kind == "measure") {
                measurementSeen = true
                measurementCount += 1
                map[gate.target] = gate.qubit
            } else if (measurementSeen) {
                setError("All measurement operations must be at the end")
                return null
            }
        }

        if (measurementCount == 0) {
            setError("Add at least one measurement before running shots")
            return null
        }

        return map
    }

    function measuredLabel(basisState: number, circuit: Circuit, map: number[]): string {
        let label = ""

        for (let classicalBit = circuit.numClbits - 1; classicalBit >= 0; classicalBit--) {
            const qubit = map[classicalBit]
            label = label + (qubit < 0 ? 0 : bitAt(basisState, qubit))
        }

        return label
    }

    function sampleBasisState(probabilities: number[]): number {
        const randomValue = randomFraction()
        let cumulative = 0

        for (let i = 0; i < probabilities.length; i++) {
            cumulative += probabilities[i]

            if (randomValue < cumulative) {
                return i
            }
        }

        return probabilities.length - 1
    }

    function addCount(job: Job, label: string): void {
        for (let i = 0; i < job.countLabels.length; i++) {
            if (job.countLabels[i] == label) {
                job.counts[i] += 1
                return
            }
        }

        let insertAt = job.countLabels.length

        for (let i = 0; i < job.countLabels.length; i++) {
            if (label < job.countLabels[i]) {
                insertAt = i
                break
            }
        }

        job.countLabels.insertAt(insertAt, label)
        job.counts.insertAt(insertAt, 1)
    }

    function setCount(job: Job, label: string, count: number): void {
        for (let i = 0; i < job.countLabels.length; i++) {
            if (job.countLabels[i] == label) {
                job.counts[i] = count
                return
            }
        }

        let insertAt = job.countLabels.length

        for (let i = 0; i < job.countLabels.length; i++) {
            if (label < job.countLabels[i]) {
                insertAt = i
                break
            }
        }

        job.countLabels.insertAt(insertAt, label)
        job.counts.insertAt(insertAt, count)
    }

    function handleIBMSerialMessage(message: string): void {
        const parts = message.split("|")

        if (parts.length < 2) {
            return
        }

        const messageKind = parts[0]
        const job = getJob(parts[1])

        if (!job || job.source != "ibm") {
            return
        }

        if (messageKind == "IBMQ_ACCEPTED" && parts.length >= 4) {
            job.remoteJobId = parts[2]
            job.backend = parts[3]
            job.status = "queued"
        } else if (messageKind == "IBMQ_STATUS" && parts.length >= 3) {
            job.status = parts[2].toLowerCase()
            job.statusResponseCounter += 1
        } else if (messageKind == "IBMQ_SHOT" && parts.length >= 3) {
            job.memory = [parts[2]]
        } else if (messageKind == "IBMQ_COUNT" && parts.length >= 4) {
            setCount(job, parts[2], parseInt(parts[3]))
        } else if (messageKind == "IBMQ_DONE") {
            if (parts.length >= 3) {
                job.shots = parseInt(parts[2])
            }
            job.status = "done"
            job.resultResponseCounter += 1
        } else if (messageKind == "IBMQ_ERROR" && parts.length >= 3) {
            job.error = parts[2]
            job.status = "failed"
            job.statusResponseCounter += 1
            job.resultResponseCounter += 1
        }
    }

    function initializeIBMSerial(): void {
        if (ibmSerialInitialized) {
            return
        }

        ibmSerialInitialized = true
        serial.redirectToUSB()
        serial.setRxBufferSize(512)
        serial.setTxBufferSize(512)
        serial.onDataReceived("\n", function () {
            handleIBMSerialMessage(serial.readUntil("\n"))
        })
    }

    function sendIBMLine(line: string): void {
        serial.writeLine(line)
        basic.pause(5)
    }

    function waitForIBMStatusReply(
        job: Job,
        previousStatusResponseCounter: number
    ): boolean {
        let remainingTenths = IBM_REPLY_TIMEOUT_TENTHS

        while (
            job.statusResponseCounter == previousStatusResponseCounter &&
            job.status != "failed" &&
            remainingTenths > 0
        ) {
            basic.pause(100)
            remainingTenths -= 1
        }

        if (job.statusResponseCounter != previousStatusResponseCounter) {
            return true
        }

        if (job.status == "failed") {
            setError(job.error == "" ? "IBM job failed" : job.error)
            return false
        }

        setError("The PC bridge did not return a status for job " + job.id)
        return false
    }

    function waitForIBMResult(job: Job, timeoutTenths: number): boolean {
        if (job.source != "ibm" || job.status == "done") {
            return true
        }

        if (job.status == "failed") {
            setError(job.error == "" ? "IBM job failed" : job.error)
            return false
        }

        const previousResultResponseCounter = job.resultResponseCounter
        sendIBMLine("IBMQ_GET_RESULT|" + job.id)
        let remainingTenths = timeoutTenths

        while (
            job.resultResponseCounter == previousResultResponseCounter &&
            job.status != "failed" &&
            remainingTenths > 0
        ) {
            basic.pause(100)
            remainingTenths -= 1
        }

        if (
            job.resultResponseCounter != previousResultResponseCounter &&
            job.status == "done"
        ) {
            return true
        }

        if (job.status == "failed") {
            setError(job.error == "" ? "IBM job failed" : job.error)
            return false
        }

        setError("Timed out waiting for IBM result " + job.id)
        return false
    }

    function countForOutcome(job: Job, outcome: string): number {
        for (let i = 0; i < job.countLabels.length; i++) {
            if (job.countLabels[i] == outcome) {
                return job.counts[i]
            }
        }

        return 0
    }

    function jobSourceLabel(job: Job): string {
        return job.source == "ibm" ? "IBM Quantum" : "Local simulation"
    }

    function countPercentage(count: number, shots: number): number {
        if (shots <= 0) {
            return 0
        }

        return Math.round(1000 * count / shots) / 10
    }

    function printJobCounts(job: Job): void {
        if (job.countLabels.length == 0) {
            if (job.status == "failed") {
                sendIBMLine("Error: " + job.error)
            } else {
                sendIBMLine("Results are not ready. Status: " + job.status)
            }
            return
        }

        sendIBMLine("Counts:")

        for (let i = 0; i < job.countLabels.length; i++) {
            const count = job.counts[i]
            sendIBMLine(
                "  " + job.countLabels[i] + ": " + count + " / " + job.shots +
                " (" + countPercentage(count, job.shots) + "%)"
            )
        }
    }

    export function printJobToSerial(jobId: string, view: number): void {
        clearError()
        const job = getJob(jobId)

        initializeIBMSerial()

        if (!job) {
            sendIBMLine("MicroQiskit error: job not found: " + jobId)
            return
        }

        if (view == 3) {
            const currentStatus = getJobStatus(jobId)
            sendIBMLine(
                "Qiskit job " + job.id + ": " + currentStatus +
                " (" + jobSourceLabel(job) + ")"
            )
            return
        }

        if (!waitForIBMResult(job, IBM_RESULT_TIMEOUT_TENTHS)) {
            sendIBMLine("MicroQiskit error: " + lastError)
            return
        }

        if (view == 1) {
            if (job.memory.length > 0) {
                sendIBMLine(
                    "Qiskit job " + job.id + " first shot (highest bit first): " +
                    job.memory[0]
                )
            } else if (job.status == "failed") {
                sendIBMLine("Qiskit job " + job.id + " failed: " + job.error)
            } else {
                sendIBMLine(
                    "Qiskit job " + job.id + " result is not ready. Status: " +
                    job.status
                )
            }
            return
        }

        if (view == 2) {
            sendIBMLine("=== Qiskit counts: " + job.id + " ===")
            printJobCounts(job)
            sendIBMLine("==============================")
            return
        }

        sendIBMLine("=== Qiskit job: " + job.id + " ===")
        sendIBMLine("Run on: " + jobSourceLabel(job))
        sendIBMLine("Status: " + job.status)
        sendIBMLine("Shots: " + job.shots)

        if (job.source == "ibm" && job.backend != "") {
            sendIBMLine("IBM system: " + job.backend)
        }

        if (job.source == "ibm" && job.remoteJobId != "") {
            sendIBMLine("IBM job ID: " + job.remoteJobId)
        }

        if (job.memory.length > 0) {
            sendIBMLine("First shot (highest bit first): " + job.memory[0])
        }

        printJobCounts(job)
        sendIBMLine("============================")
    }

    function runWithNoise(circuitId: string, shots: number, noiseModel: number[]): string {
        clearError()
        const circuit = getCircuit(circuitId)

        if (!circuit) {
            return ""
        }

        if (shots < 1 || shots > MAX_SHOTS || shots != Math.floor(shots)) {
            setError("Shots must be between 1 and " + MAX_SHOTS)
            return ""
        }

        const map = measurementMap(circuit)

        if (!map) {
            return ""
        }

        const state = buildState(circuit)

        if (!state) {
            return ""
        }

        let probabilities = probabilitiesFromState(state)

        if (!applyMeasurementNoise(probabilities, circuit.numQubits, noiseModel)) {
            return ""
        }

        const jobId = "job" + nextJobId
        nextJobId += 1
        const job = new Job(jobId, circuitId, shots)
        job.probabilities = copyNumberArray(probabilities)
        job.stateReal = copyNumberArray(state.real)
        job.stateImaginary = copyNumberArray(state.imaginary)

        for (let i = 0; i < probabilities.length; i++) {
            job.probabilityLabels.push(basisLabel(i, circuit.numQubits))
        }

        for (let shot = 0; shot < shots; shot++) {
            const basisState = sampleBasisState(probabilities)
            const label = measuredLabel(basisState, circuit, map)
            job.memory.push(label)
            addCount(job, label)
        }

        jobs.push(job)
        return jobId
    }

    export function createCircuit(numQubits: number, numClbits: number): string {
        clearError()

        if (numQubits < 1 || numQubits > MAX_QUBITS || numQubits != Math.floor(numQubits)) {
            setError("Qubits must be between 1 and " + MAX_QUBITS)
            return ""
        }

        if (numClbits < 0 || numClbits > MAX_QUBITS || numClbits != Math.floor(numClbits)) {
            setError("Classical bits must be between 0 and " + MAX_QUBITS)
            return ""
        }

        const circuitId = "circuit" + nextCircuitId
        nextCircuitId += 1
        circuits.push(new Circuit(circuitId, numQubits, numClbits))
        return circuitId
    }

    export function combineCircuits(firstCircuitId: string, secondCircuitId: string): string {
        clearError()
        const first = getCircuit(firstCircuitId)
        const second = getCircuit(secondCircuitId)

        if (!first || !second) {
            return ""
        }

        const combinedId = createCircuit(
            Math.max(first.numQubits, second.numQubits),
            Math.max(first.numClbits, second.numClbits)
        )
        const combined = getCircuit(combinedId)
        combined.name = first.name

        for (let i = 0; i < first.data.length; i++) {
            combined.data.push(copyGate(first.data[i]))
        }

        for (let i = 0; i < second.data.length; i++) {
            combined.data.push(copyGate(second.data[i]))
        }

        return combinedId
    }

    export function setCircuitName(circuitId: string, name: string): void {
        clearError()
        const circuit = getCircuit(circuitId)

        if (circuit) {
            circuit.name = name
        }
    }

    export function getCircuitName(circuitId: string): string {
        clearError()
        const circuit = getCircuit(circuitId)
        return circuit ? circuit.name : ""
    }

    export function getCircuitQubitCount(circuitId: string): number {
        clearError()
        const circuit = getCircuit(circuitId)
        return circuit ? circuit.numQubits : 0
    }

    export function getCircuitClassicalBitCount(circuitId: string): number {
        clearError()
        const circuit = getCircuit(circuitId)
        return circuit ? circuit.numClbits : 0
    }

    export function initializeRealState(circuitId: string, amplitudes: number[]): void {
        let imaginary: number[] = []

        for (let i = 0; i < amplitudes.length; i++) {
            imaginary.push(0)
        }

        initializeState(circuitId, amplitudes, imaginary)
    }

    export function initializeState(
        circuitId: string,
        real: number[],
        imaginary: number[]
    ): void {
        clearError()
        const circuit = getCircuit(circuitId)

        if (!circuit) {
            return
        }

        const expectedLength = powerOfTwo(circuit.numQubits)

        if (real.length != expectedLength || imaginary.length != expectedLength) {
            setError("Initial state needs " + expectedLength + " amplitudes")
            return
        }

        const candidate = new QuantumState(expectedLength)
        candidate.real = copyNumberArray(real)
        candidate.imaginary = copyNumberArray(imaginary)
        const norm = stateNorm(candidate)

        if (Math.abs(norm - 1) > 0.001) {
            setError("Initial state amplitudes must have norm 1")
            return
        }

        const gate = new Gate("initialize")
        gate.real = copyNumberArray(real)
        gate.imaginary = copyNumberArray(imaginary)
        circuit.data = []
        circuit.data.push(gate)
    }

    export function applyX(circuitId: string, qubit: number): void {
        appendSingleQubitGate(circuitId, "x", qubit)
    }

    export function applyY(circuitId: string, qubit: number): void {
        applyRZ(circuitId, PI, qubit)

        if (lastError == "") {
            applyX(circuitId, qubit)
        }
    }

    export function applyZ(circuitId: string, qubit: number): void {
        applyRZ(circuitId, PI, qubit)
    }

    export function applyH(circuitId: string, qubit: number): void {
        appendSingleQubitGate(circuitId, "h", qubit)
    }

    export function applyRX(circuitId: string, theta: number, qubit: number): void {
        appendSingleQubitGate(circuitId, "rx", qubit, theta)
    }

    export function applyRY(circuitId: string, theta: number, qubit: number): void {
        applyRX(circuitId, PI / 2, qubit)

        if (lastError == "") {
            applyRZ(circuitId, theta, qubit)
        }

        if (lastError == "") {
            applyRX(circuitId, -PI / 2, qubit)
        }
    }

    export function applyRZ(circuitId: string, theta: number, qubit: number): void {
        appendSingleQubitGate(circuitId, "rz", qubit, theta)
    }

    export function applyCX(circuitId: string, control: number, target: number): void {
        appendControlledGate(circuitId, "cx", control, target)
    }

    export function applyCRX(
        circuitId: string,
        theta: number,
        control: number,
        target: number
    ): void {
        appendControlledGate(circuitId, "crx", control, target, theta)
    }

    export function measureQubit(
        circuitId: string,
        qubit: number,
        classicalBit: number
    ): void {
        clearError()
        const circuit = getCircuit(circuitId)

        if (
            !circuit ||
            !validQubit(circuit, qubit) ||
            !validClassicalBit(circuit, classicalBit)
        ) {
            return
        }

        const gate = new Gate("measure")
        gate.qubit = qubit
        gate.target = classicalBit
        circuit.data.push(gate)
    }

    export function measureAll(circuitId: string): void {
        clearError()
        const circuit = getCircuit(circuitId)

        if (!circuit) {
            return
        }

        if (circuit.numClbits < circuit.numQubits) {
            setError("Measure all needs at least one classical bit per qubit")
            return
        }

        for (let qubit = 0; qubit < circuit.numQubits; qubit++) {
            const gate = new Gate("measure")
            gate.qubit = qubit
            gate.target = qubit
            circuit.data.push(gate)
        }
    }

    export function runSimulation(circuitId: string, shots: number = 1024): string {
        return runWithNoise(circuitId, shots, [])
    }

    export function runOnIBMQuantum(circuitId: string, shots: number = 1024): string {
        clearError()
        const circuit = getCircuit(circuitId)

        if (!circuit) {
            return ""
        }

        if (shots < 1 || shots > MAX_SHOTS || shots != Math.floor(shots)) {
            setError("Shots must be between 1 and " + MAX_SHOTS)
            return ""
        }

        if (!measurementMap(circuit)) {
            return ""
        }

        for (let i = 0; i < circuit.data.length; i++) {
            if (circuit.data[i].kind == "initialize") {
                setError("Custom initial states are not supported on IBM hardware")
                return ""
            }
        }

        const jobId = "job" + nextJobId
        nextJobId += 1
        const job = new Job(jobId, circuitId, shots)
        job.source = "ibm"
        job.status = "submitting"
        jobs.push(job)

        initializeIBMSerial()
        sendIBMLine(
            "IBMQ_BEGIN|" + jobId + "|" + circuit.numQubits + "|" +
            circuit.numClbits + "|" + shots
        )

        for (let i = 0; i < circuit.data.length; i++) {
            const gate = circuit.data[i]
            sendIBMLine(
                "IBMQ_GATE|" + jobId + "|" + gate.kind + "|" + gate.qubit +
                "|" + gate.target + "|" + gate.theta
            )
        }

        sendIBMLine("IBMQ_END|" + jobId)
        return jobId
    }

    export function runSimulationWithUniformNoise(
        circuitId: string,
        shots: number,
        errorProbability: number
    ): string {
        clearError()
        const circuit = getCircuit(circuitId)

        if (!circuit) {
            return ""
        }

        let noiseModel: number[] = []

        for (let i = 0; i < circuit.numQubits; i++) {
            noiseModel.push(errorProbability)
        }

        return runWithNoise(circuitId, shots, noiseModel)
    }

    export function runSimulationWithNoise(
        circuitId: string,
        shots: number,
        noiseModel: number[]
    ): string {
        return runWithNoise(circuitId, shots, copyNumberArray(noiseModel))
    }

    export function getStatevectorReal(circuitId: string): number[] {
        clearError()
        const circuit = getCircuit(circuitId)

        if (!circuit) {
            return []
        }

        const state = buildState(circuit)
        return state ? copyNumberArray(state.real) : []
    }

    export function getStatevectorImaginary(circuitId: string): number[] {
        clearError()
        const circuit = getCircuit(circuitId)

        if (!circuit) {
            return []
        }

        const state = buildState(circuit)
        return state ? copyNumberArray(state.imaginary) : []
    }

    export function getProbabilityLabels(circuitId: string): string[] {
        clearError()
        const circuit = getCircuit(circuitId)

        if (!circuit) {
            return []
        }

        let labels: string[] = []

        for (let i = 0; i < powerOfTwo(circuit.numQubits); i++) {
            labels.push(basisLabel(i, circuit.numQubits))
        }

        return labels
    }

    export function getProbabilities(circuitId: string): number[] {
        clearError()
        const circuit = getCircuit(circuitId)

        if (!circuit) {
            return []
        }

        const state = buildState(circuit)
        return state ? probabilitiesFromState(state) : []
    }

    export function getProbabilitiesWithNoise(
        circuitId: string,
        noiseModel: number[]
    ): number[] {
        clearError()
        const circuit = getCircuit(circuitId)

        if (!circuit) {
            return []
        }

        const state = buildState(circuit)

        if (!state) {
            return []
        }

        const probabilities = probabilitiesFromState(state)

        if (!applyMeasurementNoise(
            probabilities,
            circuit.numQubits,
            copyNumberArray(noiseModel)
        )) {
            return []
        }

        return probabilities
    }

    export function getJobMemory(jobId: string): string[] {
        clearError()
        const job = getJob(jobId)
        return job && waitForIBMResult(job, IBM_RESULT_TIMEOUT_TENTHS)
            ? copyStringArray(job.memory) : []
    }

    export function getJobCountLabels(jobId: string): string[] {
        clearError()
        const job = getJob(jobId)
        return job && waitForIBMResult(job, IBM_RESULT_TIMEOUT_TENTHS)
            ? copyStringArray(job.countLabels) : []
    }

    export function getJobCounts(jobId: string): number[] {
        clearError()
        const job = getJob(jobId)
        return job && waitForIBMResult(job, IBM_RESULT_TIMEOUT_TENTHS)
            ? copyNumberArray(job.counts) : []
    }

    export function getCount(jobId: string, outcome: string): number {
        clearError()
        const job = getJob(jobId)

        if (!job || !waitForIBMResult(job, IBM_RESULT_TIMEOUT_TENTHS)) {
            return 0
        }

        return countForOutcome(job, outcome)
    }

    export function getPercentage(jobId: string, outcome: string): number {
        clearError()
        const job = getJob(jobId)

        if (
            !job ||
            !waitForIBMResult(job, IBM_RESULT_TIMEOUT_TENTHS) ||
            job.shots == 0
        ) {
            return 0
        }

        return 100 * countForOutcome(job, outcome) / job.shots
    }

    export function getMostFrequentResult(jobId: string): string {
        clearError()
        const job = getJob(jobId)

        if (
            !job ||
            !waitForIBMResult(job, IBM_RESULT_TIMEOUT_TENTHS) ||
            job.counts.length == 0
        ) {
            return ""
        }

        let bestIndex = 0

        for (let i = 1; i < job.counts.length; i++) {
            if (job.counts[i] > job.counts[bestIndex]) {
                bestIndex = i
            }
        }

        return job.countLabels[bestIndex]
    }

    export function getJobShots(jobId: string): number {
        clearError()
        const job = getJob(jobId)
        return job ? job.shots : 0
    }

    export function getJobStatus(jobId: string): string {
        clearError()
        const job = getJob(jobId)

        if (!job) {
            return ""
        }

        if (job.source == "ibm") {
            const previousStatusResponseCounter = job.statusResponseCounter
            sendIBMLine("IBMQ_GET_STATUS|" + job.id)

            if (!waitForIBMStatusReply(job, previousStatusResponseCounter)) {
                return "timeout"
            }
        }

        return job.status
    }

    export function isJobFinished(jobId: string): boolean {
        clearError()
        const job = getJob(jobId)
        return job ? job.status == "done" || job.status == "failed" : false
    }

    export function getJobError(jobId: string): string {
        clearError()
        const job = getJob(jobId)
        return job ? job.error : ""
    }

    export function getJobProbabilityLabels(jobId: string): string[] {
        clearError()
        const job = getJob(jobId)
        return job ? copyStringArray(job.probabilityLabels) : []
    }

    export function getJobProbabilities(jobId: string): number[] {
        clearError()
        const job = getJob(jobId)
        return job ? copyNumberArray(job.probabilities) : []
    }

    export function getJobStatevectorReal(jobId: string): number[] {
        clearError()
        const job = getJob(jobId)
        return job ? copyNumberArray(job.stateReal) : []
    }

    export function getJobStatevectorImaginary(jobId: string): number[] {
        clearError()
        const job = getJob(jobId)
        return job ? copyNumberArray(job.stateImaginary) : []
    }

    export function getJobResult(jobId: string): number[] {
        clearError()
        const job = getJob(jobId)

        if (
            !job ||
            !waitForIBMResult(job, IBM_RESULT_TIMEOUT_TENTHS) ||
            job.memory.length == 0
        ) {
            return []
        }

        const bitString = job.memory[0]
        let result: number[] = []

        // Preserve the original block's list order: classical bit 0 first.
        for (let bit = 0; bit < bitString.length; bit++) {
            const character = bitString.charAt(bitString.length - 1 - bit)
            result.push(character == "1" ? 1 : 0)
        }

        return result
    }

    export function getLastError(): string {
        return lastError
    }
}
