import tkinter as tk
from tkinter import ttk, messagebox

from protocol import simulate


# =========================================================
# COLORS
# =========================================================

BG = "#1e1e1e"
PANEL = "#252526"
PANEL_2 = "#2d2d30"

FG = "#f5f5f5"
MUTED = "#bdbdbd"

SUCCESS = "#66d17a"
ERROR = "#ff6b6b"
WARNING = "#ffd166"
ACCENT = "#4aa3ff"


# =========================================================
# MAIN WINDOW
# =========================================================

root = tk.Tk()

root.title("Sliding Window Protocol Simulator")
root.geometry("1000x720")
root.minsize(900, 650)
root.configure(bg=BG)


# =========================================================
# VARIABLES
# =========================================================

protocol_var = tk.StringVar(value="Go-Back-N")
frames_var = tk.StringVar(value="10")
window_var = tk.StringVar(value="4")
packet_loss_var = tk.StringVar(value="20")
ack_loss_var = tk.StringVar(value="10")
speed_var = tk.StringVar(value="Normal")

current_frame_var = tk.StringVar(value="-")
current_status_var = tk.StringVar(value="Ready")
stats_var = tk.StringVar(value="Ready to start simulation")


# =========================================================
# SIMULATION STATE
# =========================================================

running = False
events = []
event_index = 0

# ID returned by root.after()
# This allows STOP and RESET to cancel the animation.
after_id = None


# =========================================================
# WINDOW CLOSE
# =========================================================

def close_app():
    global running, after_id

    if after_id is not None:
        try:
            root.after_cancel(after_id)
        except tk.TclError:
            pass

        after_id = None

    running = False
    root.destroy()


root.protocol("WM_DELETE_WINDOW", close_app)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def write_log(text):
    log_text.config(state="normal")

    log_text.insert("end", text + "\n")

    log_text.see("end")

    log_text.config(state="disabled")


def set_inputs_enabled(enabled):

    state = "normal" if enabled else "disabled"

    protocol_combo.config(state="readonly" if enabled else "disabled")

    frames_entry.config(state=state)
    window_entry.config(state=state)
    packet_loss_entry.config(state=state)
    ack_loss_entry.config(state=state)

    speed_combo.config(state="readonly" if enabled else "disabled")


def get_delay():

    speed = speed_var.get()

    if speed == "Slow":
        return 1000

    if speed == "Fast":
        return 250

    return 550


def clear_log():

    log_text.config(state="normal")
    log_text.delete("1.0", "end")
    log_text.config(state="disabled")


# =========================================================
# NETWORK VISUALIZATION
# =========================================================

def draw_network(frame=None, status="Ready"):

    network_canvas.delete("all")

    width = network_canvas.winfo_width()

    if width < 100:
        width = 900

    # Sender and Receiver boxes
    sender_x = 170
    receiver_x = width - 170
    center_x = width / 2

    box_top = 45
    box_bottom = 115

    # Sender
    network_canvas.create_rectangle(
        sender_x - 70,
        box_top,
        sender_x + 70,
        box_bottom,
        fill=PANEL_2,
        outline=ACCENT,
        width=2
    )

    network_canvas.create_text(
        sender_x,
        80,
        text="SENDER",
        fill=FG,
        font=("Arial", 14, "bold")
    )

    # Receiver
    network_canvas.create_rectangle(
        receiver_x - 70,
        box_top,
        receiver_x + 70,
        box_bottom,
        fill=PANEL_2,
        outline=SUCCESS,
        width=2
    )

    network_canvas.create_text(
        receiver_x,
        80,
        text="RECEIVER",
        fill=FG,
        font=("Arial", 14, "bold")
    )

    # Data channel
    data_y = 175

    network_canvas.create_line(
        sender_x + 75,
        data_y,
        receiver_x - 75,
        data_y,
        fill=ACCENT,
        width=3,
        arrow=tk.LAST
    )

    network_canvas.create_text(
        center_x,
        data_y - 18,
        text="DATA",
        fill=ACCENT,
        font=("Arial", 11, "bold")
    )

    # ACK channel
    ack_y = 250

    network_canvas.create_line(
        receiver_x - 75,
        ack_y,
        sender_x + 75,
        ack_y,
        fill=SUCCESS,
        width=3,
        arrow=tk.LAST
    )

    network_canvas.create_text(
        center_x,
        ack_y + 18,
        text="ACK",
        fill=SUCCESS,
        font=("Arial", 11, "bold")
    )

    # Current frame
    if frame is not None:

        if status in ("PACKET LOST", "ACK LOST", "TIMEOUT", "ERROR"):
            frame_color = ERROR

        elif status in ("RECEIVED", "ACK RECEIVED", "COMPLETE"):
            frame_color = SUCCESS

        elif status == "TRANSMITTING":
            frame_color = WARNING

        else:
            frame_color = ACCENT

        network_canvas.create_oval(
            center_x - 32,
            data_y - 32,
            center_x + 32,
            data_y + 32,
            fill=frame_color,
            outline=""
        )

        network_canvas.create_text(
            center_x,
            data_y,
            text=f"F{frame}",
            fill="#111111",
            font=("Arial", 12, "bold")
        )

    # Status
    network_canvas.create_text(
        center_x,
        305,
        text=status,
        fill=FG,
        font=("Arial", 12, "bold")
    )


# =========================================================
# START SIMULATION
# =========================================================

def start_simulation():

    global running
    global events
    global event_index
    global after_id

    if running:
        return

    # -----------------------------------------------------
    # Validate inputs
    # -----------------------------------------------------

    try:
        total_frames = int(frames_var.get())
        window_size = int(window_var.get())
        packet_loss = int(packet_loss_var.get())
        ack_loss = int(ack_loss_var.get())

    except ValueError:

        messagebox.showerror(
            "Invalid Input",
            "Please enter valid numeric values."
        )

        return

    if total_frames < 1 or total_frames > 100:

        messagebox.showerror(
            "Invalid Frames",
            "Number of frames must be between 1 and 100."
        )

        return

    if window_size < 1 or window_size > total_frames:

        messagebox.showerror(
            "Invalid Window Size",
            "Window size must be between 1 and the number of frames."
        )

        return

    if packet_loss < 0 or packet_loss > 99:

        messagebox.showerror(
            "Invalid Packet Loss",
            "Packet loss must be between 0 and 99%."
        )

        return

    if ack_loss < 0 or ack_loss > 99:

        messagebox.showerror(
            "Invalid ACK Loss",
            "ACK loss must be between 0 and 99%."
        )

        return

    # -----------------------------------------------------
    # Generate simulation
    # -----------------------------------------------------

    events, summary = simulate(
        protocol_var.get(),
        total_frames,
        window_size,
        packet_loss,
        ack_loss
    )

    event_index = 0
    after_id = None
    running = True

    # -----------------------------------------------------
    # Disable input controls
    # -----------------------------------------------------

    set_inputs_enabled(False)

    start_button.config(state="disabled")

    # RESET stays enabled while running
    reset_button.config(state="normal")

    # STOP becomes available
    stop_button.config(state="normal")

    # -----------------------------------------------------
    # Reset display
    # -----------------------------------------------------

    clear_log()

    current_frame_var.set("-")
    current_status_var.set("Running")

    stats_var.set("Simulation running...")

    draw_network()

    write_log("=" * 70)
    write_log(
        f"PROTOCOL: {protocol_var.get()}"
    )
    write_log(
        f"FRAMES: {total_frames} | "
        f"WINDOW SIZE: {window_size}"
    )
    write_log(
        f"PACKET LOSS: {packet_loss}% | "
        f"ACK LOSS: {ack_loss}%"
    )
    write_log("=" * 70)

    # Start animation
    animate_next()


# =========================================================
# ANIMATE NEXT EVENT
# =========================================================

def animate_next():

    global running
    global event_index
    global after_id

    if not running:
        return

    # -----------------------------------------------------
    # Simulation finished
    # -----------------------------------------------------

    if event_index >= len(events):

        running = False
        after_id = None

        start_button.config(state="normal")
        reset_button.config(state="normal")
        stop_button.config(state="disabled")

        set_inputs_enabled(True)

        if events:

            summary = events[-1].get("summary")

            if summary:

                total = summary["total_frames"]
                delivered = summary["delivered"]
                sent = summary["total_sent"]
                retransmissions = summary["retransmissions"]

                stats_var.set(
                    f"Delivered: {delivered}/{total}    |    "
                    f"Total Sent: {sent}    |    "
                    f"Retransmissions: {retransmissions}"
                )

        current_status_var.set("Complete")

        write_log("=" * 70)
        write_log("SIMULATION COMPLETE")
        write_log("=" * 70)

        draw_network(
            current_frame_var.get()
            if current_frame_var.get() != "-"
            else None,
            "COMPLETE"
        )

        return

    # -----------------------------------------------------
    # Get current event
    # -----------------------------------------------------

    event = events[event_index]

    message = event["message"]
    frame = event.get("frame")
    status = event.get("status", "INFO")

    # -----------------------------------------------------
    # Update log
    # -----------------------------------------------------

    write_log(message)

    # -----------------------------------------------------
    # Update visualization
    # -----------------------------------------------------

    if frame is not None:

        current_frame_var.set(str(frame))

    current_status_var.set(status)

    draw_network(frame, status)

    # -----------------------------------------------------
    # Move to next event
    # -----------------------------------------------------

    event_index += 1

    # -----------------------------------------------------
    # Schedule next animation
    #
    # IMPORTANT:
    # Store the ID returned by root.after().
    # STOP and RESET use this ID to cancel the callback.
    # -----------------------------------------------------

    delay = get_delay()

    after_id = root.after(
        delay,
        animate_next
    )


# =========================================================
# STOP SIMULATION
# =========================================================

def stop_simulation():

    global running
    global after_id

    if not running:
        return

    # Cancel the scheduled animation callback
    if after_id is not None:

        try:
            root.after_cancel(after_id)

        except tk.TclError:
            pass

        after_id = None

    running = False

    # Restore controls
    start_button.config(state="normal")
    reset_button.config(state="normal")
    stop_button.config(state="disabled")

    set_inputs_enabled(True)

    current_status_var.set("Stopped")

    stats_var.set("Simulation stopped")

    write_log("-" * 70)
    write_log("SIMULATION STOPPED BY USER")
    write_log("-" * 70)

    draw_network(
        current_frame_var.get()
        if current_frame_var.get() != "-"
        else None,
        "STOPPED"
    )


# =========================================================
# RESET SIMULATION
# =========================================================

def reset_simulation():

    global running
    global events
    global event_index
    global after_id

    # -----------------------------------------------------
    # Cancel scheduled animation
    # -----------------------------------------------------

    if after_id is not None:

        try:
            root.after_cancel(after_id)

        except tk.TclError:
            pass

        after_id = None

    # -----------------------------------------------------
    # Reset simulation state
    # -----------------------------------------------------

    running = False
    events = []
    event_index = 0

    # -----------------------------------------------------
    # Restore default values
    # -----------------------------------------------------

    protocol_var.set("Go-Back-N")
    frames_var.set("10")
    window_var.set("4")
    packet_loss_var.set("20")
    ack_loss_var.set("10")
    speed_var.set("Normal")

    # -----------------------------------------------------
    # Clear display
    # -----------------------------------------------------

    current_frame_var.set("-")
    current_status_var.set("Ready")

    stats_var.set("Ready to start simulation")

    clear_log()

    write_log("Simulation reset.")
    write_log("Configure the settings and press START.")

    draw_network()

    # -----------------------------------------------------
    # Restore buttons and inputs
    # -----------------------------------------------------

    start_button.config(state="normal")
    reset_button.config(state="normal")
    stop_button.config(state="disabled")

    set_inputs_enabled(True)


# =========================================================
# MAIN TITLE
# =========================================================

title_frame = tk.Frame(
    root,
    bg=BG
)

title_frame.pack(
    fill="x",
    padx=25,
    pady=(18, 5)
)

title_label = tk.Label(
    title_frame,
    text="SLIDING WINDOW PROTOCOL SIMULATOR",
    font=("Arial", 22, "bold"),
    bg=BG,
    fg=FG
)

title_label.pack()

subtitle_label = tk.Label(
    title_frame,
    text="Go-Back-N & Selective Repeat",
    font=("Arial", 12),
    bg=BG,
    fg=MUTED
)

subtitle_label.pack(
    pady=(2, 0)
)


# =========================================================
# SETTINGS PANEL
# =========================================================

settings_frame = tk.LabelFrame(
    root,
    text="  Simulation Settings  ",
    font=("Arial", 11, "bold"),
    bg=PANEL,
    fg=FG,
    bd=1,
    relief="groove"
)

settings_frame.pack(
    fill="x",
    padx=25,
    pady=10
)


# Protocol
tk.Label(
    settings_frame,
    text="Protocol",
    bg=PANEL,
    fg=FG,
    font=("Arial", 10)
).grid(
    row=0,
    column=0,
    padx=(15, 5),
    pady=12,
    sticky="w"
)

protocol_combo = ttk.Combobox(
    settings_frame,
    textvariable=protocol_var,
    values=["Go-Back-N", "Selective Repeat"],
    state="readonly",
    width=18
)

protocol_combo.grid(
    row=0,
    column=1,
    padx=5,
    pady=12
)


# Frames
tk.Label(
    settings_frame,
    text="Frames",
    bg=PANEL,
    fg=FG,
    font=("Arial", 10)
).grid(
    row=0,
    column=2,
    padx=(15, 5),
    pady=12
)

frames_entry = tk.Entry(
    settings_frame,
    textvariable=frames_var,
    width=8,
    bg=PANEL_2,
    fg=FG,
    insertbackground=FG,
    relief="flat"
)

frames_entry.grid(
    row=0,
    column=3,
    padx=5,
    pady=12
)


# Window size
tk.Label(
    settings_frame,
    text="Window Size",
    bg=PANEL,
    fg=FG,
    font=("Arial", 10)
).grid(
    row=0,
    column=4,
    padx=(15, 5),
    pady=12
)

window_entry = tk.Entry(
    settings_frame,
    textvariable=window_var,
    width=8,
    bg=PANEL_2,
    fg=FG,
    insertbackground=FG,
    relief="flat"
)

window_entry.grid(
    row=0,
    column=5,
    padx=5,
    pady=12
)


# Packet loss
tk.Label(
    settings_frame,
    text="Packet Loss %",
    bg=PANEL,
    fg=FG,
    font=("Arial", 10)
).grid(
    row=1,
    column=0,
    padx=(15, 5),
    pady=12
)

packet_loss_entry = tk.Entry(
    settings_frame,
    textvariable=packet_loss_var,
    width=8,
    bg=PANEL_2,
    fg=FG,
    insertbackground=FG,
    relief="flat"
)

packet_loss_entry.grid(
    row=1,
    column=1,
    padx=5,
    pady=12
)


# ACK loss
tk.Label(
    settings_frame,
    text="ACK Loss %",
    bg=PANEL,
    fg=FG,
    font=("Arial", 10)
).grid(
    row=1,
    column=2,
    padx=(15, 5),
    pady=12
)

ack_loss_entry = tk.Entry(
    settings_frame,
    textvariable=ack_loss_var,
    width=8,
    bg=PANEL_2,
    fg=FG,
    insertbackground=FG,
    relief="flat"
)

ack_loss_entry.grid(
    row=1,
    column=3,
    padx=5,
    pady=12
)


# Speed
tk.Label(
    settings_frame,
    text="Animation Speed",
    bg=PANEL,
    fg=FG,
    font=("Arial", 10)
).grid(
    row=1,
    column=4,
    padx=(15, 5),
    pady=12
)

speed_combo = ttk.Combobox(
    settings_frame,
    textvariable=speed_var,
    values=["Slow", "Normal", "Fast"],
    state="readonly",
    width=10
)

speed_combo.grid(
    row=1,
    column=5,
    padx=5,
    pady=12
)


# =========================================================
# NETWORK VISUALIZATION
# =========================================================

network_frame = tk.LabelFrame(
    root,
    text="  Network Visualization  ",
    font=("Arial", 11, "bold"),
    bg=PANEL,
    fg=FG,
    bd=1,
    relief="groove"
)

network_frame.pack(
    fill="x",
    padx=25,
    pady=5
)

network_canvas = tk.Canvas(
    network_frame,
    height=330,
    bg=PANEL,
    highlightthickness=0
)

network_canvas.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=5
)


# =========================================================
# CURRENT FRAME / STATUS
# =========================================================

status_frame = tk.Frame(
    network_frame,
    bg=PANEL
)

status_frame.pack(
    fill="x",
    padx=15,
    pady=(0, 8)
)

tk.Label(
    status_frame,
    text="Current Frame:",
    bg=PANEL,
    fg=MUTED,
    font=("Arial", 10)
).pack(
    side="left"
)

tk.Label(
    status_frame,
    textvariable=current_frame_var,
    bg=PANEL,
    fg=ACCENT,
    font=("Arial", 10, "bold")
).pack(
    side="left",
    padx=(5, 25)
)

tk.Label(
    status_frame,
    text="Status:",
    bg=PANEL,
    fg=MUTED,
    font=("Arial", 10)
).pack(
    side="left"
)

tk.Label(
    status_frame,
    textvariable=current_status_var,
    bg=PANEL,
    fg=FG,
    font=("Arial", 10, "bold")
).pack(
    side="left",
    padx=5
)


# =========================================================
# EVENT LOG
# =========================================================

log_frame = tk.LabelFrame(
    root,
    text="  Simulation Event Log  ",
    font=("Arial", 11, "bold"),
    bg=PANEL,
    fg=FG,
    bd=1,
    relief="groove"
)

log_frame.pack(
    fill="both",
    expand=True,
    padx=25,
    pady=8
)


log_text = tk.Text(
    log_frame,
    height=8,
    bg="#181818",
    fg=FG,
    insertbackground=FG,
    font=("Courier New", 10),
    relief="flat",
    wrap="word",
    state="disabled"
)

log_text.pack(
    side="left",
    fill="both",
    expand=True,
    padx=(8, 0),
    pady=8
)


log_scrollbar = ttk.Scrollbar(
    log_frame,
    orient="vertical",
    command=log_text.yview
)

log_scrollbar.pack(
    side="right",
    fill="y",
    padx=(0, 8),
    pady=8
)

log_text.configure(
    yscrollcommand=log_scrollbar.set
)


# =========================================================
# STATS
# =========================================================

stats_label = tk.Label(
    root,
    textvariable=stats_var,
    bg=BG,
    fg=MUTED,
    font=("Arial", 10)
)

stats_label.pack(
    pady=(0, 5)
)


# =========================================================
# BUTTONS
# =========================================================

button_frame = tk.Frame(
    root,
    bg=BG
)

button_frame.pack(
    pady=(2, 15)
)


start_button = tk.Button(
    button_frame,
    text="START",
    font=("Arial", 12, "bold"),
    width=10,
    height=2,
    bg=ACCENT,
    fg="white",
    activebackground=ACCENT,
    activeforeground="white",
    relief="flat",
    cursor="hand2",
    command=start_simulation
)

start_button.pack(
    side="left",
    padx=8
)


reset_button = tk.Button(
    button_frame,
    text="RESET",
    font=("Arial", 12, "bold"),
    width=10,
    height=2,
    bg=PANEL_2,
    fg=FG,
    activebackground="#3a3a3d",
    activeforeground=FG,
    relief="flat",
    cursor="hand2",
    command=reset_simulation
)

reset_button.pack(
    side="left",
    padx=8
)


stop_button = tk.Button(
    button_frame,
    text="STOP",
    font=("Arial", 12, "bold"),
    width=10,
    height=2,
    bg=ERROR,
    fg="white",
    activebackground=ERROR,
    activeforeground="white",
    relief="flat",
    cursor="hand2",
    state="disabled",
    command=stop_simulation
)

stop_button.pack(
    side="left",
    padx=8
)


# =========================================================
# INITIAL DISPLAY
# =========================================================

write_log("Simulation ready.")
write_log("Configure the settings and press START.")

draw_network()


# =========================================================
# RUN APPLICATION
# =========================================================

root.mainloop()