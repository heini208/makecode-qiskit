"""Graphical PC bridge between a Calliope mini and IBM Quantum."""

from __future__ import annotations

import queue
import threading
import time
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from typing import Any


IBM_CHANNEL = "ibm_quantum_platform"
SERIAL_BAUD_RATE = 115200
CALLIOPE_V3_USB_IDS = {(0x1366, 0x1025)}


@dataclass(frozen=True)
class ConnectionSettings:
    token: str
    instance: str
    region: str | None
    save_account: bool
    account_name: str


def hide_token(message: str, token: str) -> str:
    """Prevent an exception message from accidentally displaying the key."""
    return message.replace(token, "<hidden>") if token else message


def backend_name(backend: Any) -> str:
    """Read a backend name across supported Qiskit backend APIs."""
    name = getattr(backend, "name", str(backend))
    return str(name() if callable(name) else name)


def is_calliope_port(port: Any) -> bool:
    """Identify a Calliope from USB metadata, independently of user code."""
    usb_id = (getattr(port, "vid", None), getattr(port, "pid", None))
    if usb_id in CALLIOPE_V3_USB_IDS:
        return True

    metadata = " ".join(
        str(value or "")
        for value in (
            getattr(port, "description", ""),
            getattr(port, "product", ""),
            getattr(port, "manufacturer", ""),
            getattr(port, "interface", ""),
            getattr(port, "hwid", ""),
        )
    ).lower()
    return "calliope" in metadata


class QiskitBridgeApp(tk.Tk):
    """Small desktop interface for IBM and Calliope connections."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Calliope Qiskit Bridge")
        self.geometry("780x570")
        self.minsize(680, 500)

        self.events: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.ibm_service: Any | None = None
        self.serial_connection: Any | None = None
        self.serial_write_lock = threading.Lock()
        self.serial_stop = threading.Event()
        self.serial_thread: threading.Thread | None = None
        self.port_devices: dict[str, str] = {}
        self.serial_port_info: dict[str, Any] = {}
        self.incoming_circuits: dict[str, dict[str, Any]] = {}
        self.active_ibm_jobs: set[str] = set()
        self.ibm_job_statuses: dict[str, str] = {}
        self.ibm_job_results: dict[str, dict[str, Any]] = {}
        self.ibm_jobs_lock = threading.Lock()
        self.dashboard_visible = False
        self.closing = False

        self._configure_styles()
        self.protocol("WM_DELETE_WINDOW", self.close_app)
        self.show_login_screen()
        self.after(100, self.process_events)

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("Subtitle.TLabel", font=("Segoe UI", 10))
        style.configure("Section.TLabel", font=("Segoe UI", 11, "bold"))
        style.configure(
            "Connected.TLabel",
            foreground="#16803c",
            font=("Segoe UI", 11, "bold"),
        )
        style.configure(
            "Disconnected.TLabel",
            foreground="#b42318",
            font=("Segoe UI", 11, "bold"),
        )
        style.configure(
            "Checking.TLabel",
            foreground="#9a6700",
            font=("Segoe UI", 11, "bold"),
        )

    def clear_window(self) -> None:
        for child in self.winfo_children():
            child.destroy()

    def show_login_screen(self) -> None:
        self.dashboard_visible = False
        self.clear_window()

        outer = ttk.Frame(self, padding=28)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(1, weight=1)

        ttk.Label(
            outer,
            text="Connect to IBM Quantum",
            style="Title.TLabel",
        ).grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(
            outer,
            text=(
                "Enter your IBM Cloud API key. It is hidden while you type "
                "and is not saved by default."
            ),
            style="Subtitle.TLabel",
            wraplength=680,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 24))

        ttk.Label(outer, text="IBM Cloud API key").grid(
            row=2, column=0, sticky="w", padx=(0, 16), pady=7
        )
        self.token_entry = ttk.Entry(outer, show="*", width=52)
        self.token_entry.grid(row=2, column=1, sticky="ew", pady=7)
        self.token_entry.focus_set()

        ttk.Label(outer, text="Service instance").grid(
            row=3, column=0, sticky="w", padx=(0, 16), pady=7
        )
        self.instance_entry = ttk.Entry(outer)
        self.instance_entry.grid(row=3, column=1, sticky="ew", pady=7)
        self.instance_entry.insert(0, "")

        ttk.Label(
            outer,
            text="Leave empty to select the service instance automatically.",
            foreground="#666666",
        ).grid(row=4, column=1, sticky="w", pady=(0, 8))

        ttk.Label(outer, text="Region").grid(
            row=5, column=0, sticky="w", padx=(0, 16), pady=7
        )
        self.region_box = ttk.Combobox(
            outer,
            values=("Automatic", "us-east", "eu-de"),
            state="readonly",
        )
        self.region_box.current(0)
        self.region_box.grid(row=5, column=1, sticky="ew", pady=7)

        self.save_account_var = tk.BooleanVar(value=False)
        self.save_account_check = ttk.Checkbutton(
            outer,
            text="Save credentials on this computer",
            variable=self.save_account_var,
            command=self.toggle_account_name,
        )
        self.save_account_check.grid(
            row=6, column=0, columnspan=2, sticky="w", pady=(18, 4)
        )

        ttk.Label(
            outer,
            text=(
                "Saved Qiskit credentials are stored as plain text. "
                "Use this only on a trusted personal computer."
            ),
            foreground="#8a4b08",
            wraplength=680,
        ).grid(row=7, column=0, columnspan=2, sticky="w", pady=(0, 10))

        ttk.Label(outer, text="Saved account name").grid(
            row=8, column=0, sticky="w", padx=(0, 16), pady=7
        )
        self.account_name_entry = ttk.Entry(outer)
        self.account_name_entry.insert(0, "calliope")
        self.account_name_entry.configure(state="disabled")
        self.account_name_entry.grid(row=8, column=1, sticky="ew", pady=7)

        self.login_status = ttk.Label(outer, text="")
        self.login_status.grid(
            row=9, column=0, columnspan=2, sticky="w", pady=(18, 8)
        )

        self.connect_ibm_button = ttk.Button(
            outer,
            text="Connect to IBM Quantum",
            command=self.start_ibm_connection,
        )
        self.connect_ibm_button.grid(
            row=10, column=0, columnspan=2, sticky="ew", pady=(4, 0), ipady=5
        )
        self.bind("<Return>", lambda _event: self.start_ibm_connection())

    def toggle_account_name(self) -> None:
        state = "normal" if self.save_account_var.get() else "disabled"
        self.account_name_entry.configure(state=state)

    def read_login_settings(self) -> ConnectionSettings | None:
        token = self.token_entry.get().strip()
        if not token:
            messagebox.showwarning(
                "API key required",
                "Enter your IBM Cloud API key before connecting.",
                parent=self,
            )
            self.token_entry.focus_set()
            return None

        instance = self.instance_entry.get().strip() or "auto"
        region_text = self.region_box.get()
        region = None if region_text == "Automatic" or instance != "auto" else region_text
        account_name = self.account_name_entry.get().strip() or "calliope"

        return ConnectionSettings(
            token=token,
            instance=instance,
            region=region,
            save_account=self.save_account_var.get(),
            account_name=account_name,
        )

    def start_ibm_connection(self) -> None:
        if str(self.connect_ibm_button["state"]) == "disabled":
            return

        settings = self.read_login_settings()
        if settings is None:
            return

        self.connect_ibm_button.configure(state="disabled")
        self.login_status.configure(
            text="Connecting and checking the IBM account...",
            style="Checking.TLabel",
        )
        threading.Thread(
            target=self.ibm_connection_worker,
            args=(settings,),
            daemon=True,
        ).start()

    def ibm_connection_worker(self, settings: ConnectionSettings) -> None:
        try:
            from qiskit_ibm_runtime import QiskitRuntimeService
        except ImportError:
            self.events.put(
                (
                    "ibm_error",
                    "The Qiskit packages are missing. Install them with:\n"
                    "python -m pip install -r requirements.txt",
                )
            )
            return

        arguments: dict[str, Any] = {
            "channel": IBM_CHANNEL,
            "token": settings.token,
            "instance": settings.instance,
        }
        if settings.region is not None:
            arguments["region"] = settings.region

        try:
            service = QiskitRuntimeService(**arguments)
            instances = service.instances()

            backend_error = ""
            try:
                backend_names = sorted(
                    backend_name(backend) for backend in service.backends()
                )
            except Exception as exc:
                backend_names = []
                backend_error = hide_token(str(exc), settings.token)

            save_message = "Credentials were not saved."
            if settings.save_account:
                save_arguments = dict(arguments)
                save_arguments.update(
                    {
                        "name": settings.account_name,
                        "set_as_default": False,
                        "overwrite": False,
                    }
                )
                try:
                    QiskitRuntimeService.save_account(**save_arguments)
                    save_message = (
                        f"Credentials saved as account '{settings.account_name}'."
                    )
                except Exception as exc:
                    save_message = (
                        "IBM connected, but the credentials could not be saved: "
                        + hide_token(str(exc), settings.token)
                    )

            self.events.put(
                (
                    "ibm_connected",
                    {
                        "service": service,
                        "instance": settings.instance,
                        "region": settings.region,
                        "instance_count": len(instances),
                        "backend_names": backend_names,
                        "backend_error": backend_error,
                        "save_message": save_message,
                    },
                )
            )
        except Exception as exc:
            self.events.put(
                ("ibm_error", hide_token(str(exc), settings.token))
            )

    def show_dashboard(self, connection_info: dict[str, Any]) -> None:
        self.unbind("<Return>")
        self.dashboard_visible = True
        self.clear_window()

        outer = ttk.Frame(self, padding=22)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(4, weight=1)

        header = ttk.Frame(outer)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        ttk.Label(
            header,
            text="Calliope Qiskit Bridge",
            style="Title.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Button(header, text="Sign out", command=self.sign_out).grid(
            row=0, column=1, sticky="e"
        )

        statuses = ttk.LabelFrame(outer, text="Connections", padding=12)
        statuses.grid(row=1, column=0, sticky="ew", pady=(18, 10))
        statuses.columnconfigure((0, 2), weight=1)

        self.ibm_status_label = ttk.Label(
            statuses,
            text="● IBM Quantum: Connected",
            style="Connected.TLabel",
        )
        self.ibm_status_label.grid(row=0, column=0, sticky="w")
        self.ibm_check_button = ttk.Button(
            statuses,
            text="Check IBM",
            command=self.check_ibm_connection,
        )
        self.ibm_check_button.grid(row=0, column=1, padx=(10, 28))

        self.calliope_status_label = ttk.Label(
            statuses,
            text="● Calliope: Disconnected",
            style="Disconnected.TLabel",
        )
        self.calliope_status_label.grid(row=0, column=2, sticky="w")

        serial_frame = ttk.LabelFrame(outer, text="Calliope USB connection", padding=12)
        serial_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        serial_frame.columnconfigure(0, weight=1)

        self.auto_detect_button = ttk.Button(
            serial_frame,
            text="Find and connect Calliope automatically",
            command=self.start_auto_discovery,
        )
        self.auto_detect_button.grid(
            row=0, column=0, columnspan=3, sticky="ew", pady=(0, 10)
        )

        self.port_box = ttk.Combobox(serial_frame, state="readonly")
        self.port_box.grid(row=1, column=0, sticky="ew", padx=(0, 8))
        self.refresh_ports_button = ttk.Button(
            serial_frame,
            text="Refresh ports",
            command=self.refresh_serial_ports,
        )
        self.refresh_ports_button.grid(row=1, column=1, padx=(0, 8))
        self.calliope_connect_button = ttk.Button(
            serial_frame,
            text="Connect selected port",
            command=self.toggle_calliope_connection,
        )
        self.calliope_connect_button.grid(row=1, column=2)

        log_header = ttk.Frame(outer)
        log_header.grid(row=3, column=0, sticky="ew", pady=(5, 5))
        log_header.columnconfigure(0, weight=1)
        ttk.Label(log_header, text="Messages received", style="Section.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(log_header, text="Clear", command=self.clear_log).grid(
            row=0, column=1, sticky="e"
        )

        self.message_log = ScrolledText(
            outer,
            height=15,
            wrap="word",
            state="disabled",
            font=("Consolas", 10),
        )
        self.message_log.grid(row=4, column=0, sticky="nsew")

        self.refresh_serial_ports()
        self.log_message("IBM Quantum -> PC: Connection verified.")
        self.log_message(
            f"Accessible service instances: {connection_info['instance_count']}"
        )

        backend_names = connection_info["backend_names"]
        if backend_names:
            self.log_message(
                "Accessible quantum systems: " + ", ".join(backend_names)
            )
        elif connection_info["backend_error"]:
            self.log_message(
                "IBM system list unavailable: " + connection_info["backend_error"]
            )
        else:
            self.log_message("Accessible quantum systems: none found")

        self.log_message(connection_info["save_message"])
        self.after(250, self.start_auto_discovery)

    def refresh_serial_ports(self) -> None:
        if not self.dashboard_visible:
            return

        try:
            from serial.tools import list_ports
        except ImportError:
            self.port_devices = {}
            self.port_box.configure(values=("PySerial is not installed",))
            self.port_box.current(0)
            self.calliope_connect_button.configure(state="disabled")
            self.auto_detect_button.configure(state="disabled")
            self.log_message(
                "PC: PySerial is missing. Run: python -m pip install -r requirements.txt"
            )
            return

        ports = list(list_ports.comports())
        self.serial_port_info = {port.device: port for port in ports}
        self.port_devices = {
            f"{port.device} — {port.description}": port.device for port in ports
        }
        labels = list(self.port_devices)
        self.port_box.configure(values=labels)

        if labels:
            self.port_box.current(0)
            self.calliope_connect_button.configure(state="normal")
            self.auto_detect_button.configure(state="normal")
        else:
            self.port_box.set("")
            self.calliope_connect_button.configure(state="disabled")
            self.auto_detect_button.configure(state="disabled")
            self.log_message("PC: No serial device was found.")

    def start_auto_discovery(self) -> None:
        if not self.dashboard_visible or self.serial_connection is not None:
            return

        if not self.serial_port_info:
            self.log_message("PC: No serial ports are available for discovery.")
            return

        candidates = [
            port for port in self.serial_port_info.values() if is_calliope_port(port)
        ]
        if not candidates:
            self.calliope_status_label.configure(
                text="● Calliope: Not found",
                style="Disconnected.TLabel",
            )
            self.log_message(
                "PC: No Calliope USB device was identified. "
                "You can refresh or select a port manually."
            )
            return

        selected_port = candidates[0]
        if len(candidates) > 1:
            self.log_message(
                f"PC: Found {len(candidates)} Calliope devices; connecting to "
                f"{selected_port.device}."
            )
        else:
            self.log_message(
                f"PC: Identified Calliope hardware on {selected_port.device}."
            )

        for label, device in self.port_devices.items():
            if device == selected_port.device:
                self.port_box.set(label)
                break
        self.connect_calliope()

    def toggle_calliope_connection(self) -> None:
        if self.serial_connection is not None:
            self.disconnect_calliope()
        else:
            self.connect_calliope()

    def connect_calliope(self) -> None:
        label = self.port_box.get()
        port = self.port_devices.get(label)
        if port is None:
            messagebox.showwarning(
                "Select a port",
                "Select the Calliope serial port first.",
                parent=self,
            )
            return

        self.serial_stop.clear()
        self.calliope_connect_button.configure(state="disabled")
        self.auto_detect_button.configure(state="disabled")
        self.refresh_ports_button.configure(state="disabled")
        self.calliope_status_label.configure(
            text="● Calliope: Connecting...",
            style="Checking.TLabel",
        )
        self.log_message(f"PC: Opening {port} at {SERIAL_BAUD_RATE} baud...")
        self.serial_thread = threading.Thread(
            target=self.serial_worker,
            args=(port,),
            daemon=True,
        )
        self.serial_thread.start()

    def serial_worker(self, port: str) -> None:
        try:
            import serial

            connection = serial.Serial(
                port=port,
                baudrate=SERIAL_BAUD_RATE,
                timeout=0.5,
            )
            self.serial_connection = connection

            # Opening a serial port can restart the board. Give it time to boot.
            time.sleep(2)
            if self.serial_stop.is_set():
                return
            self.events.put(("calliope_connected", port))
            self.listen_to_calliope(connection)
        except Exception as exc:
            if not self.serial_stop.is_set():
                self.events.put(("calliope_error", str(exc)))
        finally:
            connection = self.serial_connection
            self.serial_connection = None
            if connection is not None:
                try:
                    connection.close()
                except Exception:
                    pass
            self.events.put(("calliope_disconnected", port))

    def listen_to_calliope(self, connection: Any) -> None:
        """Read and log newline-delimited Calliope messages until disconnected."""
        while not self.serial_stop.is_set():
            raw_line = connection.readline()
            if not raw_line:
                continue

            message = raw_line.decode("utf-8", errors="replace").strip()
            if not message:
                continue

            self.events.put(("serial_received", message))

            if message == "HELLO":
                self.send_calliope("HELLO_ACK")
            elif message.startswith("IBMQ_"):
                self.handle_ibm_protocol_message(message)

    def send_calliope(self, message: str) -> bool:
        """Send one protocol line without interleaving concurrent IBM jobs."""
        connection = self.serial_connection
        if connection is None:
            self.events.put(
                ("bridge_log", f"PC: Could not send while Calliope is disconnected: {message}")
            )
            return False

        try:
            with self.serial_write_lock:
                connection.write((message + "\n").encode("utf-8"))
                connection.flush()
                time.sleep(0.01)
        except Exception as exc:
            self.events.put(("bridge_log", f"PC: Serial send failed: {exc}"))
            return False

        self.events.put(("serial_sent", message))
        return True

    def protocol_error(self, request_id: str, message: str) -> None:
        safe_message = self.safe_protocol_text(message)
        with self.ibm_jobs_lock:
            self.ibm_job_statuses[request_id] = "FAILED"
        self.send_calliope(f"IBMQ_ERROR|{request_id}|{safe_message}")

    def send_ibm_status(self, request_id: str, status: str) -> None:
        with self.ibm_jobs_lock:
            self.ibm_job_statuses[request_id] = status
        self.send_calliope(f"IBMQ_STATUS|{request_id}|{status}")

    def replay_ibm_result(self, request_id: str) -> None:
        with self.ibm_jobs_lock:
            result = self.ibm_job_results.get(request_id)

        if result is None:
            return

        first_shot = result["first_shot"]
        if first_shot:
            self.send_calliope(f"IBMQ_SHOT|{request_id}|{first_shot}")
        for label in sorted(result["counts"]):
            self.send_calliope(
                f"IBMQ_COUNT|{request_id}|{label}|{result['counts'][label]}"
            )
        self.send_calliope(f"IBMQ_DONE|{request_id}|{result['shots']}")

    @staticmethod
    def safe_protocol_text(message: str) -> str:
        return message.replace("|", "/").replace("\r", " ").replace("\n", " ")[:180]

    def handle_ibm_protocol_message(self, message: str) -> None:
        """Collect a framed Calliope circuit and start its IBM job."""
        parts = message.split("|")
        message_kind = parts[0]
        request_id = parts[1] if len(parts) >= 2 else "unknown"

        try:
            if message_kind == "IBMQ_GET_STATUS":
                if len(parts) != 2:
                    raise ValueError("Invalid IBM status request")
                with self.ibm_jobs_lock:
                    status = self.ibm_job_statuses.get(request_id)
                if status is None:
                    raise ValueError("IBM job is unknown to the PC bridge")
                self.send_calliope(f"IBMQ_STATUS|{request_id}|{status}")
                return

            if message_kind == "IBMQ_GET_RESULT":
                if len(parts) != 2:
                    raise ValueError("Invalid IBM result request")
                with self.ibm_jobs_lock:
                    result_exists = request_id in self.ibm_job_results
                    status = self.ibm_job_statuses.get(request_id)
                if result_exists:
                    threading.Thread(
                        target=self.replay_ibm_result,
                        args=(request_id,),
                        daemon=True,
                    ).start()
                elif status is not None:
                    self.send_calliope(f"IBMQ_STATUS|{request_id}|{status}")
                else:
                    raise ValueError("IBM job is unknown to the PC bridge")
                return

            if message_kind == "IBMQ_BEGIN":
                if len(parts) != 5:
                    raise ValueError("Invalid circuit header")
                if not request_id or not all(
                    character.isalnum() or character in "_-" for character in request_id
                ):
                    raise ValueError("Invalid request ID")

                num_qubits = int(parts[2])
                num_clbits = int(parts[3])
                shots = int(parts[4])
                if num_qubits < 1 or num_qubits > 8:
                    raise ValueError("Qubit count must be between 1 and 8")
                if num_clbits < 1 or num_clbits > 8:
                    raise ValueError("Classical bit count must be between 1 and 8")
                if shots < 1 or shots > 2048:
                    raise ValueError("Shots must be between 1 and 2048")

                with self.ibm_jobs_lock:
                    if request_id in self.active_ibm_jobs:
                        raise ValueError("This IBM job is already active")
                    self.ibm_job_results.pop(request_id, None)
                    self.ibm_job_statuses[request_id] = "RECEIVING_CIRCUIT"
                self.incoming_circuits[request_id] = {
                    "request_id": request_id,
                    "num_qubits": num_qubits,
                    "num_clbits": num_clbits,
                    "shots": shots,
                    "gates": [],
                }
                return

            if message_kind == "IBMQ_GATE":
                if len(parts) != 6 or request_id not in self.incoming_circuits:
                    raise ValueError("Gate received without a circuit header")
                request = self.incoming_circuits[request_id]
                if len(request["gates"]) >= 1000:
                    raise ValueError("Circuit has too many operations")
                request["gates"].append(
                    {
                        "kind": parts[2].lower(),
                        "qubit": int(parts[3]),
                        "target": int(parts[4]),
                        "theta": float(parts[5]),
                    }
                )
                return

            if message_kind == "IBMQ_END":
                if len(parts) != 2 or request_id not in self.incoming_circuits:
                    raise ValueError("Circuit end received without a circuit header")
                request = self.incoming_circuits.pop(request_id)
                if self.ibm_service is None:
                    raise ValueError("IBM Quantum is not connected")
                with self.ibm_jobs_lock:
                    self.active_ibm_jobs.add(request_id)
                    self.ibm_job_statuses[request_id] = "RECEIVED"
                threading.Thread(
                    target=self.ibm_job_worker,
                    args=(request, self.ibm_service),
                    daemon=True,
                ).start()
                return

            raise ValueError("Unknown IBM protocol message")
        except (TypeError, ValueError) as exc:
            self.incoming_circuits.pop(request_id, None)
            self.protocol_error(request_id, str(exc))

    def ibm_job_worker(self, request: dict[str, Any], service: Any) -> None:
        """Build, transpile, execute and return one real IBM Sampler job."""
        request_id = request["request_id"]

        try:
            from qiskit import QuantumCircuit
            from qiskit.transpiler import generate_preset_pass_manager
            from qiskit_ibm_runtime import SamplerV2

            circuit = QuantumCircuit(
                request["num_qubits"],
                request["num_clbits"],
            )
            measurement_count = 0

            for gate in request["gates"]:
                kind = gate["kind"]
                qubit = gate["qubit"]
                target = gate["target"]
                theta = gate["theta"]

                if qubit < 0 or qubit >= request["num_qubits"]:
                    raise ValueError(f"Qubit index out of range: {qubit}")

                if kind in {"x", "y", "z", "h"}:
                    getattr(circuit, kind)(qubit)
                elif kind in {"rx", "ry", "rz"}:
                    getattr(circuit, kind)(theta, qubit)
                elif kind in {"cx", "crx"}:
                    if target < 0 or target >= request["num_qubits"]:
                        raise ValueError(f"Target qubit out of range: {target}")
                    if kind == "cx":
                        circuit.cx(qubit, target)
                    else:
                        circuit.crx(theta, qubit, target)
                elif kind == "measure":
                    if target < 0 or target >= request["num_clbits"]:
                        raise ValueError(f"Classical bit out of range: {target}")
                    circuit.measure(qubit, target)
                    measurement_count += 1
                else:
                    raise ValueError(f"Unsupported IBM gate: {kind}")

            if measurement_count == 0:
                raise ValueError("The circuit needs at least one measurement")

            self.send_ibm_status(request_id, "SELECTING_QPU")
            backend = service.least_busy(
                operational=True,
                simulator=False,
                min_num_qubits=request["num_qubits"],
            )
            selected_backend_name = backend_name(backend)

            self.send_ibm_status(request_id, "TRANSPILING")
            pass_manager = generate_preset_pass_manager(
                backend=backend,
                optimization_level=1,
            )
            isa_circuit = pass_manager.run(circuit)

            sampler = SamplerV2(mode=backend)
            runtime_job = sampler.run([isa_circuit], shots=request["shots"])
            remote_job_id = runtime_job.job_id()
            self.send_calliope(
                f"IBMQ_ACCEPTED|{request_id}|{remote_job_id}|{selected_backend_name}"
            )

            last_status = ""
            while True:
                status_value = runtime_job.status()
                status = getattr(status_value, "name", str(status_value))
                status = status.split(".")[-1].upper()
                if status != last_status:
                    displayed_status = (
                        "RETRIEVING_RESULT" if status == "DONE" else status
                    )
                    self.send_ibm_status(request_id, displayed_status)
                    last_status = status
                if status in {"DONE", "ERROR", "CANCELLED"}:
                    break
                time.sleep(3)

            result = runtime_job.result()
            data = result[0].data
            bit_array = getattr(data, "c", None)
            if bit_array is None:
                keys = list(data.keys())
                if not keys:
                    raise ValueError("IBM returned no classical measurement data")
                bit_array = data[keys[0]]

            bitstrings = bit_array.get_bitstrings()
            counts = bit_array.get_counts()
            with self.ibm_jobs_lock:
                self.ibm_job_results[request_id] = {
                    "first_shot": bitstrings[0] if bitstrings else "",
                    "bitstrings": list(bitstrings),
                    "counts": dict(counts),
                    "shots": len(bitstrings),
                    "backend": selected_backend_name,
                    "ibm_job_id": remote_job_id,
                }
                self.ibm_job_statuses[request_id] = "RESULT_READY"
            self.events.put(
                (
                    "bridge_log",
                    f"IBM job {remote_job_id}: cached {len(bitstrings)} shots "
                    f"and {len(counts)} outcomes locally.",
                )
            )
            self.replay_ibm_result(request_id)
            with self.ibm_jobs_lock:
                self.ibm_job_statuses[request_id] = "DONE"
        except Exception as exc:
            self.protocol_error(request_id, str(exc))
        finally:
            with self.ibm_jobs_lock:
                self.active_ibm_jobs.discard(request_id)

    def disconnect_calliope(self) -> None:
        self.serial_stop.set()
        connection = self.serial_connection
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass

    def check_ibm_connection(self) -> None:
        if self.ibm_service is None:
            return
        self.ibm_check_button.configure(state="disabled")
        self.ibm_status_label.configure(
            text="● IBM Quantum: Checking...",
            style="Checking.TLabel",
        )
        threading.Thread(target=self.ibm_check_worker, daemon=True).start()

    def ibm_check_worker(self) -> None:
        try:
            instances = self.ibm_service.instances()
            self.events.put(("ibm_check_ok", len(instances)))
        except Exception as exc:
            self.events.put(("ibm_check_error", str(exc)))

    def log_message(self, message: str) -> None:
        if not self.dashboard_visible:
            return
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.message_log.configure(state="normal")
        self.message_log.insert("end", f"[{timestamp}] {message}\n")
        self.message_log.see("end")
        self.message_log.configure(state="disabled")

    def clear_log(self) -> None:
        self.message_log.configure(state="normal")
        self.message_log.delete("1.0", "end")
        self.message_log.configure(state="disabled")

    def process_events(self) -> None:
        while True:
            try:
                event_name, payload = self.events.get_nowait()
            except queue.Empty:
                break
            self.handle_event(event_name, payload)

        if not self.closing:
            self.after(100, self.process_events)

    def handle_event(self, event_name: str, payload: Any) -> None:
        if event_name == "ibm_connected":
            self.ibm_service = payload["service"]
            self.token_entry.delete(0, "end")
            self.show_dashboard(payload)
            return

        if event_name == "ibm_error":
            self.connect_ibm_button.configure(state="normal")
            self.login_status.configure(
                text="Connection failed.",
                style="Disconnected.TLabel",
            )
            messagebox.showerror(
                "IBM connection failed",
                str(payload)
                + "\n\nCheck the API key, internet connection, and service instance.",
                parent=self,
            )
            return

        if not self.dashboard_visible:
            return

        if event_name == "calliope_connected":
            for label, device in self.port_devices.items():
                if device == payload:
                    self.port_box.configure(state="readonly")
                    self.port_box.set(label)
                    self.port_box.configure(state="disabled")
                    break
            self.calliope_status_label.configure(
                text=f"● Calliope: Connected ({payload})",
                style="Connected.TLabel",
            )
            self.calliope_connect_button.configure(
                text="Disconnect Calliope",
                state="normal",
            )
            self.log_message(f"Calliope connected on {payload}.")
        elif event_name == "calliope_disconnected":
            self.calliope_status_label.configure(
                text="● Calliope: Disconnected",
                style="Disconnected.TLabel",
            )
            self.calliope_connect_button.configure(
                text="Connect selected port",
                state="normal" if self.port_devices else "disabled",
            )
            self.auto_detect_button.configure(
                state="normal" if self.port_devices else "disabled"
            )
            self.refresh_ports_button.configure(state="normal")
            self.port_box.configure(state="readonly")
            self.log_message("Calliope disconnected.")
        elif event_name == "calliope_error":
            self.log_message(f"Calliope connection error: {payload}")
            messagebox.showerror(
                "Calliope connection failed",
                str(payload),
                parent=self,
            )
        elif event_name == "serial_received":
            self.log_message(f"Calliope -> PC: {payload}")
        elif event_name == "serial_sent":
            self.log_message(f"PC -> Calliope: {payload}")
        elif event_name == "bridge_log":
            self.log_message(str(payload))
        elif event_name == "ibm_check_ok":
            self.ibm_status_label.configure(
                text="● IBM Quantum: Connected",
                style="Connected.TLabel",
            )
            self.ibm_check_button.configure(state="normal")
            self.log_message(
                f"IBM Quantum -> PC: Connection verified ({payload} instances)."
            )
        elif event_name == "ibm_check_error":
            self.ibm_status_label.configure(
                text="● IBM Quantum: Disconnected",
                style="Disconnected.TLabel",
            )
            self.ibm_check_button.configure(state="normal")
            self.log_message(f"IBM connection check failed: {payload}")

    def sign_out(self) -> None:
        self.disconnect_calliope()
        self.ibm_service = None
        self.show_login_screen()

    def close_app(self) -> None:
        self.closing = True
        self.disconnect_calliope()
        self.destroy()


def main() -> None:
    app = QiskitBridgeApp()
    app.mainloop()


if __name__ == "__main__":
    main()
