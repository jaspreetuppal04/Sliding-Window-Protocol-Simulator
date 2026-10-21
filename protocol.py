import random

def make_event(message, frame=None, status="INFO"):
    return {"message": message, "frame": frame, "status": status}


def make_summary(total_frames, total_sent, retransmissions, delivered, protocol):
    return {
        "total_frames": total_frames,
        "total_sent": total_sent,
        "retransmissions": retransmissions,
        "delivered": delivered,
        "protocol": protocol,
    }


def _lost(percent):
    """Return True when this transmission/ACK is lost."""
    return random.randint(1, 100) <= percent


def _validate(total_frames, window_size, packet_loss, ack_loss):
    total_frames = max(0, int(total_frames))
    window_size = max(1, int(window_size))
    packet_loss = max(0, min(100, int(packet_loss)))
    ack_loss = max(0, min(100, int(ack_loss)))
    return total_frames, window_size, packet_loss, ack_loss


def simulate(protocol, total_frames, window_size, packet_loss, ack_loss):
    """Run Go-Back-N or Selective Repeat, preserving the GUI's expected API."""
    total_frames, window_size, packet_loss, ack_loss = _validate(
        total_frames, window_size, packet_loss, ack_loss
    )
    if protocol == "Go-Back-N":
        return simulate_gbn(total_frames, window_size, packet_loss, ack_loss)
    return simulate_selective_repeat(
        total_frames, window_size, packet_loss, ack_loss
    )


def simulate_gbn(total_frames, window_size, packet_loss, ack_loss):
    """Go-Back-N with cumulative ACKs and retransmission from the oldest
    unacknowledged frame. The receiver accepts only in-order frames.
    """
    events = [make_event(
        f"Starting Go-Back-N simulation | Frames={total_frames}, Window={window_size}"
    )]
    base = 0
    receiver_next = 0
    attempts_by_frame = [0] * total_frames
    total_sent = 0
    retransmissions = 0
    # Bound the simulation in extreme-loss cases (e.g. 99% packet + ACK loss).
    max_attempts = max(1000, total_frames * 1000)
    attempts = 0

    while base < total_frames and attempts < max_attempts:
        round_base = base
        window_end = min(round_base + window_size, total_frames)
        current_window = list(range(round_base, window_end))
        events.append(make_event(f"Sender Window: {current_window}"))
        base_before_round = base
        best_cumulative_ack = base - 1

        # Send every frame in this window. A later frame may be discarded by
        # the receiver if an earlier frame was lost, which is normal for GBN.
        for frame in current_window:
            if attempts >= max_attempts:
                break
            attempts += 1
            if attempts_by_frame[frame] > 0:
                retransmissions += 1
            attempts_by_frame[frame] += 1
            total_sent += 1
            events.append(make_event(
                f"Current Sender Window: {current_window}", frame, "INFO"
            ))
            events.append(make_event(f"Sending Frame {frame}...", frame, "TRANSMITTING"))

            if _lost(packet_loss):
                events.append(make_event(
                    f"✗ Frame {frame} lost in network", frame, "PACKET LOST"
                ))
                events.append(make_event(
                    f"Timeout for Frame {frame} → Go-Back-N retransmission required",
                    frame, "TIMEOUT"
                ))
                # Receiver state does not advance; later frames in this window
                # will be rejected as out of order.
                cumulative_ack = receiver_next - 1
            else:
                if frame == receiver_next:
                    receiver_next += 1
                    events.append(make_event(
                        f"✓ Frame {frame} received in order", frame, "RECEIVED"
                    ))
                elif frame < receiver_next:
                    events.append(make_event(
                        f"↻ Duplicate Frame {frame} received; already accepted",
                        frame, "RECEIVED"
                    ))
                else:
                    events.append(make_event(
                        f"✗ Frame {frame} discarded: waiting for Frame {receiver_next}",
                        frame, "OUT OF ORDER"
                    ))
                cumulative_ack = receiver_next - 1

            # Receiver sends a cumulative ACK for its latest in-order frame.
            if cumulative_ack >= 0:
                if _lost(ack_loss):
                    events.append(make_event(
                        f"✗ ACK {cumulative_ack} lost", cumulative_ack, "ACK LOST"
                    ))
                    events.append(make_event(
                        f"Timeout waiting for cumulative ACK {cumulative_ack}",
                        frame, "TIMEOUT"
                    ))
                else:
                    events.append(make_event(
                        f"← ACK {cumulative_ack} received (cumulative)",
                        cumulative_ack, "ACK RECEIVED"
                    ))
                    best_cumulative_ack = max(best_cumulative_ack, cumulative_ack)

        # Only a successfully received cumulative ACK can move the sender base.
        if best_cumulative_ack >= base:
            base = max(base, best_cumulative_ack + 1)

        if base == base_before_round and base < total_frames:
            outstanding = list(range(base, window_end))
            events.append(make_event(
                f"Timeout: retransmitting outstanding frames from Frame {base}: {outstanding}",
                base, "TIMEOUT"
            ))
        elif base < total_frames:
            events.append(make_event(
                f"Window slides forward; new Sender Window starts at Frame {base}",
                base, "INFO"
            ))

    delivered = receiver_next
    if base < total_frames:
        events.append(make_event(
            "Simulation stopped because the retry limit was reached; some frames remain unacknowledged.",
            status="ERROR"
        ))
    else:
        events.append(make_event("Simulation completed successfully.", status="COMPLETE"))

    summary = make_summary(total_frames, total_sent, retransmissions, delivered, "Go-Back-N")
    events[-1]["summary"] = summary
    return events, summary


def simulate_selective_repeat(total_frames, window_size, packet_loss, ack_loss):
    """Selective Repeat: the receiver buffers out-of-order frames. The sender
    retransmits only frames whose ACK has not successfully reached the sender.
    """
    events = [make_event(
        f"Starting Selective Repeat simulation | Frames={total_frames}, Window={window_size}"
    )]
    acknowledged = set()  # ACKs successfully received by the sender.
    received = set()      # Frames received/buffered by the receiver.
    attempts_by_frame = [0] * total_frames
    total_sent = 0
    retransmissions = 0
    max_attempts = max(1000, total_frames * 1000)
    attempts = 0

    while len(acknowledged) < total_frames and attempts < max_attempts:
        # The sender window is anchored at the first frame not yet ACKed.
        base = 0
        while base < total_frames and base in acknowledged:
            base += 1
        if base >= total_frames:
            break

        window_end = min(base + window_size, total_frames)
        window_positions = list(range(base, window_end))
        pending = [frame for frame in window_positions if frame not in acknowledged]
        events.append(make_event(f"Sender Window: {window_positions}"))
        events.append(make_event(f"Unacknowledged Frames: {pending}"))

        for frame in pending:
            if attempts >= max_attempts:
                break
            if frame in acknowledged:
                continue

            attempts += 1
            if attempts_by_frame[frame] > 0:
                retransmissions += 1
            attempts_by_frame[frame] += 1
            total_sent += 1
            # Repeat the current window near each transmission/loss so it
            # remains visible in the event log while the animation scrolls.
            events.append(make_event(
                f"Current Sender Window: {window_positions}", frame, "INFO"
            ))
            events.append(make_event(f"Sending Frame {frame}...", frame, "TRANSMITTING"))

            if _lost(packet_loss):
                events.append(make_event(
                    f"✗ Frame {frame} lost in network", frame, "PACKET LOST"
                ))
                events.append(make_event(
                    f"Timeout for Frame {frame} → only Frame {frame} needs retransmission",
                    frame, "TIMEOUT"
                ))
                continue

            if frame in received:
                events.append(make_event(
                    f"↻ Duplicate Frame {frame} received; receiver already has it",
                    frame, "RECEIVED"
                ))
            else:
                received.add(frame)
                if all(previous in received for previous in range(frame)):
                    events.append(make_event(f"✓ Frame {frame} received", frame, "RECEIVED"))
                else:
                    events.append(make_event(
                        f"✓ Frame {frame} received and buffered (out of order)",
                        frame, "RECEIVED"
                    ))

            if _lost(ack_loss):
                events.append(make_event(f"✗ ACK {frame} lost", frame, "ACK LOST"))
                events.append(make_event(
                    f"Timeout for Frame {frame} → only Frame {frame} needs retransmission",
                    frame, "TIMEOUT"
                ))
            else:
                acknowledged.add(frame)
                events.append(make_event(f"← ACK {frame} received", frame, "ACK RECEIVED"))

        new_base = 0
        while new_base < total_frames and new_base in acknowledged:
            new_base += 1
        if new_base > base and new_base < total_frames:
            events.append(make_event(
                f"Window slides forward; new Sender Window starts at Frame {new_base}",
                new_base, "INFO"
            ))

    delivered = len(received)
    if len(acknowledged) < total_frames:
        events.append(make_event(
            "Simulation stopped because the retry limit was reached; some frames remain unacknowledged.",
            status="ERROR"
        ))
    else:
        events.append(make_event("Simulation completed successfully.", status="COMPLETE"))

    summary = make_summary(
        total_frames, total_sent, retransmissions, delivered, "Selective Repeat"
    )
    events[-1]["summary"] = summary
    return events, summary
