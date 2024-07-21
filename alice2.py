import qiskit
from qiskit import QuantumCircuit, transpile, qpy
from qiskit_aer import AerSimulator
import numpy as np
import json
import socket
import time 

def create_entangled_pairs(num_qubits):
    circuit = QuantumCircuit(num_qubits*2, num_qubits)
    for i in range(num_qubits):
        bit=np.random.choice(['0','1'])
        if bit=='1':
            circuit.x(i)
        circuit.cx(i, i+num_qubits)
    return circuit

def measure_qubits(circuit, num_qubits):
    bases = []
    qubits = []
    for i in range(num_qubits):
        basis = np.random.choice([ 'X','Z'])
        bases.append(basis)
        if basis == 'X':
            circuit.h(i)
        circuit.measure(i, i)
    simulator = AerSimulator()
    compiled_circuit = transpile(circuit, simulator)
    print(compiled_circuit)
    result = simulator.run(compiled_circuit).result()
    counts = result.get_counts(circuit)
    measured_qubits = list(counts.keys())[0]
    for bit in measured_qubits:
        qubits.append(int(bit))
    return qubits, bases

def sift_keys(alice_bases, bob_bases, alice_bits):
    sifted_keys = []
    for a_basis, b_basis, a_bit in zip(alice_bases, bob_bases, alice_bits):
        if a_basis == b_basis:
            sifted_keys.append(a_bit)
    return sifted_keys

def main():
    num_qubits = 12
    circuit = create_entangled_pairs(num_qubits)
    alice_qubits, alice_bases = measure_qubits(circuit, num_qubits)

    with open('entangled_pairs.qpy', 'wb') as f:
        qpy.dump(circuit, f)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as quantum_channel:
        quantum_channel.connect(('EVE_IP', 44105))

        with open('entangled_pairs.qpy', 'rb') as f:
            qpy_data = f.read()
        quantum_channel.sendall(qpy_data)
    time.sleep(5)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('BOB_IP', 65535))
        data = s.recv(4096)
        if data.decode() == "REQUEST BASES":
            s.sendall(json.dumps({"bases": alice_bases}).encode())

        data = s.recv(4096)
        bob_data = json.loads(data.decode())
        sifted_keys = sift_keys(alice_bases, bob_data['bases'], alice_qubits)
        print("Alice's sifted keys:", sifted_keys)
        s.sendall(json.dumps({"bits": alice_qubits}).encode())
if __name__ == "__main__":
    main()
