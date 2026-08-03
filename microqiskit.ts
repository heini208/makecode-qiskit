namespace microQiskitRuntime {
    class Measurement {
        qubit: number
        classicalBit: number

        constructor(qubit: number, classicalBit: number) {
            this.qubit = qubit
            this.classicalBit = classicalBit
        }
    }

    class Circuit {
        id: string
        numQubits: number
        numClbits: number
        hApplied: boolean[]
        measurements: Measurement[]

        constructor(id: string, numQubits: number, numClbits: number) {
            this.id = id
            this.numQubits = numQubits
            this.numClbits = numClbits
            this.hApplied = []
            this.measurements = []

            for (let i = 0; i < numQubits; i++) {
                this.hApplied.push(false)
            }
        }
    }

    class Job {
        id: string
        result: number[]

        constructor(id: string, result: number[]) {
            this.id = id
            this.result = result
        }
    }

    let circuits: Circuit[] = []
    let jobs: Job[] = []
    let nextCircuitId = 1
    let nextJobId = 1

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

    function copyNumberArray(values: number[]): number[] {
        let copy: number[] = []

        for (let i = 0; i < values.length; i++) {
            copy.push(values[i])
        }

        return copy
    }

    export function createCircuit(
        numQubits: number,
        numClbits: number
    ): string {
        if (numQubits < 1 || numClbits < 1) {
            return ""
        }

        const circuitId = "circuit" + nextCircuitId
        nextCircuitId += 1

        circuits.push(new Circuit(circuitId, numQubits, numClbits))

        return circuitId
    }

    export function applyH(
        circuitId: string,
        qubit: number
    ): void {
        const circuitIndex = findCircuitIndex(circuitId)

        if (circuitIndex < 0) {
            return
        }

        const circuit = circuits[circuitIndex]

        if (qubit < 0 || qubit >= circuit.numQubits) {
            return
        }

        circuit.hApplied[qubit] = !circuit.hApplied[qubit]
    }

    export function measureQubit(
        circuitId: string,
        qubit: number,
        classicalBit: number
    ): void {
        const circuitIndex = findCircuitIndex(circuitId)

        if (circuitIndex < 0) {
            return
        }

        const circuit = circuits[circuitIndex]

        if (qubit < 0 || qubit >= circuit.numQubits) {
            return
        }

        if (classicalBit < 0 || classicalBit >= circuit.numClbits) {
            return
        }

        circuit.measurements.push(
            new Measurement(qubit, classicalBit)
        )
    }

    export function runSimulation(circuitId: string): string {
        const circuitIndex = findCircuitIndex(circuitId)

        if (circuitIndex < 0) {
            return ""
        }

        const circuit = circuits[circuitIndex]
        let result: number[] = []
        let measuredQubits: number[] = []

        for (let i = 0; i < circuit.numClbits; i++) {
            result.push(0)
        }

        for (let i = 0; i < circuit.numQubits; i++) {
            measuredQubits.push(-1)
        }

        for (let i = 0; i < circuit.measurements.length; i++) {
            const measurement = circuit.measurements[i]
            const qubit = measurement.qubit
            const classicalBit = measurement.classicalBit

            if (measuredQubits[qubit] < 0) {
                if (circuit.hApplied[qubit]) {
                    measuredQubits[qubit] = randint(0, 1)
                } else {
                    measuredQubits[qubit] = 0
                }
            }

            result[classicalBit] = measuredQubits[qubit]
        }

        const jobId = "job" + nextJobId
        nextJobId += 1

        jobs.push(new Job(jobId, result))

        return jobId
    }

    export function getJobResult(jobId: string): number[] {
        const jobIndex = findJobIndex(jobId)

        if (jobIndex < 0) {
            return []
        }

        return copyNumberArray(jobs[jobIndex].result)
    }
}