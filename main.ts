//% color="#6f42c1" weight=80 icon="\uf0c3" block="MicroQiskit"
//% subcategories='["Qiskit basic", "Qiskit advanced"]'
//% groups='["Circuits", "Gates", "Measurement", "Simulation", "Results", "Statevector", "Initialization", "Diagnostics"]'
namespace microQiskit {
    /** Basic single-qubit gates. */
    export enum BasicGate {
        H,
        X,
        Y,
        Z
    }

    /** Single-qubit rotation gates. */
    export enum RotationGate {
        RX,
        RY,
        RZ
    }

    /** Creates a MicroQiskit quantum circuit. */
    //% blockId=microqiskit_create_circuit
    //% block="create circuit with $numQubits qubits and $numClbits classical bits"
    //% subcategory="Qiskit basic" group="Circuits" weight=100 blockSetVariable=circuit
    //% numQubits.min=1 numQubits.max=8 numQubits.defl=1
    //% numClbits.min=0 numClbits.max=8 numClbits.defl=1
    export function createCircuit(
        numQubits: number = 1,
        numClbits: number = 1
    ): string {
        return microQiskitRuntime.createCircuit(numQubits, numClbits)
    }

    /** Combines the operations from two circuits, as with MicroQiskit circuit addition. */
    //% blockId=microqiskit_combine_circuits
    //% block="combine circuit $firstCircuitId then $secondCircuitId"
    //% subcategory="Qiskit advanced" group="Circuits" weight=100 blockSetVariable=circuit
    //% firstCircuitId.shadow=variables_get firstCircuitId.defl=firstCircuit
    //% secondCircuitId.shadow=variables_get secondCircuitId.defl=secondCircuit
    export function combineCircuits(
        firstCircuitId: string,
        secondCircuitId: string
    ): string {
        return microQiskitRuntime.combineCircuits(firstCircuitId, secondCircuitId)
    }

    /** Gives a circuit a name. */
    //% blockId=microqiskit_set_circuit_name
    //% block="set name of circuit $circuitId to $name"
    //% subcategory="Qiskit advanced" group="Circuits" weight=95
    //% circuitId.shadow=variables_get circuitId.defl=circuit
    export function setCircuitName(circuitId: string, name: string): void {
        microQiskitRuntime.setCircuitName(circuitId, name)
    }

    /** Returns the circuit name. */
    //% blockId=microqiskit_get_circuit_name
    //% block="name of circuit $circuitId"
    //% subcategory="Qiskit advanced" group="Circuits" weight=90
    //% circuitId.shadow=variables_get circuitId.defl=circuit
    export function getCircuitName(circuitId: string): string {
        return microQiskitRuntime.getCircuitName(circuitId)
    }

    /** Returns the number of qubits in a circuit. */
    //% blockId=microqiskit_circuit_qubit_count
    //% block="number of qubits in circuit $circuitId"
    //% subcategory="Qiskit advanced" group="Circuits" weight=85
    //% circuitId.shadow=variables_get circuitId.defl=circuit
    export function getCircuitQubitCount(circuitId: string): number {
        return microQiskitRuntime.getCircuitQubitCount(circuitId)
    }

    /** Returns the number of classical bits in a circuit. */
    //% blockId=microqiskit_circuit_classical_bit_count
    //% block="number of classical bits in circuit $circuitId"
    //% subcategory="Qiskit advanced" group="Circuits" weight=80
    //% circuitId.shadow=variables_get circuitId.defl=circuit
    export function getCircuitClassicalBitCount(circuitId: string): number {
        return microQiskitRuntime.getCircuitClassicalBitCount(circuitId)
    }

    /** Applies a basic single-qubit gate selected from the dropdown. */
    //% blockId=microqiskit_apply_basic_gate
    //% block="apply $gate to circuit $circuitId on qubit $qubit"
    //% subcategory="Qiskit basic" group="Gates" weight=100
    //% circuitId.shadow=variables_get circuitId.defl=circuit
    //% qubit.min=0 qubit.max=7 qubit.defl=0
    export function applyBasicGate(
        circuitId: string,
        gate: BasicGate = BasicGate.H,
        qubit: number = 0
    ): void {
        if (gate == BasicGate.H) {
            microQiskitRuntime.applyH(circuitId, qubit)
        } else if (gate == BasicGate.X) {
            microQiskitRuntime.applyX(circuitId, qubit)
        } else if (gate == BasicGate.Y) {
            microQiskitRuntime.applyY(circuitId, qubit)
        } else {
            microQiskitRuntime.applyZ(circuitId, qubit)
        }
    }

    /** Applies a rotation gate selected from the dropdown. The angle is in radians. */
    //% blockId=microqiskit_apply_rotation_gate
    //% block="apply $gate angle $theta to circuit $circuitId on qubit $qubit"
    //% subcategory="Qiskit advanced" group="Gates" weight=100 inlineInputMode=external
    //% circuitId.shadow=variables_get circuitId.defl=circuit
    //% theta.defl=1.57079632679
    //% qubit.min=0 qubit.max=7 qubit.defl=0
    export function applyRotationGate(
        circuitId: string,
        gate: RotationGate = RotationGate.RX,
        theta: number = 1.57079632679,
        qubit: number = 0
    ): void {
        if (gate == RotationGate.RX) {
            microQiskitRuntime.applyRX(circuitId, theta, qubit)
        } else if (gate == RotationGate.RY) {
            microQiskitRuntime.applyRY(circuitId, theta, qubit)
        } else {
            microQiskitRuntime.applyRZ(circuitId, theta, qubit)
        }
    }

    /** Applies a Pauli X gate. */
    //% blockId=microqiskit_apply_x
    //% block="apply X to circuit $circuitId on qubit $qubit"
    //% subcategory="Qiskit basic" group="Gates" weight=100 blockHidden=true
    //% circuitId.shadow=variables_get circuitId.defl=circuit
    //% qubit.min=0 qubit.max=7 qubit.defl=0
    export function applyX(circuitId: string, qubit: number = 0): void {
        microQiskitRuntime.applyX(circuitId, qubit)
    }

    /** Applies a Pauli Y gate. */
    //% blockId=microqiskit_apply_y
    //% block="apply Y to circuit $circuitId on qubit $qubit"
    //% subcategory="Qiskit basic" group="Gates" weight=95 blockHidden=true
    //% circuitId.shadow=variables_get circuitId.defl=circuit
    //% qubit.min=0 qubit.max=7 qubit.defl=0
    export function applyY(circuitId: string, qubit: number = 0): void {
        microQiskitRuntime.applyY(circuitId, qubit)
    }

    /** Applies a Pauli Z gate. */
    //% blockId=microqiskit_apply_z
    //% block="apply Z to circuit $circuitId on qubit $qubit"
    //% subcategory="Qiskit basic" group="Gates" weight=90 blockHidden=true
    //% circuitId.shadow=variables_get circuitId.defl=circuit
    //% qubit.min=0 qubit.max=7 qubit.defl=0
    export function applyZ(circuitId: string, qubit: number = 0): void {
        microQiskitRuntime.applyZ(circuitId, qubit)
    }

    /** Applies a Hadamard gate. */
    //% blockId=microqiskit_apply_h
    //% block="apply H to circuit $circuitId on qubit $qubit"
    //% subcategory="Qiskit basic" group="Gates" weight=85 blockHidden=true
    //% circuitId.shadow=variables_get circuitId.defl=circuit
    //% qubit.min=0 qubit.max=7 qubit.defl=0
    export function applyH(circuitId: string, qubit: number = 0): void {
        microQiskitRuntime.applyH(circuitId, qubit)
    }

    /** Applies an X-axis rotation. The angle is in radians. */
    //% blockId=microqiskit_apply_rx
    //% block="apply RX angle $theta to circuit $circuitId on qubit $qubit"
    //% subcategory="Qiskit advanced" group="Gates" weight=80 inlineInputMode=external blockHidden=true
    //% circuitId.shadow=variables_get circuitId.defl=circuit
    //% theta.defl=1.57079632679
    //% qubit.min=0 qubit.max=7 qubit.defl=0
    export function applyRX(
        circuitId: string,
        theta: number,
        qubit: number = 0
    ): void {
        microQiskitRuntime.applyRX(circuitId, theta, qubit)
    }

    /** Applies a Y-axis rotation. The angle is in radians. */
    //% blockId=microqiskit_apply_ry
    //% block="apply RY angle $theta to circuit $circuitId on qubit $qubit"
    //% subcategory="Qiskit advanced" group="Gates" weight=75 inlineInputMode=external blockHidden=true
    //% circuitId.shadow=variables_get circuitId.defl=circuit
    //% theta.defl=1.57079632679
    //% qubit.min=0 qubit.max=7 qubit.defl=0
    export function applyRY(
        circuitId: string,
        theta: number,
        qubit: number = 0
    ): void {
        microQiskitRuntime.applyRY(circuitId, theta, qubit)
    }

    /** Applies a Z-axis rotation. The angle is in radians. */
    //% blockId=microqiskit_apply_rz
    //% block="apply RZ angle $theta to circuit $circuitId on qubit $qubit"
    //% subcategory="Qiskit advanced" group="Gates" weight=70 inlineInputMode=external blockHidden=true
    //% circuitId.shadow=variables_get circuitId.defl=circuit
    //% theta.defl=1.57079632679
    //% qubit.min=0 qubit.max=7 qubit.defl=0
    export function applyRZ(
        circuitId: string,
        theta: number,
        qubit: number = 0
    ): void {
        microQiskitRuntime.applyRZ(circuitId, theta, qubit)
    }

    /** Applies a controlled X gate. */
    //% blockId=microqiskit_apply_cx
    //% block="apply CX to circuit $circuitId control $control target $target"
    //% subcategory="Qiskit basic" group="Gates" weight=90 inlineInputMode=external
    //% circuitId.shadow=variables_get circuitId.defl=circuit
    //% control.min=0 control.max=7 control.defl=0
    //% target.min=0 target.max=7 target.defl=1
    export function applyCX(
        circuitId: string,
        control: number = 0,
        target: number = 1
    ): void {
        microQiskitRuntime.applyCX(circuitId, control, target)
    }

    /** Applies a controlled X-axis rotation. The angle is in radians. */
    //% blockId=microqiskit_apply_crx
    //% block="apply CRX angle $theta to circuit $circuitId control $control target $target"
    //% subcategory="Qiskit advanced" group="Gates" weight=90 inlineInputMode=external
    //% circuitId.shadow=variables_get circuitId.defl=circuit
    //% theta.defl=1.57079632679
    //% control.min=0 control.max=7 control.defl=0
    //% target.min=0 target.max=7 target.defl=1
    export function applyCRX(
        circuitId: string,
        theta: number,
        control: number = 0,
        target: number = 1
    ): void {
        microQiskitRuntime.applyCRX(circuitId, theta, control, target)
    }

    /** Measures one qubit into one classical bit. */
    //% blockId=microqiskit_measure_qubit
    //% block="measure circuit $circuitId qubit $qubit into classical bit $classicalBit"
    //% subcategory="Qiskit advanced" group="Measurement" weight=100 inlineInputMode=external
    //% circuitId.shadow=variables_get circuitId.defl=circuit
    //% qubit.min=0 qubit.max=7 qubit.defl=0
    //% classicalBit.min=0 classicalBit.max=7 classicalBit.defl=0
    export function measureQubit(
        circuitId: string,
        qubit: number = 0,
        classicalBit: number = 0
    ): void {
        microQiskitRuntime.measureQubit(circuitId, qubit, classicalBit)
    }

    /** Measures qubit i into classical bit i for the whole circuit. */
    //% blockId=microqiskit_measure_all
    //% block="measure all qubits in circuit $circuitId"
    //% subcategory="Qiskit basic" group="Measurement" weight=100
    //% circuitId.shadow=variables_get circuitId.defl=circuit
    export function measureAll(circuitId: string): void {
        microQiskitRuntime.measureAll(circuitId)
    }

    /** Runs a local MicroQiskit simulation. */
    //% blockId=microqiskit_run_simulation
    //% block="run circuit $circuitId locally with $shots shots"
    //% subcategory="Qiskit basic" group="Simulation" weight=100 blockSetVariable=job
    //% circuitId.shadow=variables_get circuitId.defl=circuit
    //% shots.min=1 shots.max=2048 shots.defl=1024
    export function runSimulation(
        circuitId: string,
        shots: number = 1024
    ): string {
        return microQiskitRuntime.runSimulation(circuitId, shots)
    }

    /** Runs a circuit on real IBM Quantum hardware through the connected PC app. */
    //% blockId=microqiskit_run_ibm_quantum
    //% block="run circuit $circuitId on IBM Quantum with $shots shots"
    //% subcategory="Qiskit basic" group="Simulation" weight=90 blockSetVariable=job
    //% circuitId.shadow=variables_get circuitId.defl=circuit
    //% shots.min=1 shots.max=2048 shots.defl=1024
    export function runOnIBMQuantum(
        circuitId: string,
        shots: number = 1024
    ): string {
        return microQiskitRuntime.runOnIBMQuantum(circuitId, shots)
    }

    /** Runs with the same final measurement-error probability on every qubit. */
    //% blockId=microqiskit_run_uniform_noise
    //% block="run circuit $circuitId with $shots shots and measurement error $errorProbability"
    //% subcategory="Qiskit advanced" group="Simulation" weight=100 blockSetVariable=job inlineInputMode=external
    //% circuitId.shadow=variables_get circuitId.defl=circuit
    //% shots.min=1 shots.max=2048 shots.defl=1024
    //% errorProbability.min=0 errorProbability.max=1 errorProbability.defl=0.05
    export function runSimulationWithUniformNoise(
        circuitId: string,
        shots: number = 1024,
        errorProbability: number = 0.05
    ): string {
        return microQiskitRuntime.runSimulationWithUniformNoise(
            circuitId,
            shots,
            errorProbability
        )
    }

    /** Runs with one final measurement-error probability per qubit. */
    //% blockId=microqiskit_run_noise_list
    //% block="run circuit $circuitId with $shots shots and measurement error list $noiseModel"
    //% subcategory="Qiskit advanced" group="Simulation" weight=90 blockSetVariable=job inlineInputMode=external
    //% circuitId.shadow=variables_get circuitId.defl=circuit
    //% shots.min=1 shots.max=2048 shots.defl=1024
    export function runSimulationWithNoise(
        circuitId: string,
        shots: number,
        noiseModel: number[]
    ): string {
        return microQiskitRuntime.runSimulationWithNoise(circuitId, shots, noiseModel)
    }

    /** Returns every measured bit string, one per shot. */
    //% blockId=microqiskit_job_memory
    //% block="shot memory from job $jobId"
    //% subcategory="Qiskit advanced" group="Results" weight=100
    //% jobId.shadow=variables_get jobId.defl=job
    export function getJobMemory(jobId: string): string[] {
        return microQiskitRuntime.getJobMemory(jobId)
    }

    /** Returns the measured bit-string labels corresponding to the counts list. */
    //% blockId=microqiskit_job_count_labels
    //% block="outcome labels from job $jobId"
    //% subcategory="Qiskit advanced" group="Results" weight=95
    //% jobId.shadow=variables_get jobId.defl=job
    export function getJobCountLabels(jobId: string): string[] {
        return microQiskitRuntime.getJobCountLabels(jobId)
    }

    /** Returns counts corresponding to the outcome-label list. */
    //% blockId=microqiskit_job_counts
    //% block="outcome counts from job $jobId"
    //% subcategory="Qiskit advanced" group="Results" weight=90
    //% jobId.shadow=variables_get jobId.defl=job
    export function getJobCounts(jobId: string): number[] {
        return microQiskitRuntime.getJobCounts(jobId)
    }

    /** Returns how often a particular bit string was measured. */
    //% blockId=microqiskit_get_count
    //% block="count of outcome $outcome in job $jobId"
    //% subcategory="Qiskit basic" group="Results" weight=80
    //% jobId.shadow=variables_get jobId.defl=job
    //% outcome.defl="0"
    export function getCount(jobId: string, outcome: string): number {
        return microQiskitRuntime.getCount(jobId, outcome)
    }

    /** Returns the percentage of shots with a particular bit string. */
    //% blockId=microqiskit_get_percentage
    //% block="percentage of outcome $outcome in job $jobId"
    //% subcategory="Qiskit basic" group="Results" weight=70
    //% jobId.shadow=variables_get jobId.defl=job
    //% outcome.defl="0"
    export function getPercentage(jobId: string, outcome: string): number {
        return microQiskitRuntime.getPercentage(jobId, outcome)
    }

    /** Returns the bit string with the largest count. */
    //% blockId=microqiskit_most_frequent
    //% block="most frequent outcome from job $jobId"
    //% subcategory="Qiskit basic" group="Results" weight=90
    //% jobId.shadow=variables_get jobId.defl=job
    export function getMostFrequentResult(jobId: string): string {
        return microQiskitRuntime.getMostFrequentResult(jobId)
    }

    /** Returns the number of shots used by a job. */
    //% blockId=microqiskit_job_shots
    //% block="number of shots in job $jobId"
    //% subcategory="Qiskit advanced" group="Results" weight=85
    //% jobId.shadow=variables_get jobId.defl=job
    export function getJobShots(jobId: string): number {
        return microQiskitRuntime.getJobShots(jobId)
    }

    /** Returns the status for either a local or an IBM job. */
    //% blockId=microqiskit_job_status
    //% block="status of job $jobId"
    //% subcategory="Qiskit basic" group="Results" weight=98
    //% jobId.shadow=variables_get jobId.defl=job
    export function getJobStatus(jobId: string): string {
        return microQiskitRuntime.getJobStatus(jobId)
    }

    /** Reports whether either a local or an IBM job has finished. */
    //% blockId=microqiskit_job_finished
    //% block="job $jobId is finished"
    //% subcategory="Qiskit basic" group="Results" weight=97
    //% jobId.shadow=variables_get jobId.defl=job
    export function isJobFinished(jobId: string): boolean {
        return microQiskitRuntime.isJobFinished(jobId)
    }

    /** Returns an error from a failed job, or an empty string. */
    //% blockId=microqiskit_job_error
    //% block="error from job $jobId"
    //% subcategory="Qiskit basic" group="Results" weight=60
    //% jobId.shadow=variables_get jobId.defl=job
    export function getJobError(jobId: string): string {
        return microQiskitRuntime.getJobError(jobId)
    }

    /** Returns one shot as a list with classical bit 0 first. */
    //% blockId=microqiskit_job_result
    //% block="bit list result from job $jobId"
    //% subcategory="Qiskit basic" group="Results" weight=100
    //% jobId.shadow=variables_get jobId.defl=job
    export function getJobResult(jobId: string): number[] {
        return microQiskitRuntime.getJobResult(jobId)
    }

    /** Returns basis-state labels for circuit probabilities. */
    //% blockId=microqiskit_probability_labels
    //% block="basis labels for circuit $circuitId"
    //% subcategory="Qiskit advanced" group="Statevector" weight=100
    //% circuitId.shadow=variables_get circuitId.defl=circuit
    export function getProbabilityLabels(circuitId: string): string[] {
        return microQiskitRuntime.getProbabilityLabels(circuitId)
    }

    /** Returns the exact probability of every basis state. */
    //% blockId=microqiskit_probabilities
    //% block="basis probabilities for circuit $circuitId"
    //% subcategory="Qiskit advanced" group="Statevector" weight=95
    //% circuitId.shadow=variables_get circuitId.defl=circuit
    export function getProbabilities(circuitId: string): number[] {
        return microQiskitRuntime.getProbabilities(circuitId)
    }

    /** Returns exact basis probabilities after final measurement noise. */
    //% blockId=microqiskit_probabilities_with_noise
    //% block="basis probabilities for circuit $circuitId with measurement error list $noiseModel"
    //% subcategory="Qiskit advanced" group="Statevector" weight=90 inlineInputMode=external
    //% circuitId.shadow=variables_get circuitId.defl=circuit
    export function getProbabilitiesWithNoise(
        circuitId: string,
        noiseModel: number[]
    ): number[] {
        return microQiskitRuntime.getProbabilitiesWithNoise(
            circuitId,
            noiseModel
        )
    }

    /** Returns the real part of every state-vector amplitude. */
    //% blockId=microqiskit_statevector_real
    //% block="real statevector for circuit $circuitId"
    //% subcategory="Qiskit advanced" group="Statevector" weight=85
    //% circuitId.shadow=variables_get circuitId.defl=circuit
    export function getStatevectorReal(circuitId: string): number[] {
        return microQiskitRuntime.getStatevectorReal(circuitId)
    }

    /** Returns the imaginary part of every state-vector amplitude. */
    //% blockId=microqiskit_statevector_imaginary
    //% block="imaginary statevector for circuit $circuitId"
    //% subcategory="Qiskit advanced" group="Statevector" weight=80
    //% circuitId.shadow=variables_get circuitId.defl=circuit
    export function getStatevectorImaginary(circuitId: string): number[] {
        return microQiskitRuntime.getStatevectorImaginary(circuitId)
    }

    /** Returns probabilities used for a completed job, including its noise model. */
    //% blockId=microqiskit_job_probabilities
    //% block="basis probabilities from job $jobId"
    //% subcategory="Qiskit advanced" group="Statevector" weight=75
    //% jobId.shadow=variables_get jobId.defl=job
    export function getJobProbabilities(jobId: string): number[] {
        return microQiskitRuntime.getJobProbabilities(jobId)
    }

    /** Returns basis labels corresponding to the job-probability list. */
    //% blockId=microqiskit_job_probability_labels
    //% block="basis labels from job $jobId"
    //% subcategory="Qiskit advanced" group="Statevector" weight=70
    //% jobId.shadow=variables_get jobId.defl=job
    export function getJobProbabilityLabels(jobId: string): string[] {
        return microQiskitRuntime.getJobProbabilityLabels(jobId)
    }

    /** Replaces a circuit with a real normalized initial state. */
    //% blockId=microqiskit_initialize_real
    //% block="initialize circuit $circuitId with real amplitudes $amplitudes"
    //% subcategory="Qiskit advanced" group="Initialization" weight=100 inlineInputMode=external
    //% circuitId.shadow=variables_get circuitId.defl=circuit
    export function initializeRealState(circuitId: string, amplitudes: number[]): void {
        microQiskitRuntime.initializeRealState(circuitId, amplitudes)
    }

    /** Replaces a circuit with a normalized complex initial state. */
    //% blockId=microqiskit_initialize_complex
    //% block="initialize circuit $circuitId with real $real and imaginary $imaginary amplitudes"
    //% subcategory="Qiskit advanced" group="Initialization" weight=90 inlineInputMode=external
    //% circuitId.shadow=variables_get circuitId.defl=circuit
    export function initializeState(
        circuitId: string,
        real: number[],
        imaginary: number[]
    ): void {
        microQiskitRuntime.initializeState(circuitId, real, imaginary)
    }

    /** Returns the real part of the state vector saved with a job. */
    //% blockId=microqiskit_job_statevector_real
    //% block="real statevector from job $jobId"
    //% subcategory="Qiskit advanced" group="Statevector" weight=65
    //% jobId.shadow=variables_get jobId.defl=job
    export function getJobStatevectorReal(jobId: string): number[] {
        return microQiskitRuntime.getJobStatevectorReal(jobId)
    }

    /** Returns the imaginary part of the state vector saved with a job. */
    //% blockId=microqiskit_job_statevector_imaginary
    //% block="imaginary statevector from job $jobId"
    //% subcategory="Qiskit advanced" group="Statevector" weight=60
    //% jobId.shadow=variables_get jobId.defl=job
    export function getJobStatevectorImaginary(jobId: string): number[] {
        return microQiskitRuntime.getJobStatevectorImaginary(jobId)
    }

    /** Returns the most recent MicroQiskit error, or an empty string. */
    //% blockId=microqiskit_last_error
    //% block="last MicroQiskit error"
    //% subcategory="Qiskit advanced" group="Diagnostics" weight=10
    export function getLastError(): string {
        return microQiskitRuntime.getLastError()
    }
}
