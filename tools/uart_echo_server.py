from __future__ import annotations

import argparse
import sys
import time

import serial


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Test USB serial communication with the Calliope mini."
    )
    parser.add_argument(
        "--port",
        required=True,
        help="Serial port, for example COM14 or /dev/ttyACM0.",
    )
    parser.add_argument(
        "--baud",
        type=int,
        default=115200,
        help="Serial baud rate.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        with serial.Serial(
            port=args.port,
            baudrate=args.baud,
            timeout=1,
        ) as connection:
            time.sleep(2)
            connection.reset_input_buffer()

            print(
                f"Listening on {args.port} at {args.baud} baud."
            )

            while True:
                raw_line = connection.readline()

                if not raw_line:
                    continue

                message = raw_line.decode(
                    "utf-8",
                    errors="replace",
                ).strip()

                if not message:
                    continue

                print(f"Calliope -> PC: {message}")

                if message == "HELLO":
                    connection.write(b"HELLO_ACK\n")
                    connection.flush()
                    print("PC -> Calliope: HELLO_ACK")

                elif message == "RECEIVED":
                    print("Handshake completed successfully.")
                    return 0

    except serial.SerialException as exc:
        print(f"Serial error: {exc}", file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        print("\nStopped.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())