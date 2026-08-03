let uartAcknowledged = false

function bitListToString(bits: number[]): string {
    let text = ""

    for (let i = 0; i < bits.length; i++) {
        if (i > 0) {
            text = text + ","
        }

        text = text + bits[i]
    }

    return text
}

serial.redirectToUSB()
serial.setRxBufferSize(128)
serial.setTxBufferSize(128)

serial.onDataReceived("\n", function () {
    const response = serial.readUntil("\n")

    if (response == "HELLO_ACK") {
        uartAcknowledged = true
        serial.writeLine("RECEIVED")
    }
})

const circuit = microQiskit.createCircuit(1, 1)

microQiskit.applyH(circuit, 0)
microQiskit.measureQubit(circuit, 0, 0)

const job = microQiskit.runSimulation(circuit)
const result = microQiskit.getJobResult(job)

serial.writeLine(
    "QISKIT_RESULT=" + bitListToString(result)
)

basic.forever(function () {
    if (!uartAcknowledged) {
        serial.writeLine("HELLO")
    }

    basic.pause(1000)
})