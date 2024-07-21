import qiskit
from qiskit import QuantumCircuit, transpile, qpy
from qiskit_aer import AerSimulator
import numpy as np
import json
import socket

def measure_qubits(circuit, num_qubits):
    bases = []
    qubits = []
    for i in range(num_qubits,num_qubits*2):
        basis = np.random.choice(['X', 'Z'])
        bases.append(basis)
        if basis == 'X':
            circuit.h(i)
        circuit.measure(i, int(i/2))
    simulator = AerSimulator()
    compiled_circuit = transpile(circuit, simulator)
    print(compiled_circuit)
    result = simulator.run(compiled_circuit).result()
    counts = result.get_counts(circuit)
    measured_qubits = list(counts.keys())[0]
    for bit in measured_qubits:
        qubits.append(int(bit))
    return qubits, bases

def intercept_and_measure(circuit, num_qubits):
    eve_qubits, eve_bases = measure_qubits(circuit, num_qubits)
    for i in range(num_qubits):
        circuit.clear()
        if eve_bases[i] == 'X':
            circuit.h(i)
        if eve_qubits[i] == 1:
            circuit.x(i)
    return eve_bases, eve_qubits

def main():
    num_qubits = 12
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', 44105))
        s.listen()
        conn, addr = s.accept()
        with conn:
            qpy_data = conn.recv(4096)
            with open('intercepted_entangled_pairs.qpy', 'wb') as f:
                f.write(qpy_data)

            with open('intercepted_entangled_pairs.qpy', 'rb') as f:
                circuit = qpy.load(f)[0]

            eve_bases, eve_qubits = intercept_and_measure(circuit, num_qubits)

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as bob_socket:
                bob_socket.connect(('BOB_IP', 44106))
                with open('intercepted_entangled_pairs.qpy', 'rb') as f:
                    qpy_data = f.read()
                bob_socket.sendall(qpy_data)
                print("Eve intercepted Bob's data:", eve_qubits)

if __name__ == "__main__":
    main()
