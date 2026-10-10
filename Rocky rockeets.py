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
            "time_s", "altitude_m", "velocity_mps", "accel_mps2", 
            "mass_kg", "thrust_N", "q_pa", "drag_force_N", "throttle_pct"
        ]
        # Initialize and clear CSV file with headers
        with open(self.filename, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(self.headers)

    def log(self, t, alt, vel, acc, mass, thrust, q, drag, throttle):
        row = [
            round(t, 2), round(alt, 2), round(vel, 2), round(acc, 2),
            round(mass, 2), round(thrust, 2), round(q, 2), round(drag, 2),
            round(throttle, 1)
        ]
        self.records.append(row)
        with open(self.filename, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)

    def print_post_flight_summary(self, dt):
        if not self.records:
            return

        peak_alt = max(r[1] for r in self.records)
        peak_vel = max(r[2] for r in self.records)
        peak_acc = max(r[3] for r in self.records)
        peak_g = peak_acc / 9.81
        peak_q = max(r[6] for r in self.records)

        # Numerical integration of delta-v budget and losses
        total_delta_v = sum((r[5] / r[4]) * dt for r in self.records)
        gravity_loss = sum(9.81 * dt for r in self.records if r[1] > 0)
        drag_loss = sum((r[7] / r[4]) * dt for r in self.records)

        print("\n" + "=" * 58)
        print("📊 AVIONICS POST-FLIGHT TELEMETRY REPORT")
        print("=" * 58)
        print(f"Max Altitude (Apogee)    : {peak_alt:8.1f} m")
        print(f"Max Velocity             : {peak_vel:8.1f} m/s")
        print(f"Peak Acceleration        : {peak_acc:8.2f} m/s² ({peak_g:4.1f} G)")
        print(f"Max Dynamic Pressure (q) : {peak_q:8.1f} Pa")
        print("-" * 58)
        print("ENERGY BUDGET & LOSSES:")
        print(f"  • Total Thrust Δv Expended : {total_delta_v:8.1f} m/s")
        print(f"  • Gravity Drag Losses (gΔt): {gravity_loss:8.1f} m/s")
        print(f"  • Aerodynamic Drag Losses  : {drag_loss:8.1f} m/s")
        print(f"\nTelemetry saved to: {os.path.abspath(self.filename)}")
        print("=" * 58)

# ==================== AERODYNAMICS & ATMOSPHERE ENGINE ====================
class AtmosphereModel:
    RHO_0 = 1.225          # Sea-level density (kg/m^3)
    SCALE_HEIGHT = 8500.0  # Scale height (m)
    SPEED_OF_SOUND = 340.0 # m/s

    @classmethod
    def air_density(cls, altitude: float) -> float:
        if altitude < 0:
            return cls.RHO_0
        return cls.RHO_0 * math.exp(-altitude / cls.SCALE_HEIGHT)

    @classmethod
    def drag_coefficient(cls, mach: float) -> float:
        base_cd = 0.35
        if mach < 0.8:
            return base_cd
        elif 0.8 <= mach <= 1.2:
            # Transonic wave drag spike
            return base_cd + 0.45 * math.sin(math.pi * (mach - 0.8) / 0.4)
        else:
            return base_cd + 0.25 / (mach ** 0.5)

# ==================== SIMULATION RUNNER ====================
def configure_stage():
    clear()
    print("==========================================================")
    print("🚀 LEVEL 1 (PHASE 2): TELEMETRY RECORDER & POST-FLIGHT DATA")
    print("==========================================================")
    print("Mission Target: Reach an apogee of 500.0 m.")
    print("Vehicle Profile:")
    print("  • Dry Mass: 50.0 kg | Cross-Sectional Area: 0.0707 m²")
    print("  • Max Thrust: 1400.0 N | Burn Rate: 5.0 kg/s")
    print("Phase 2 Additions:")
    print("  • High-rate black-box CSV flight recorder")
    print("  • Numerical Δv budget & drag loss accounting")
    print("  • Peak G-load and dynamic pressure (q) telemetry")
    print("==========================================================")

    dry_mass = 50.0
    while True:
        try:
            val = input("\nEnter propellant load in kg [10.0 - 150.0]: ").strip()
            fuel = float(val)
            if 10.0 <= fuel <= 150.0:
                return dry_mass, fuel
            print("Please enter a value between 10.0 and 150.0 kg.")
        except ValueError:
            print("Invalid input. Enter a numeric value.")

def play_launch(dry_mass, fuel_mass):
    recorder = FlightRecorder("flight_telemetry.csv")

    altitude = 0.0
    velocity = 0.0
    gravity = 9.81
    max_thrust = 1400.0
    burn_rate_full = 5.0
    dt = 0.2
    step = 0

    radius = 0.15
    cross_section_area = math.pi * (radius ** 2)

    initial_mass = dry_mass + fuel_mass
    initial_twr = max_thrust / (initial_mass * gravity)

    print("\n--- PRE-LAUNCH FLIGHT ENVELOPE ---")
    print(f"Total Wet Mass      : {initial_mass:6.1f} kg")
    print(f"Liftoff TWR         : {initial_twr:6.2f} "
          f"{'(TWR > 1.0: Lift-off ready)' if initial_twr > 1.0 else '(WARNING: TWR <= 1.0, Pad clamped)'}")
    print(f"Telemetry Output    : flight_telemetry.csv [ARMED]")
    input("\nPress Enter to begin ignition sequence...")

    while True:
        clear()
        total_mass = dry_mass + fuel_mass
        twr = (max_thrust / (total_mass * gravity)) if (fuel_mass > 0 and total_mass > 0) else 0.0

        # Atmospheric computations
        rho = AtmosphereModel.air_density(altitude)
        mach = abs(velocity) / AtmosphereModel.SPEED_OF_SOUND
        cd = AtmosphereModel.drag_coefficient(mach)
        q = 0.5 * rho * (velocity ** 2)
        drag_force = 0.5 * rho * velocity * abs(velocity) * cd * cross_section_area

        print(f"--- T+{step * dt:05.1f}s AVIONICS TELEMETRY ---")
        print(f"Altitude      : {altitude:6.1f} m  [Target: 500.0 m]")
        print(f"Velocity      : {velocity:6.1f} m/s (Mach {mach:4.2f})")
        print(f"Air Density   : {rho:6.4f} kg/m³ | Dynamic Cd: {cd:4.2f}")
        print(f"Dyn Pressure q: {q:6.1f} Pa  | Drag Force: {drag_force:6.1f} N")
        print(f"Propellant    : {fuel_mass:6.1f} kg | Mass: {total_mass:6.1f} kg | TWR: {twr:4.2f}")
        print("-" * 54)
        
        track_height = 10
        pos = min(track_height - 1, max(0, int((altitude / 500.0) * track_height)))
        for i in range(track_height - 1, -1, -1):
            if i == pos:
                print("   |    [🚀] (Booster Core)")
            else:
                print("   |")
        print("===+==================================== (PAD 39A)")

        if fuel_mass <= 0:
            throttle = 0.0
            print("\n⚠️ MECO: Main Engine Cut-Off. Aerodynamic coasting...")
            time.sleep(0.15)
        else:
            while True:
                cmd = input("\nEnter throttle % [0-100] (Default 100, 'q' to abort): ").strip()
                if cmd == "":
                    throttle = 100.0
                    break
                if cmd.lower() == "q":
                    print("\nMission aborted by Flight Director.")
                    recorder.print_post_flight_summary(dt)
                    return
                try:
                    throttle = float(cmd)
                    if 0.0 <= throttle <= 100.0:
                        break
                    print("Throttle must be within 0.0 to 100.0.")
                except ValueError:
                    print("Invalid input.")

        requested_burn = (throttle / 100.0) * burn_rate_full * dt
        actual_burn = min(fuel_mass, requested_burn)
        fuel_mass -= actual_burn

        current_thrust = (actual_burn / (burn_rate_full * dt)) * max_thrust if (burn_rate_full * dt) > 0 else 0.0
        net_force = current_thrust - (total_mass * gravity) - drag_force
        accel = net_force / total_mass

        if altitude <= 0.0 and accel < 0:
            accel = 0.0
            velocity = 0.0
            altitude = 0.0

        recorder.log(step * dt, altitude, velocity, accel, total_mass, current_thrust, q, drag_force, throttle)

        velocity += accel * dt
        altitude += velocity * dt
        step += 1

        if altitude >= 500.0:
            clear()
            print("==========================================================")
            print("🏆 MISSION SUCCESS: LEVEL 1 CLEARED (APOGEE EXCEEDED)!")
            print(f"Target passed at T+{step * dt:.1f}s.")
            print("==========================================================")
            recorder.print_post_flight_summary(dt)
            return

        if velocity < 0 and fuel_mass <= 0 and altitude > 0:
            clear()
            print("==========================================================")
            print("⚠️ MISSION FAILED: APOGEE SHORT OF TARGET")
            print(f"Max Altitude Achieved: {altitude:.1f} m (Target: 500.0 m)")
            print("==========================================================")
            recorder.print_post_flight_summary(dt)
            return

        time.sleep(0.02)

if __name__ == "__main__":
    dry, fuel = configure_stage()
    play_launch(dry, fuel)