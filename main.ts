//% color="#6f42c1" weight=80 icon="\uf0c3" block="MicroQiskit"
//% groups='["Circuits", "Gates", "Measurement", "Simulation", "Results"]'
namespace microQiskit {
    /**
     * Creates a quantum circuit.
     */
    //% blockId=microqiskit_create_circuit
    //% block="create circuit with $numQubits qubits and $numClbits classical bits"
    //% group="Circuits"
    //% weight=100
    //% blockSetVariable=circuit
    //% numQubits.min=1
    //% numQubits.max=8
    //% numQubits.defl=1
    //% numClbits.min=1
    //% numClbits.max=8
    //% numClbits.defl=1
    export function createCircuit(
        numQubits: number = 1,
        numClbits: number = 1
    ): string {
        return microQiskitRuntime.createCircuit(
            numQubits,
            numClbits
        )
    }

    /**
     * Applies a Hadamard gate.
     */
    //% blockId=microqiskit_apply_h
    //% block="apply H to circuit $circuitId on qubit $qubit"
    //% group="Gates"
    //% weight=100
    //% circuitId.shadow=variables_get
    //% circuitId.defl=circuit
    //% qubit.min=0
    //% qubit.max=7
    //% qubit.defl=0
    export function applyH(
        circuitId: string,
        qubit: number = 0
    ): void {
        microQiskitRuntime.applyH(circuitId, qubit)
    }

    /**
     * Measures one qubit into a classical bit.
     */
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
        microQiskitRuntime.measureQubit(
            circuitId,
            qubit,
            classicalBit
        )
    }

    /**
     * Runs one local simulation shot.
     */
    //% blockId=microqiskit_run_simulation
    //% block="run circuit $circuitId locally"
    //% group="Simulation"
    //% weight=100
    //% blockSetVariable=job
    //% circuitId.shadow=variables_get
    //% circuitId.defl=circuit
    export function runSimulation(
        circuitId: string
    ): string {
        return microQiskitRuntime.runSimulation(circuitId)
    }

    /**
     * Returns the job result as a list of classical bits.
     */
    //% blockId=microqiskit_job_result
    //% block="bit list result from job $jobId"
    //% group="Results"
    //% weight=100
    //% jobId.shadow=variables_get
    //% jobId.defl=job
    export function getJobResult(
        jobId: string
    ): number[] {
        return microQiskitRuntime.getJobResult(jobId)
    }
}