//% color="#6f42c1" weight=80 icon="\uf0c3" block="MicroQiskit"
//% groups='["Random", "Circuits", "Gates", "Measurement", "Simulation", "Results"]'
namespace microQiskit {
    export enum SingleGate {
        //% block="H"
        H,

        //% block="X"
        X,

        //% block="Y"
        Y,

        //% block="Z"
        Z
    }

    export enum RotationGate {
        //% block="RX"
        RX,

        //% block="RY"
        RY,

        //% block="RZ"
        RZ
    }

    export enum TwoQubitGate {
        //% block="CX"
        CX
    }

    let nextCircuitId = 1
    let nextJobId = 1

    function createCircuitId(): string {
        const id = "circuit" + nextCircuitId
        nextCircuitId += 1
        return id
    }

    function createJobId(): string {
        const id = "job" + nextJobId
        nextJobId += 1
        return id
    }

    //% blockId=microqiskit_start_random_job
    //% block="start random simulation with $qubits qubits"
    //% group="Random"
    //% weight=100
    //% blockSetVariable=job
    //% qubits.min=1
    //% qubits.max=8
    //% qubits.defl=2
    export function startRandomJob(qubits: number = 2): string {
        return createJobId()
    }

    //% blockId=microqiskit_create_circuit
    //% block="create circuit with $numQubits qubits and $numClbits classical bits"
    //% group="Circuits"
    //% weight=100
    //% blockSetVariable=circuit
    //% numQubits.min=1
    //% numQubits.max=8
    //% numQubits.defl=2
    //% numClbits.min=0
    //% numClbits.max=8
    //% numClbits.defl=2
    export function createCircuit(
        numQubits: number = 2,
        numClbits: number = 2
    ): string {
        return createCircuitId()
    }

    //% blockId=microqiskit_clone_circuit
    //% block="clone circuit $circuitId"
    //% group="Circuits"
    //% weight=90
    //% blockSetVariable=clonedCircuit
    //% circuitId.shadow=variables_get
    //% circuitId.defl=circuit
    export function cloneCircuit(circuitId: string): string {
        return createCircuitId()
    }

    //% blockId=microqiskit_reset_circuit
    //% block="reset circuit $circuitId"
    //% group="Circuits"
    //% weight=80
    //% circuitId.shadow=variables_get
    //% circuitId.defl=circuit
    export function resetCircuit(circuitId: string): void {
    }

    //% blockId=microqiskit_delete_circuit
    //% block="delete circuit $circuitId"
    //% group="Circuits"
    //% weight=70
    //% circuitId.shadow=variables_get
    //% circuitId.defl=circuit
    export function deleteCircuit(circuitId: string): void {
    }

    //% blockId=microqiskit_single_gate
    //% block="apply $gate gate to circuit $circuitId on qubit $qubit"
    //% group="Gates"
    //% weight=100
    //% circuitId.shadow=variables_get
    //% circuitId.defl=circuit
    //% qubit.min=0
    //% qubit.max=7
    //% qubit.defl=0
    export function applySingleGate(
        gate: SingleGate,
        circuitId: string,
        qubit: number = 0
    ): void {
    }

    //% blockId=microqiskit_rotation_gate
    //% block="apply $gate gate to circuit $circuitId on qubit $qubit with angle $angle"
    //% group="Gates"
    //% weight=90
    //% inlineInputMode=external
    //% circuitId.shadow=variables_get
    //% circuitId.defl=circuit
    //% qubit.min=0
    //% qubit.max=7
    //% qubit.defl=0
    //% angle.defl=3.14159
    export function applyRotationGate(
        gate: RotationGate,
        circuitId: string,
        qubit: number = 0,
        angle: number = 3.14159
    ): void {
    }

    //% blockId=microqiskit_two_qubit_gate
    //% block="apply $gate gate to circuit $circuitId control $control target $target"
    //% group="Gates"
    //% weight=80
    //% inlineInputMode=external
    //% circuitId.shadow=variables_get
    //% circuitId.defl=circuit
    //% control.min=0
    //% control.max=7
    //% control.defl=0
    //% target.min=0
    //% target.max=7
    //% target.defl=1
    export function applyTwoQubitGate(
        gate: TwoQubitGate,
        circuitId: string,
        control: number = 0,
        target: number = 1
    ): void {
    }

    //% blockId=microqiskit_measure_qubit
    //% block="measure circuit $circuitId qubit $qubit into classical bit $classicalBit"
    //% group="Measurement"
    //% weight=100
    //% inlineInputMode=external
    //% circuitId.shadow=variables_get
    //% circuitId.defl=circuit
    //% qubit.min=0
    //% qubit.max=7
    //% qubit.defl=0
    //% classicalBit.min=0
    //% classicalBit.max=7
    //% classicalBit.defl=0
    export function measureQubit(
        circuitId: string,
        qubit: number = 0,
        classicalBit: number = 0
    ): void {
    }

    //% blockId=microqiskit_measure_all
    //% block="measure all qubits in circuit $circuitId"
    //% group="Measurement"
    //% weight=90
    //% circuitId.shadow=variables_get
    //% circuitId.defl=circuit
    export function measureAll(circuitId: string): void {
    }

    //% blockId=microqiskit_run_simulation
    //% block="run circuit $circuitId locally"
    //% group="Simulation"
    //% weight=100
    //% blockSetVariable=job
    //% circuitId.shadow=variables_get
    //% circuitId.defl=circuit
    export function runSimulation(circuitId: string): string {
        return createJobId()
    }

    //% blockId=microqiskit_job_sample
    //% block="sample from job $jobId"
    //% group="Results"
    //% weight=100
    //% jobId.shadow=variables_get
    //% jobId.defl=job
    export function getJobSample(jobId: string): string {
        return "0"
    }

    //% blockId=microqiskit_job_states
    //% block="states from job $jobId"
    //% group="Results"
    //% weight=90
    //% jobId.shadow=variables_get
    //% jobId.defl=job
    export function getJobStates(jobId: string): string {
        return "[]"
    }

    //% blockId=microqiskit_job_counts
    //% block="counts from job $jobId"
    //% group="Results"
    //% weight=80
    //% jobId.shadow=variables_get
    //% jobId.defl=job
    export function getJobCounts(jobId: string): string {
        return "{}"
    }

    //% blockId=microqiskit_job_probabilities
    //% block="probabilities from job $jobId"
    //% group="Results"
    //% weight=70
    //% jobId.shadow=variables_get
    //% jobId.defl=job
    export function getJobProbabilities(jobId: string): string {
        return "{}"
    }

    //% blockId=microqiskit_job_status
    //% block="status of job $jobId"
    //% group="Results"
    //% weight=60
    //% jobId.shadow=variables_get
    //% jobId.defl=job
    export function getJobStatus(jobId: string): string {
        return "DONE"
    }
}