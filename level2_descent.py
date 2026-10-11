import os
import sys
import time
import math
import csv

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

# ==================== TELEMETRY FLIGHT RECORDER ====================
class FlightRecorder:
    def __init__(self, filename="flight_telemetry.csv"):
        self.filename = filename
        self.records = []
        self.headers = [
            "time_s", "altitude_m", "velocity_mps, "accel_mps2",
            "mass_kg", "thrust_N", "q_pa", "drag_force_N", "throttle_pct", "phase"
        ]
        with open(self.filename, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(self.headers)

    def log(self, t, alt, vel, acc, mass, thrust, q, drag, throttle, phase):
        row = [
            round(t, 2), round(alt, 2), round(vel, 2), round(acc, 2),
            round(mass, 2), round(thrust, 2), round(q, 2), round(drag, 2),
            round(throttle, 1), phase
        ]
        self.records.append(row)
        with open(self.filename, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)

    def print_post_flight_summary(self, dt, outcome_str):
        if not self.records:
            return
        
        peak_alt = max(r[1] for r in self.records)
        peak_vel = max(abs(r[2]) for r in self.records)
        peak_acc = max(abs(r[3]) for r in self.records)
        peak_g = peak_acc / 9.81
        peak_q = max(r[6] for r in self.records)
        touchdown_v = self.records[-1][2]

        total_delta_v = sum((r[5] / r[4]) * dt for r in self.records)
        gravity_loss = sum(9.81 * dt for r in self.records if r[1] > 0)
        drag_loss = sum((abs(r[7]) / r[4]) * dt for r in self.records)

        print("\n" + "=" * 60)
        print(f"📊 FLIGHT OUTCOME: {outcome_str}")
        print("=" * 60)
        print(f"Touchdown velocity        : {touchdown_v:8.2f} m/s")
        print(f"Max Altitude (Apogee)     : {peak_alt:8.1f} m")
        print(f"Peak Speed Encountred     : {peak_vel:8.1f} m/s")
        print(f"Peak G-load               : {peak_g:8.2f} G")
        print(f"Peak Dynamic Preassure(q) : {peak_q:8.1f} Pa")
        print("-" * 60)
        print("DELTA-V & ENERGY ACCOUNTING:")
        print(f"  • Total Engine Δv Delivered: {total_delta_v:8.1f} m/s")
        print(f"  • Gravity Drag Losses      : {gravity_loss:8.1f} m/s")
        print(f"  • Aerodynamic Drag Losses  : {drag_loss:8.1f} m/s")
        print(f"\nTelemetry logged: {os.path.abspath(self.filename)}")
        print("=" * 60)

# ===================== AERODYNAMICS & ATMOSPHERE ENGINE ================================
class AtmosphereModel:
    RHO_0 = 1.225
    SCALE_HEIGHT = 8500.0
    SPEED_OF_SOUND = 340.0

    @classmethod
    def air_density(cls, altitude: float) -> float:
        if altitude < 0:
            return cls.RHO_0
        return cls.RHO_0 * math.exp(-altitude / cls.SCALE_HEIGHT)

    @classmethod
    def drag_coefficient(cls, mach: float, descending: bool = False) -> float:
        base_cd = 0.35 if not descending else 0.85
        if mach < 0.8:
            return base_cd
        elif 0.8 <= mach <= 1.2:
            return base_cd + 0.45 * math.sin(math.pi * (mach - 0.8) / 0.4)
        else:
            return base_cd + 0.25 / (mach ** 0.5)

#===================== FLIGHT GUIDANCE COMPUTER ====================
def compute_suicide_burn_alt(velocity, current_mass, max_thrust, gravity):
    """Calculates theoretical radar altitude required to stop at max thrust."""
    if velocity >= 0:
        return 0.0
    a_net = (max_thrust / current_mass) - gravity
    if a_net <= 0:
        return 999999.0
    return (velocity ** 2) / (2.0 * a_net)

# ======================== SIMULATION RUNNER ===================
def configure_stage():
    clear()
    print("============================================================")
    print("Level 2 (PHASE 3): POWERED DESCENT & SUICIDE BURN")
    print("Mission Profile:")
    print(" 1. Ascent phase to > 500 m apogee.")
    print(" 2. Atmospheric re-entry freefall.")
    print(" 3. Suicide burn hoverslam landing (< 3.0 m/s touchdown).")
    print("Vehicle Specs:")
    print(" • Dry Mass: 50.0 kg | Cross-section: 0.0707 m^2")
    print(" • Max Engine Thrust: 1800.0 N (Upgraded for hoverslam)")
    print(" • Fuel Flow Rate: 6.0 kg/s at 100% throttle")
    print("=========================================================")

    dry_mass = 50.0
    while True:
        try:
            val = input("\nEnter propellant load in kg [40.0 - 150.0]: ").strip()
            fuel = float(val)
            if 40.0 <= fuel ,= 150.0:
                return dry_mass, fuel 
            print("Recommended 40 to 150 kg for ascent + reserve landing propellant.")
        except ValueError:
            print("Invalid input. Enter a numeric value. ")

def play_launch(dry_mass, fuel_mass):
    recorder = FlightRecorder("flight_telemetry.csv")

    altitude = 0.0
    velocity = 0.0
    gravity = 9.81
    max_thrust = 1800.0
    burn_rate_full = 6.0
    dt = 0.2
    step = 0

    radius = 0.15
    cross_section_area = math.pi * (radius ** 2)

    apogee_reached = False
    peak_altitude = 0.0

    print("\n--- PRE-LAUNCH READINESS ---")
    print(f"Total Mass: {dry_mass + fuel_mass:.1f} kg")
    print("Flight Plan: Burn to apogee -> Coast -> Execute hoverslam.")
    input("\nPress Enter to ignite booster...")

    while True:
        clear()
        total_mass = dry_mass + fuel_mass
        twr = (max_thrust / (total_mass * gravity)) if (fuel_mass > 0 and total_mass > 0) else 0.0

        if velocity < 0 and not apogee_reached and altitude > 10.0:
            apogee_reached = True

        flight_phase = "ASCENT" if not apogee_reached else "DESCENT"

        # Atmospheric calculations
        descending = velocity < 0
        rho = AtmosphereModel.air_density(altitude)
        mach = abs(velocity) / AtmosphereModel.SPEED_OF_SOUND
        cd = AtmosphereModel.drag_coefficient(mach, descending=descending)
        q = 0.5 * rho * (velocity ** 2)
        drag_force = 0.5 * rho * velocity * abs(velocity) * cd * cross_section_area

        #Suicide burn radar calculation
        hoverslam_threshold = compute_suicide_burn_alt(velocity, total_mass, max_thrust, gravity)

        print(f"-- T+{step * dt:05.1f}s | PHASE: {flight_phase} ---")
        print(f"Altitude      : {altitude:6.1f} m  | Apogee Achieved: {peak_altitude:6.1f} m")
        print(f"Velocity      : {velocity:6.1f} m/s ({'CLIMBING' if velocity >= 0 else 'FALLING'})")
        print(f"Propellant    : {fuel_mass:6.1f} kg | Mass: {total_mass:6.1f} kg  | TWR: {twr:4.2f}")
        print(f"Dyn Pressure q: {q:6.1f} Pa  | Drag Force: {drag_force:6.1f} N")

        if descending:
            burn_margin = altitude - hoverslam_threshold
            margin_status = "CRITICAL IGNITION" if burn_margin <= 0 else f"{burn_margin:5.1f} m above burn window"
            print(f"Radar Suicide Burn Alt : {hoverslam_threshold:6.1f} m [{margin_status}]")
        print("-" * 58)

        # ASCII position display
        track_height = 10
        pos = min(track_height - 1, max(0, int((altitude / 500.0) * track_height)))
        icon = "[🚀]" if velocity >= 0 else "[🔻]"
        for i in range(track_height - 1, -1, -1):
            if i == pos:
                print(f"   |     {icon} ({flight_phase})")
            else:
                print("    |")
        print("===+===================================== (PAD 39A)")

        #Throttle input
        if fuel_mass <= 0:
            throttle = 0.0
            print("\n⚠️ PROPELLANT DEPLETED. Unpowered ballistic flight.")
            time.sleep(0.12)
        else:
            default_thro = "0" if (descending and altitude > hoverslam_threshold + 20) else "100"
            while True:
                cmd = input(f"\nThrottle % [0-100] (Enter for {default_thro}%, 'q' to abort): ").strip()
                if cmd == "":
                    throttle = float(default_thro)
                    break
                if cmd.lower() == "q":
                    recorder.print_post_flight_summary(dt, "MISSION ABORTED")
                    return
                try:
                    throttle = float(cmd)
                    if 0.0 <= throttle <= 100.0:
                        break
                    print("Throttle must be 0 to 100.")
                except ValueError:
                    print("Invalid input.")

        # Propulsion and motion integration
        requested_burn = (throttle / 100.0) * burn_rate_full * dt
        actual_burn = min(fuel_mass, requested_burn)
        fuel_mass -= actual_burn

        current_thrust = (actual_burn / (burn_rate_full * dt)) * max_thrust if (burn_rate_full * dt) > 0 else 0.0
        net_force = current_thrust - (total_mass * gravity) - drag_force
        accel = net_force / total_mass

        # Pad clamping before liftoff
        if altitude <= 0.0 and accel < 0 and not apogee_reached:
            accel = 0.0
            velocity = 0.0
            altitude = 0.0

        recorder.log(step * dt, altitude, velocity, accel, total_mass, current_thrust, q, drag_force, throttle, flight_phase)

        velocity += accel * dt
        altitude += velocity * dt
        if altitude > peak_altitude:
            peak_altitude = altitude
        step += 1

        # Touchdown detection on descent
        if apogee_reached and altitude <= 0.0:
            altitude = 0.0
            clear()
            if abs(velocity) <= 3.0:
                outcome = "🏆 SUCCESSFUL HOVERSLAM TOUCHDOWN! BOOSTER RECOVERED"
            elif abs(velocity) <= 8.0:
                outcome = "⚠️ HARD LANDING - LANDING GEAR COLLAPSE"
            else:
                outcome = "💥 CRASH - RAPID UNSCHEDULED DISASSEMBLY (RUD)"
            recorder.print_post_flight_summary(dt, outcome)
            return

        time.sleep(0.02)

if __name__ == "__main__":
    dry, fuel = configure_stage()
    play_launch(dry, fuel) 
    




