import random


def make_event(message, frame=None, status="INFO"):
    return {
        "message": message,
        "frame": frame,
        "status": status
    }


def make_summary(total_frames, total_sent, retransmissions, delivered, protocol):
    return {
        "total_frames": total_frames,
        "total_sent": total_sent,
        "retransmissions": retransmissions,
        "delivered": delivered,
        "protocol": protocol
    }


def simulate(protocol, total_frames, window_size, packet_loss, ack_loss):
    if protocol == "Go-Back-N":
        return simulate_gbn(
            total_frames,
            window_size,
            packet_loss,
            ack_loss
        )

    return simulate_selective_repeat(
        total_frames,
        window_size,
        packet_loss,
        ack_loss
    )


# ---------------------------------------------------------
# GO-BACK-N
# ---------------------------------------------------------

def simulate_gbn(total_frames, window_size, packet_loss, ack_loss):

    events = []
    base = 0
    next_frame = 0

    total_sent = 0
    retransmissions = 0
    delivered = 0

    events.append(
        make_event(
            f"Starting Go-Back-N simulation | "
            f"Frames={total_frames}, Window={window_size}",
            status="INFO"
        )
    )

    max_attempts = total_frames * 20
    attempts = 0

    while base < total_frames and attempts < max_attempts:

        # Send all frames currently inside the window
        window_end = min(base + window_size, total_frames)

        events.append(
            make_event(
                f"Sender Window: "
                f"{list(range(base, window_end))}",
                status="INFO"
            )
        )

        frame = next_frame

        while frame < window_end:

            attempts += 1

            if attempts >= max_attempts:
                break

            is_retransmission = frame < next_frame

            if is_retransmission:
                retransmissions += 1

            total_sent += 1

            events.append(
                make_event(
                    f"Sending Frame {frame}...",
                    frame,
                    "TRANSMITTING"
                )
            )

            # Packet loss
            packet_random = random.randint(1, 100)

            if packet_random <= packet_loss:

                events.append(
                    make_event(
                        f"✗ Frame {frame} lost in network",
                        frame,
                        "PACKET LOST"
                    )
                )

                events.append(
                    make_event(
                        f"Timeout for Frame {frame} "
                        f"→ Go-Back-N retransmission required",
                        frame,
                        "TIMEOUT"
                    )
                )

                # Retransmit from the first unacknowledged frame
                next_frame = base
                break

            # Receiver gets frame
            events.append(
                make_event(
                    f"✓ Frame {frame} received",
                    frame,
                    "RECEIVED"
                )
            )

            # ACK loss
            ack_random = random.randint(1, 100)

            if ack_random <= ack_loss:

                events.append(
                    make_event(
                        f"✗ ACK {frame} lost",
                        frame,
                        "ACK LOST"
                    )
                )

                events.append(
                    make_event(
                        f"Timeout waiting for ACK {frame}",
                        frame,
                        "TIMEOUT"
                    )
                )

                next_frame = base
                break

            # ACK successfully received
            events.append(
                make_event(
                    f"← ACK {frame} received (cumulative)",
                    frame,
                    "ACK RECEIVED"
                )
            )

            base = frame + 1
            delivered = base
            next_frame = base

            frame += 1

        else:
            # Entire current window successfully processed
            continue

    if attempts >= max_attempts and base < total_frames:

        events.append(
            make_event(
                "Simulation stopped because maximum attempts were reached.",
                status="ERROR"
            )
        )

    events.append(
        make_event(
            "Simulation completed.",
            status="COMPLETE"
        )
    )

    summary = make_summary(
        total_frames,
        total_sent,
        retransmissions,
        delivered,
        "Go-Back-N"
    )

    events[-1]["summary"] = summary

    return events, summary


# ---------------------------------------------------------
# SELECTIVE REPEAT
# ---------------------------------------------------------

def simulate_selective_repeat(
    total_frames,
    window_size,
    packet_loss,
    ack_loss
):

    events = []

    acknowledged = set()
    next_frame = 0

    total_sent = 0
    retransmissions = 0

    max_attempts = total_frames * 20
    attempts = 0

    events.append(
        make_event(
            f"Starting Selective Repeat simulation | "
            f"Frames={total_frames}, Window={window_size}",
            status="INFO"
        )
    )

    while len(acknowledged) < total_frames and attempts < max_attempts:

        # Current sliding window
        base = 0

        while base < total_frames and base in acknowledged:
            base += 1

        window_end = min(
            base + window_size,
            total_frames
        )

        window = [
            frame
            for frame in range(base, window_end)
            if frame not in acknowledged
        ]

        if not window:
            continue

        events.append(
            make_event(
                f"Sender Window: {window}",
                status="INFO"
            )
        )

        for frame in window:

            if frame in acknowledged:
                continue

            attempts += 1

            if attempts >= max_attempts:
                break

            total_sent += 1

            # A frame that has already been attempted is a retransmission
            previous_attempts = any(
                event.get("frame") == frame
                and event.get("status") == "TRANSMITTING"
                for event in events
            )

            if previous_attempts:
                retransmissions += 1

            events.append(
                make_event(
                    f"Sending Frame {frame}...",
                    frame,
                    "TRANSMITTING"
                )
            )

            # Packet loss
            packet_random = random.randint(1, 100)

            if packet_random <= packet_loss:

                events.append(
                    make_event(
                        f"✗ Frame {frame} lost in network",
                        frame,
                        "PACKET LOST"
                    )
                )

                events.append(
                    make_event(
                        f"Timeout for Frame {frame} "
                        f"→ only Frame {frame} will be retransmitted",
                        frame,
                        "TIMEOUT"
                    )
                )

                continue

            # Receiver gets frame
            events.append(
                make_event(
                    f"✓ Frame {frame} received",
                    frame,
                    "RECEIVED"
                )
            )

            # ACK loss
            ack_random = random.randint(1, 100)

            if ack_random <= ack_loss:

                events.append(
                    make_event(
                        f"✗ ACK {frame} lost",
                        frame,
                        "ACK LOST"
                    )
                )

                events.append(
                    make_event(
                        f"Timeout for Frame {frame}",
                        frame,
                        "TIMEOUT"
                    )
                )

                continue

            # ACK received
            acknowledged.add(frame)

            events.append(
                make_event(
                    f"← ACK {frame} received",
                    frame,
                    "ACK RECEIVED"
                )
            )

        # Safety check
        if attempts >= max_attempts:
            break

    delivered = len(acknowledged)

    if attempts >= max_attempts and delivered < total_frames:

        events.append(
            make_event(
                "Simulation stopped because maximum attempts were reached.",
                status="ERROR"
            )
        )

    events.append(
        make_event(
            "Simulation completed.",
            status="COMPLETE"
        )
    )

    summary = make_summary(
        total_frames,
        total_sent,
        retransmissions,
        delivered,
        "Selective Repeat"
    )

    events[-1]["summary"] = summary

    return events, summary