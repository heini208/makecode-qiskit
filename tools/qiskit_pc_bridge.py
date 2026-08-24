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


def serial_frame_checksum(payload: str) -> int:
    """Match the small checksum used by the MakeCode transport."""
    checksum = 0
    for index, character in enumerate(payload):
        checksum = (checksum + ord(character) * (index + 1)) % 65521
    return checksum


class QiskitBridgeApp(tk.Tk):
    """Small desktop interface for IBM and Calliope connections."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Calliope Qiskit Bridge")
        self.geometry("920x720")
        self.minsize(760, 620)

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
        self.ibm_job_aliases: dict[str, str] = {}
        self.ibm_job_backends: dict[str, str] = {}
        self.ibm_jobs_lock = threading.Lock()
        self.received_serial_frames: set[tuple[int, int]] = set()
        self.framed_transport_active = False
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
        outer.rowconfigure(6, weight=1)

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

        jobs_frame = ttk.LabelFrame(outer, text="Known IBM jobs", padding=10)
        jobs_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 8))
        jobs_frame.columnconfigure(0, weight=1)

        job_columns = ("calliope_id", "ibm_id", "backend", "status", "cached")
        self.jobs_table = ttk.Treeview(
            jobs_frame,
            columns=job_columns,
            show="headings",
            height=5,
        )
        self.jobs_table.heading("calliope_id", text="Calliope job")
        self.jobs_table.heading("ibm_id", text="IBM Runtime ID")
        self.jobs_table.heading("backend", text="Quantum system")
        self.jobs_table.heading("status", text="Status")
        self.jobs_table.heading("cached", text="Result cached")
        self.jobs_table.column("calliope_id", width=95, stretch=False)
        self.jobs_table.column("ibm_id", width=205)
        self.jobs_table.column("backend", width=145)
        self.jobs_table.column("status", width=145)
        self.jobs_table.column("cached", width=95, stretch=False, anchor="center")
        self.jobs_table.grid(row=0, column=0, sticky="nsew")
        self.selected_job_id = ""
        self.jobs_table.bind("<ButtonRelease-1>", self.select_job_id_cell)
        self.jobs_table.bind("<Double-1>", self.copy_clicked_job_id)
        self.jobs_table.bind("<Control-c>", self.copy_selected_job_id)

        jobs_scrollbar = ttk.Scrollbar(
            jobs_frame,
            orient="vertical",
            command=self.jobs_table.yview,
        )
        jobs_scrollbar.grid(row=0, column=1, sticky="ns")
        self.jobs_table.configure(yscrollcommand=jobs_scrollbar.set)

        jobs_actions = ttk.Frame(jobs_frame)
        jobs_actions.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(7, 0))
        jobs_actions.columnconfigure(0, weight=1)
        ttk.Label(
            jobs_actions,
            text="Click an ID, then copy it—or double-click the ID directly.",
            foreground="#555555",
        ).grid(row=0, column=0, sticky="w")
        self.copy_job_id_button = ttk.Button(
            jobs_actions,
            text="Copy selected ID",
            command=self.copy_selected_job_id,
            state="disabled",
        )
        self.copy_job_id_button.grid(row=0, column=1, sticky="e")

        self.last_sent_var = tk.StringVar(value="Nothing sent yet")
        ttk.Label(
            outer,
            textvariable=self.last_sent_var,
            wraplength=850,
            foreground="#444444",
        ).grid(row=4, column=0, sticky="ew", pady=(0, 7))

        log_header = ttk.Frame(outer)
        log_header.grid(row=5, column=0, sticky="ew", pady=(5, 5))
        log_header.columnconfigure(0, weight=1)
        ttk.Label(
            log_header,
            text="Serial communication",
            style="Section.TLabel",
        ).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(log_header, text="Clear", command=self.clear_log).grid(
            row=0, column=1, sticky="e"
        )

        self.message_log = ScrolledText(
            outer,
            height=11,
            wrap="word",
            state="disabled",
            font=("Consolas", 10),
        )
        self.message_log.grid(row=6, column=0, sticky="nsew")

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
        self.refresh_jobs_table()
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
        pending = bytearray()

        while not self.serial_stop.is_set():
            waiting = connection.in_waiting
            chunk = connection.read(waiting if waiting > 0 else 1)
            if not chunk:
                continue

            pending.extend(chunk)

            newline_index = pending.find(b"\n")
            while newline_index >= 0:
                raw_line = bytes(pending[:newline_index])
                del pending[: newline_index + 1]

                message = raw_line.decode("utf-8", errors="replace").strip()
                if message:
                    self.handle_calliope_serial_message(message)

                newline_index = pending.find(b"\n")

            if len(pending) > 4096:
                self.events.put(
                    (
                        "bridge_log",
                        "PC: Discarded an unterminated serial message larger than 4096 bytes.",
                    )
                )
                pending.clear()

    def handle_calliope_serial_message(self, message: str) -> None:
        """Validate framed traffic and retain compatibility with older firmware."""
        if message.startswith("MQF|"):
            self.handle_calliope_serial_frame(message)
            return

        self.events.put(("serial_received", message))
        if message == "HELLO":
            self.send_calliope("HELLO_ACK")
        elif message.startswith("IBMQ_"):
            if self.framed_transport_active:
                self.events.put(
                    (
                        "bridge_log",
                        "PC: Ignored an unframed IBM message after framed transport started.",
                    )
                )
            else:
                self.handle_ibm_protocol_message(message)

    def handle_calliope_serial_frame(self, message: str) -> None:
        """Check one Calliope frame, acknowledge it, and process it once."""
        parts = message.split("|", 4)
        if len(parts) != 5:
            self.events.put(("bridge_log", "PC: Discarded a damaged serial frame."))
            return

        try:
            session = int(parts[1])
            sequence = int(parts[2])
            received_checksum = int(parts[3])
        except ValueError:
            self.events.put(("bridge_log", "PC: Discarded a malformed serial frame."))
            return

        payload = parts[4]
        expected_checksum = serial_frame_checksum(payload)
        if received_checksum != expected_checksum:
            self.send_calliope(f"MQN|{session}|{sequence}")
            self.events.put(
                (
                    "bridge_log",
                    f"PC: Frame {session}:{sequence} failed its checksum and was rejected.",
                )
            )
            return

        frame_key = (session, sequence)
        self.send_calliope(f"MQA|{session}|{sequence}")
        if frame_key in self.received_serial_frames:
            self.events.put(
                (
                    "bridge_log",
                    f"PC: Frame {session}:{sequence} was already processed; acknowledged retry.",
                )
            )
            return

        if len(self.received_serial_frames) >= 2048:
            self.received_serial_frames.clear()
        self.received_serial_frames.add(frame_key)
        self.framed_transport_active = True
        self.events.put(
            (
                "serial_received",
                f"{payload}  [verified frame {session}:{sequence}]",
            )
        )

        if payload.startswith("IBMQ_"):
            self.handle_ibm_protocol_message(payload)
        else:
            self.events.put(
                ("bridge_log", f"PC: Ignored unsupported framed message: {payload}")
            )

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
                connection.write((message + "\r\n").encode("utf-8"))
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
            cache_key = self.ibm_job_aliases.get(request_id, request_id)
            result = self.ibm_job_results.get(cache_key)

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

    def start_ibm_job_lookup(self, ibm_job_id: str) -> None:
        """Retrieve an IBM job that was identified directly by its Runtime ID."""
        if self.ibm_service is None:
            raise ValueError("IBM Quantum is not connected")

        with self.ibm_jobs_lock:
            if ibm_job_id in self.active_ibm_jobs:
                return
            self.active_ibm_jobs.add(ibm_job_id)
            self.ibm_job_statuses[ibm_job_id] = "LOOKING_UP_JOB"

        self.events.put(
            ("bridge_log", f"PC: Looking up IBM Runtime job {ibm_job_id}.")
        )
        self.send_calliope(f"IBMQ_STATUS|{ibm_job_id}|LOOKING_UP_JOB")
        threading.Thread(
            target=self.ibm_job_lookup_worker,
            args=(ibm_job_id, self.ibm_service),
            daemon=True,
        ).start()

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
                    cache_key = self.ibm_job_aliases.get(request_id, request_id)
                    status = self.ibm_job_statuses.get(cache_key)
                if status is None:
                    self.start_ibm_job_lookup(request_id)
                    return
                self.send_calliope(f"IBMQ_STATUS|{request_id}|{status}")
                return

            if message_kind == "IBMQ_GET_RESULT":
                if len(parts) != 2:
                    raise ValueError("Invalid IBM result request")
                with self.ibm_jobs_lock:
                    cache_key = self.ibm_job_aliases.get(request_id, request_id)
                    result_exists = cache_key in self.ibm_job_results
                    status = self.ibm_job_statuses.get(cache_key)
                if result_exists:
                    threading.Thread(
                        target=self.replay_ibm_result,
                        args=(request_id,),
                        daemon=True,
                    ).start()
                elif status is not None:
                    self.send_calliope(f"IBMQ_STATUS|{request_id}|{status}")
                else:
                    self.start_ibm_job_lookup(request_id)
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
            self.monitor_ibm_runtime_job(
                request_id,
                runtime_job,
                selected_backend_name,
            )
        except Exception as exc:
            self.protocol_error(request_id, str(exc))
        finally:
            with self.ibm_jobs_lock:
                self.active_ibm_jobs.discard(request_id)

    def ibm_job_lookup_worker(self, ibm_job_id: str, service: Any) -> None:
        """Load and monitor a previously submitted Sampler job by IBM ID."""
        try:
            runtime_job = service.job(ibm_job_id)
            backend = getattr(runtime_job, "backend", None)
            backend = backend() if callable(backend) else backend
            selected_backend_name = backend_name(backend) if backend else "unknown"
            self.monitor_ibm_runtime_job(
                ibm_job_id,
                runtime_job,
                selected_backend_name,
            )
        except Exception as exc:
            self.protocol_error(ibm_job_id, str(exc))
        finally:
            with self.ibm_jobs_lock:
                self.active_ibm_jobs.discard(ibm_job_id)

    def monitor_ibm_runtime_job(
        self,
        request_id: str,
        runtime_job: Any,
        selected_backend_name: str,
    ) -> None:
        """Monitor one submitted or retrieved job and cache its Sampler result."""
        remote_job_id = runtime_job.job_id()
        with self.ibm_jobs_lock:
            self.ibm_job_aliases[remote_job_id] = request_id
            self.ibm_job_backends[request_id] = selected_backend_name

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

    def select_job_id_cell(self, event: Any) -> None:
        """Remember a clicked Calliope or IBM ID cell for copying."""
        item_id = self.jobs_table.identify_row(event.y)
        column_id = self.jobs_table.identify_column(event.x)
        if not item_id or column_id not in {"#1", "#2"}:
            self.selected_job_id = ""
            self.copy_job_id_button.configure(state="disabled")
            return

        values = self.jobs_table.item(item_id, "values")
        value_index = 0 if column_id == "#1" else 1
        value = str(values[value_index]) if len(values) > value_index else ""
        self.selected_job_id = "" if value == "—" else value
        self.copy_job_id_button.configure(
            state="normal" if self.selected_job_id else "disabled"
        )

    def copy_clicked_job_id(self, event: Any) -> None:
        """Copy the ID beneath a double-click."""
        self.select_job_id_cell(event)
        self.copy_selected_job_id()

    def copy_selected_job_id(self, _event: Any = None) -> None:
        """Copy the most recently selected job ID to the system clipboard."""
        if not self.selected_job_id:
            return

        self.clipboard_clear()
        self.clipboard_append(self.selected_job_id)
        self.update_idletasks()
        self.log_message(f"PC: Copied job ID: {self.selected_job_id}")

    def refresh_jobs_table(self) -> None:
        """Refresh the dashboard from the thread-safe in-memory IBM job cache."""
        if not self.dashboard_visible or not hasattr(self, "jobs_table"):
            return

        with self.ibm_jobs_lock:
            statuses = dict(self.ibm_job_statuses)
            results = dict(self.ibm_job_results)
            aliases = dict(self.ibm_job_aliases)
            backends = dict(self.ibm_job_backends)

        remote_ids_by_key = {
            cache_key: remote_id for remote_id, cache_key in aliases.items()
        }
        known_keys = sorted(set(statuses) | set(results) | set(backends))

        for item_id in self.jobs_table.get_children():
            self.jobs_table.delete(item_id)

        for cache_key in known_keys:
            result = results.get(cache_key, {})
            remote_id = str(
                result.get("ibm_job_id")
                or remote_ids_by_key.get(cache_key)
                or (cache_key if not cache_key.startswith("job") else "")
            )
            calliope_id = cache_key if cache_key.startswith("job") else "—"
            backend = str(
                result.get("backend") or backends.get(cache_key) or "—"
            )
            status = statuses.get(cache_key, "UNKNOWN")
            readable_status = status.replace("_", " ").title()
            self.jobs_table.insert(
                "",
                "end",
                values=(
                    calliope_id,
                    remote_id or "—",
                    backend,
                    readable_status,
                    "Yes" if cache_key in results else "No",
                ),
            )

        self.after(500, self.refresh_jobs_table)

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
            self.last_sent_var.set(f"Last sent to Calliope: {payload}")
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
