# ============================================================
# AMBULANCE ALLOCATION SYSTEM
# Redesigned Gradio Interface
# ============================================================

import gradio as gr
import pandas as pd
import time


# -------------------- HELPER FUNCTIONS --------------------

def format_timer(seconds):
    seconds = max(0, int(seconds))
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    return f"{minutes:02d}:{remaining_seconds:02d}"


def get_fleet_display():
    display_df = fleet_state.copy()

    display_df["Status"] = display_df["available"].map({
        1: "🟢 Available",
        0: "🟠 Busy"
    })

    return display_df[
        ["ambulance_id", "location", "Status"]
    ].rename(columns={
        "ambulance_id": "Ambulance ID",
        "location": "Current Location"
    })


def get_fleet_stats():
    total = len(fleet_state)
    available = int(fleet_state["available"].sum())
    busy = total - available

    return f"""
    <div class="stats-container">

        <div class="stat-card">
            <div class="stat-icon blue">🚑</div>
            <div class="stat-number">{total}</div>
            <div class="stat-label">TOTAL AMBULANCES</div>
        </div>

        <div class="stat-card">
            <div class="stat-icon green">✓</div>
            <div class="stat-number green-text">{available}</div>
            <div class="stat-label">AVAILABLE</div>
        </div>

        <div class="stat-card">
            <div class="stat-icon orange">↗</div>
            <div class="stat-number orange-text">{busy}</div>
            <div class="stat-label">BUSY / DISPATCHED</div>
        </div>

    </div>
    """


def get_progress_html(progress):
    percentage = min(100, max(0, int(progress * 100)))

    return f"""
    <div class="progress-container">
        <div class="progress-heading">
            <span>Journey Progress</span>
            <strong>{percentage}%</strong>
        </div>
        <div class="progress-track">
            <div class="progress-fill" style="width:{percentage}%"></div>
        </div>
    </div>
    """


def get_priority_label(severity):
    return {
        "Critical": "🔴 CRITICAL",
        "High": "🟠 HIGH",
        "Medium": "🟡 MEDIUM",
        "Low": "🟢 LOW"
    }.get(severity, severity)


def get_candidate_display(result):
    if result is None or result.empty:
        return pd.DataFrame(columns=[
            "Ambulance",
            "Location",
            "Distance (km)",
            "Predicted ETA (min)",
            "AI Score"
        ])

    display = result[
        [
            "ambulance_id",
            "ambulance_location",
            "distance_km",
            "predicted_response_time",
            "allocation_score"
        ]
    ].copy()

    display.columns = [
        "Ambulance",
        "Location",
        "Distance (km)",
        "Predicted ETA (min)",
        "AI Score"
    ]

    return display.round(2)


# -------------------- DISPATCH FUNCTION --------------------

def dispatch_request(
    emergency_location,
    emergency_type,
    severity,
    traffic,
    weather,
    current_tracking
):
    global fleet_state

    # Prevent accidental overlapping dispatches in this demo.
    if current_tracking and current_tracking.get("active"):
        return (
            "🟠 DISPATCH ALREADY ACTIVE",
            current_tracking["ambulance_id"],
            "An active dispatch is in progress.",
            "N/A", "N/A",
            get_fleet_display(),
            get_fleet_stats(),
            gr.update(),
            current_tracking,
            "An ambulance is already responding to an emergency.",
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update()
        )

    result = allocate_ambulance(
        emergency_location,
        emergency_type,
        severity,
        int(traffic),
        weather
    )

    if result is None or result.empty:
        return (
            "🔴 NO AMBULANCE AVAILABLE",
            "None",
            get_priority_label(severity),
            "N/A",
            "N/A",
            get_fleet_display(),
            get_fleet_stats(),
            create_tracking_map(
                emergency_location,
                "A-01",
                0,
                "NO AVAILABLE AMBULANCE"
            ),
            None,
            f"""
### No ambulance available

**Emergency location:** {emergency_location}

The system could not find an available ambulance.
Please check fleet availability.
""",
            "00:00",
            "Waiting",
            get_progress_html(0),
            get_candidate_display(result)
        )

    best = result.iloc[0]

    ambulance_id = best["ambulance_id"]
    ambulance_location = best["ambulance_location"]
    predicted_eta = float(best["predicted_response_time"])
    distance = float(best["distance_km"])

    selected_index = fleet_state.index[
        fleet_state["ambulance_id"] == ambulance_id
    ][0]

    fleet_state.loc[selected_index, "available"] = 0

    # One-minute demonstration journey.
    demo_duration = 60

    tracking_state = {
        "active": True,
        "ambulance_id": ambulance_id,
        "emergency_location": emergency_location,
        "start_time": time.time(),
        "duration": demo_duration,
        "total_distance": distance,
        "predicted_eta": predicted_eta
    }

    timeline = f"""
### 📡 Dispatch Timeline

<text>Emergency received</text>

🟢 **Emergency registered**

📍 Location: {emergency_location}

↓

🧠 **AI allocation completed**

🚑 Selected ambulance: {ambulance_id}

↓

🟠 **Ambulance dispatched**

📍 Starting location: {ambulance_location}

↓

🚑 **EN ROUTE**

⏱️ AI predicted response time: {predicted_eta:.2f} minutes
"""

    return (
        "🟠 AMBULANCE DISPATCHED",
        f"🚑 {ambulance_id}",
        get_priority_label(severity),
        f"{distance:.2f} km",
        f"{predicted_eta:.2f} min",
        get_fleet_display(),
        get_fleet_stats(),
        create_tracking_map(
            emergency_location,
            ambulance_id,
            0,
            "DISPATCHED"
        ),
        tracking_state,
        timeline,
        format_timer(demo_duration),
        f"{distance:.2f} km",
        get_progress_html(0),
        get_candidate_display(result)
    )


# -------------------- LIVE TRACKING --------------------

def update_tracking(tracking_state):
    global fleet_state

    if not tracking_state or not tracking_state.get("active"):
        return (
            gr.update(),
            "🟢 SYSTEM READY",
            "00:00",
            "Waiting for dispatch",
            get_progress_html(0),
            get_fleet_display(),
            get_fleet_stats(),
            tracking_state,
            gr.update()
        )

    elapsed = time.time() - tracking_state["start_time"]
    duration = tracking_state["duration"]

    progress = min(elapsed / duration, 1.0)

    remaining_seconds = max(0, duration - elapsed)

    ambulance_id = tracking_state["ambulance_id"]
    emergency_location = tracking_state["emergency_location"]

    remaining_distance = (
        tracking_state["total_distance"] * (1 - progress)
    )

    if progress >= 1:

        status = "🟢 ARRIVED"

        selected_index = fleet_state.index[
            fleet_state["ambulance_id"] == ambulance_id
        ][0]

        fleet_state.loc[selected_index, "available"] = 1

        tracking_state["active"] = False

        timeline = f"""
### 📡 Dispatch Completed

🟢 Emergency received

↓

🧠 AI allocation completed

↓

🚑 **{ambulance_id} dispatched**

↓

🟠 EN ROUTE

↓

🟢 **ARRIVED AT {emergency_location}**

**The simulated demonstration journey is complete.**
"""

        remaining_distance = 0

    elif progress >= 0.85:

        status = "🟡 ARRIVING"

        timeline = f"""
### 📡 Live Dispatch Status

🚑 **{ambulance_id} — ARRIVING**

📍 Destination: {emergency_location}

📊 Journey completed: **{progress * 100:.0f}%**

📏 Remaining distance: **{remaining_distance:.2f} km**
"""

    else:

        status = "🟠 EN ROUTE"

        timeline = f"""
### 📡 Live Dispatch Status

🚑 **{ambulance_id} — EN ROUTE**

📍 Destination: {emergency_location}

📊 Journey completed: **{progress * 100:.0f}%**

📏 Remaining distance: **{remaining_distance:.2f} km**
"""

    map_html = create_tracking_map(
        emergency_location,
        ambulance_id,
        progress,
        status
    )

    return (
        map_html,
        status,
        format_timer(remaining_seconds),
        f"{remaining_distance:.2f} km",
        get_progress_html(progress),
        get_fleet_display(),
        get_fleet_stats(),
        tracking_state,
        timeline
    )


# -------------------- RESET FUNCTION --------------------

def reset_system():
    global fleet_state

    fleet_state["available"] = 1

    return (
        "🟢 SYSTEM READY",
        "No ambulance dispatched",
        "Awaiting emergency",
        "N/A",
        "N/A",
        get_fleet_display(),
        get_fleet_stats(),
        create_tracking_map(
            "F-8",
            "A-01",
            0,
            "AVAILABLE"
        ),
        None,
        """
### 📡 Dispatch Timeline

System reset successfully.

Waiting for a new emergency request.
""",
        "00:00",
        "Waiting",
        get_progress_html(0),
        get_candidate_display(None)
    )


# ============================================================
# PROFESSIONAL DASHBOARD CSS
# ============================================================

css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

.gradio-container {
    max-width: 1500px !important;
    margin: auto !important;
    font-family: 'Inter', sans-serif !important;
    background: #F3F6FA !important;
}

body {
    background: #F3F6FA !important;
}

/* Header */

.dashboard-header {
    background: linear-gradient(120deg, #142B45, #203F60);
    padding: 27px 32px;
    border-radius: 15px;
    color: white;
    margin-bottom: 20px;
    border-bottom: 4px solid #D93636;
}

.header-title {
    font-size: 29px;
    font-weight: 800;
    letter-spacing: -0.7px;
}

.header-subtitle {
    color: #C8D5E3;
    font-size: 13px;
    margin-top: 7px;
}

.header-status {
    background: #174D3A;
    color: #A7F3C5;
    padding: 7px 13px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
}

/* Section headings */

.section-heading {
    color: #142B45;
    font-size: 19px;
    font-weight: 800;
    margin: 8px 0 12px 0;
}

/* Cards */

.panel {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 13px;
    padding: 19px;
    box-shadow: 0 3px 12px rgba(25, 45, 70, 0.04);
}

/* Statistics */

.stats-container {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
    margin-bottom: 18px;
}

.stat-card {
    background: white;
    border: 1px solid #E3E9F0;
    border-radius: 12px;
    padding: 17px;
    min-height: 115px;
}

.stat-icon {
    width: 32px;
    height: 32px;
    border-radius: 9px;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 17px;
}

.blue {
    background: #E7F0FC;
    color: #2863A8;
}

.green {
    background: #E5F6ED;
    color: #188653;
}

.orange {
    background: #FFF0DF;
    color: #D47B20;
}

.stat-number {
    font-size: 29px;
    font-weight: 800;
    color: #142B45;
    margin-top: 7px;
}

.green-text {
    color: #188653;
}

.orange-text {
    color: #D47B20;
}

.stat-label {
    font-size: 10px;
    font-weight: 700;
    color: #718096;
    letter-spacing: 0.5px;
    margin-top: 3px;
}

/* Buttons */

.dispatch-button {
    min-height: 55px !important;
    background: #D93636 !important;
    color: white !important;
    border: none !important;
    font-weight: 800 !important;
    font-size: 15px !important;
    border-radius: 9px !important;
    transition: 0.2s ease !important;
}

.dispatch-button:hover {
    background: #B92727 !important;
}

.reset-button {
    min-height: 43px !important;
    border-radius: 9px !important;
}

/* Input fields */

label {
    color: #34465B !important;
    font-weight: 600 !important;
}

input, textarea {
    border-radius: 8px !important;
}

/* Tracking */

.timer-box input {
    font-size: 35px !important;
    font-weight: 800 !important;
    color: #D93636 !important;
    text-align: center !important;
    background: #FFF5F5 !important;
    border: 1px solid #F5D3D3 !important;
}

.progress-container {
    background: white;
    padding: 15px;
    border: 1px solid #E3E9F0;
    border-radius: 11px;
    margin-top: 12px;
}

.progress-heading {
    display: flex;
    justify-content: space-between;
    color: #34465B;
    font-size: 13px;
    margin-bottom: 10px;
}

.progress-heading strong {
    color: #D93636;
}

.progress-track {
    height: 11px;
    background: #E8EDF3;
    border-radius: 20px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #D93636, #F07858);
    border-radius: 20px;
    transition: width 0.5s ease;
}

/* Tables */

table {
    border-radius: 8px !important;
}

/* Timeline */

.timeline-panel {
    background: #172B3D !important;
    border: 1px solid #2F4B63 !important;
    border-left: 5px solid #D93636 !important;
    padding: 22px !important;
    border-radius: 12px !important;
    color: #FFFFFF !important;
}

.timeline-panel *,
.timeline-panel h1,
.timeline-panel h2,
.timeline-panel h3,
.timeline-panel h4,
.timeline-panel p,
.timeline-panel strong,
.timeline-panel span,
.timeline-panel li {
    color: #FFFFFF !important;
}

.timeline-panel h3 {
    color: #FFFFFF !important;
    font-size: 19px !important;
    font-weight: 800 !important;
    margin-top: 0 !important;
}

.timeline-panel p {
    color: #E8EEF5 !important;
    font-size: 14px !important;
    line-height: 1.7 !important;
}

.timeline-panel strong {
    color: #FFFFFF !important;
}

.timeline-panel code {
    color: #FFFFFF !important;
    background: #263E54 !important;
}

/* Global text contrast */

.gradio-container .prose,
.gradio-container .prose p,
.gradio-container .prose li,
.gradio-container .prose strong,
.gradio-container .prose h1,
.gradio-container .prose h2,
.gradio-container .prose h3,
.gradio-container .prose h4 {
    color: #243447 !important;
}

.gradio-container .prose h2,
.gradio-container .prose h3 {
    color: #142B45 !important;
}

/* Footer */

.footer {
    text-align: center;
    color: #718096;
    font-size: 11px;
    padding: 20px;
    border-top: 1px solid #E2E8F0;
    margin-top: 20px;
}

@media(max-width: 768px) {
    .dashboard-header {
        padding: 20px;
    }

    .header-title {
        font-size: 21px;
    }

    .stats-container {
        grid-template-columns: 1fr;
    }
}
"""


# ============================================================
# GRADIO APPLICATION
# ============================================================

with gr.Blocks(
    title="Ambulance Allocation System",
    theme=gr.themes.Soft(
        primary_hue="red",
        secondary_hue="blue",
        neutral_hue="slate"
    ),
    css=css
) as app:

    tracking_state = gr.State(None)

    # HEADER

    gr.HTML("""
    <div class="dashboard-header">
        <div style="display:flex; justify-content:space-between;
                    align-items:center; flex-wrap:wrap; gap:15px;">

            <div>
                <div class="header-title">
                    🚑 Ambulance Allocation System
                </div>

                <div class="header-subtitle">
                    AI-Powered Emergency Response, Intelligent Allocation
                    & Simulated Live Tracking
                </div>
            </div>

            <div class="header-status">
                ● SYSTEM ONLINE
            </div>

        </div>
    </div>
    """)

    # FLEET STATISTICS

    gr.HTML('<div class="section-heading">📊 Fleet Overview</div>')

    fleet_stats = gr.HTML(value=get_fleet_stats())

    # MAIN DASHBOARD

    with gr.Row(equal_height=False):

        # LEFT: EMERGENCY FORM

        with gr.Column(scale=1, min_width=290):

            with gr.Group(elem_classes="panel"):

                gr.Markdown("## 🚨 Emergency Request")

                gr.Markdown(
                    "Enter the emergency details to initiate "
                    "AI-based ambulance allocation."
                )

                emergency_location = gr.Dropdown(
                    choices=locations,
                    value="F-8",
                    label="📍 Emergency Location",
                    interactive=True
                )

                emergency_type = gr.Dropdown(
                    choices=EMERGENCY_TYPES,
                    value="Accident",
                    label="Emergency Type"
                )

                severity = gr.Dropdown(
                    choices=SEVERITY_LEVELS,
                    value="Critical",
                    label="⚠️ Emergency Severity"
                )

                traffic = gr.Slider(
                    minimum=1,
                    maximum=10,
                    value=7,
                    step=1,
                    label="🚦 Traffic Level",
                    info="1 = Low traffic, 10 = Heavy traffic"
                )

                weather = gr.Dropdown(
                    choices=WEATHER_CONDITIONS,
                    value="Clear",
                    label="🌦️ Weather Conditions"
                )

                dispatch_button = gr.Button(
                    "🚑 DISPATCH BEST AMBULANCE",
                    variant="primary",
                    elem_classes="dispatch-button"
                )

                reset_button = gr.Button(
                    "↻ Reset Dashboard",
                    variant="secondary",
                    elem_classes="reset-button"
                )

        # RIGHT: AI DISPATCH RESULTS

        with gr.Column(scale=2, min_width=400):

            with gr.Group(elem_classes="panel"):

                gr.Markdown("## 🧠 AI Dispatch Decision")

                status = gr.Textbox(
                    label="Dispatch Status",
                    value="🟢 SYSTEM READY",
                    interactive=False
                )

                with gr.Row():

                    selected_ambulance = gr.Textbox(
                        label="Selected Ambulance",
                        value="Not assigned",
                        interactive=False
                    )

                    priority = gr.Textbox(
                        label="Emergency Priority",
                        value="Awaiting request",
                        interactive=False
                    )

                with gr.Row():

                    distance_display = gr.Textbox(
                        label="Distance",
                        value="N/A",
                        interactive=False
                    )

                    eta_display = gr.Textbox(
                        label="AI Predicted ETA",
                        value="N/A",
                        interactive=False
                    )

            with gr.Group(elem_classes="panel"):

                gr.Markdown("## 🗺️ Ambulance Tracking")

                map_output = gr.HTML(
                    value=create_tracking_map(
                        "F-8",
                        "A-01",
                        0,
                        "AVAILABLE"
                    )
                )

                countdown = gr.Textbox(
                    label="⏱️ Estimated Demo Time Remaining",
                    value="00:00",
                    interactive=False,
                    elem_classes="timer-box"
                )

                remaining_distance = gr.Textbox(
                    label="📏 Remaining Distance",
                    value="Waiting for dispatch",
                    interactive=False
                )

                progress_display = gr.HTML(
                    value=get_progress_html(0)
                )

    # FLEET TABLE

    gr.Markdown("## 🚑 Ambulance Fleet")

    fleet_table = gr.Dataframe(
        value=get_fleet_display(),
        interactive=False,
        label="Current Fleet Availability",
        wrap=True
    )

    # AI CANDIDATE TABLE

    gr.Markdown("## 🧠 AI Allocation Results")

    candidate_table = gr.Dataframe(
        value=get_candidate_display(None),
        interactive=False,
        label="Ambulance Candidate Comparison",
        wrap=True
    )

    # DISPATCH TIMELINE

    gr.Markdown("## 📡 Dispatch Activity")

    timeline = gr.Markdown(
        """
### Waiting for Emergency Request

The dispatch timeline will appear here when an emergency is submitted.
""",
        elem_classes="timeline-panel"
    )

    # FOOTER

    gr.HTML("""
    <div class="footer">
        <b>AMBULANCE ALLOCATION SYSTEM</b><br>
        AI-Based Ambulance Allocation & Emergency Response Prototype<br>
        Tracking is simulated for academic demonstration.
        Real-world deployment requires verified GPS, routing and
        emergency-service integration.
    </div>
    """)

    # AUTOMATIC TRACKING UPDATES

    timer = gr.Timer(
        value=1,
        active=True
    )

    # DISPATCH EVENT

    dispatch_button.click(
        fn=dispatch_request,
        inputs=[
            emergency_location,
            emergency_type,
            severity,
            traffic,
            weather,
            tracking_state
        ],
        outputs=[
            status,
            selected_ambulance,
            priority,
            distance_display,
            eta_display,
            fleet_table,
            fleet_stats,
            map_output,
            tracking_state,
            timeline,
            countdown,
            remaining_distance,
            progress_display,
            candidate_table
        ]
    )

    # TIMER EVENT

    timer.tick(
        fn=update_tracking,
        inputs=[tracking_state],
        outputs=[
            map_output,
            status,
            countdown,
            remaining_distance,
            progress_display,
            fleet_table,
            fleet_stats,
            tracking_state,
            timeline
        ]
    )

    # RESET EVENT

    reset_button.click(
        fn=reset_system,
        inputs=[],
        outputs=[
            status,
            selected_ambulance,
            priority,
            distance_display,
            eta_display,
            fleet_table,
            fleet_stats,
            map_output,
            tracking_state,
            timeline,
            countdown,
            remaining_distance,
            progress_display,
            candidate_table
        ]
    )


# ============================================================
# LAUNCH
# ============================================================

app.launch(share=True)