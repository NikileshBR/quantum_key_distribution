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

def sift_keys(alice_bases, bob_bases, bob_bits):
    sifted_keys = []
    for a_base, b_base, b_bit in zip(alice_bases, bob_bases, bob_bits):
        if a_base == b_base:
            sifted_keys.append(b_bit)
    return sifted_keys

def calculate_qber(alice_bits, bob_bits):
    errors = sum(a != b for a, b in zip(alice_bits, bob_bits))
    qber = errors / len(alice_bits)
    return qber

def main():
    num_qubits = 12
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as quantum_channel:
        quantum_channel.bind(('0.0.0.0', 44106))
        quantum_channel.listen()
        qconn, addr = quantum_channel.accept()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', 65535))
        s.listen()
        conn, addr1 = s.accept()
        with qconn:
            qpy_data = qconn.recv(4096)
            with open('received_entangled_pairs.qpy', 'wb') as f:
                f.write(qpy_data)

            with open('received_entangled_pairs.qpy', 'rb') as f:
                circuit = qpy.load(f)[0]

            bob_bits, bob_bases = measure_qubits(circuit, num_qubits)

    
        with conn:
            conn.sendall("REQUEST BASES".encode())
            data = conn.recv(4096)
            alice_bases = json.loads(data.decode())['bases']

            conn.sendall(json.dumps({"bases": bob_bases, "bits": bob_bits}).encode())

            data = conn.recv(4096)
            alice_bits = json.loads(data.decode())['bits']

            sifted_keys_bob = sift_keys(alice_bases, bob_bases, bob_bits)
            sifted_keys_alice = sift_keys(alice_bases, bob_bases, alice_bits)

            print("Bob's sifted keys:", sifted_keys_bob)
            print("Alice's sifted keys:", sifted_keys_alice)

            qber = calculate_qber(sifted_keys_alice, sifted_keys_bob)
            print(f"QBER: {qber * 100:.2f}%")

if __name__ == "__main__":
    main()
