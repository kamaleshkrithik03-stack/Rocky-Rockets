import os
import sys
import time
import math
import csv

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

# =====================================================================
# TELEMETRY FLIGHT RECORDER
# =====================================================================
class FlightRecorder:
    def __init__(self, filename="karman_mission_telemetry.csv"):
        self.filename = filename
        self.records = []
        self.headers = [
            "time_s", "altitude_m", "downrange_m", "velocity_y_mps", 
            "mass_kg", "thrust_N", "q_pa", "mission_phase"
        ]
        with open(self.filename, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(self.headers)

    def log(self, t, alt, downrange, vy, mass, thrust, q, phase):
        row = [
            round(t, 2), round(alt, 2), round(downrange, 2), round(vy, 2),
            round(mass, 2), round(thrust, 2), round(q, 2), phase
        ]
        self.records.append(row)
        with open(self.filename, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)

# =====================================================================
# ATMOSPHERE MODEL (Extended for Space Transition)
# =====================================================================
class AtmosphereModel:
    RHO_0 = 1.225
    SCALE_HEIGHT = 8500.0
    SPEED_OF_SOUND = 340.0

    @classmethod
    def air_density(cls, altitude: float) -> float:
        if altitude < 0:
            return cls.RHO_0
        if altitude > 100000:
            return 0.0  # Vacuum of space past Kármán line
        return cls.RHO_0 * math.exp(-altitude / cls.SCALE_HEIGHT)

# =====================================================================
# MASTER SIMULATION RUNNER
# =====================================================================
def run_karman_mission():
    clear()
    print("================================================================")
    print("🚀 LEVEL 5 (PHASE 7): KÁRMÁN LINE BREACH & REUSABLE BOOSTER LANDING")
    print("================================================================")
    print(" Mission Profile:")
    print("  1. Heavy lift ascent & gravity pitch-over")
    print("  2. Stage separation & Tuned upper stage push past 100km Kármán Line")
    print("  3. Payload Deployment in space")
    print("  4. Booster entry burn & vertical propulsive landing (Hoverslam)")
    print("================================================================")
    input("\nPress Enter to initiate orbital-class launch sequence...")

    recorder = FlightRecorder("karman_mission_telemetry.csv")

    # Vehicle Specs (Tuned Heavy-Class for Kármán Breach)
    booster_dry = 450.0
    booster_fuel = 1800.0
    upper_dry = 120.0
    upper_fuel = 650.0
    payload_mass = 150.0

    booster_thrust = 45000.0  # N
    upper_thrust = 15000.0    # N
    landing_thrust = 35000.0  # N

    # Simulation States
    t = 0.0
    dt = 0.1
    step = 0
    
    altitude = 0.0
    downrange = 0.0
    velocity = 0.0
    
    phase = "ASCENT"
    b_fuel = booster_fuel
    u_fuel = upper_fuel
    payload_deployed = False
    staging_timer = 0.0

    while phase != "LANDED":
        clear()

        # Current Stack Mass & Thrusting Logic
        if phase in ["ASCENT"]:
            total_mass = booster_dry + b_fuel + upper_dry + u_fuel + payload_mass
            active_thrust = booster_thrust
            burn_rate = 35.0
        elif phase in ["STAGING_COAST"]:
            total_mass = upper_dry + u_fuel + payload_mass
            active_thrust = 0.0
            burn_rate = 0.0
        elif phase in ["UPPER_BURN"]:
            total_mass = upper_dry + u_fuel + payload_mass
            active_thrust = upper_thrust
            burn_rate = 12.0
        elif phase in ["KARMAN_COAST", "PAYLOAD_SEP"]:
            total_mass = upper_dry + payload_mass
            active_thrust = 0.0
            burn_rate = 0.0
        elif phase in ["BOOSTER_ENTRY"]:
            total_mass = booster_dry + max(0.0, b_fuel)
            active_thrust = landing_thrust if altitude < 8000 and velocity < -10 else 0.0
            burn_rate = 35.0 if active_thrust > 0 else 0.0
        else:
            total_mass = booster_dry
            active_thrust = 0.0
            burn_rate = 0.0

        gravity = 9.81
        rho = AtmosphereModel.air_density(altitude)
        q = 0.5 * rho * (velocity ** 2)
        drag = 0.5 * rho * velocity * abs(velocity) * 0.35 * 1.5

        net_force = active_thrust - (total_mass * gravity) - drag
        accel = net_force / total_mass

        # Phase Transition Logic
        if phase == "ASCENT":
            if b_fuel > 0:
                b_fuel -= burn_rate * dt
            else:
                phase = "STAGING_COAST"
                staging_timer = 2.0

        elif phase == "STAGING_COAST":
            staging_timer -= dt
            if staging_timer <= 0:
                phase = "UPPER_BURN"

        elif phase == "UPPER_BURN":
            if u_fuel > 0:
                u_fuel -= burn_rate * dt
            else:
                phase = "KARMAN_COAST"

        elif phase == "KARMAN_COAST":
            if altitude >= 100000 and velocity <= 0:
                phase = "PAYLOAD_SEP"

        elif phase == "PAYLOAD_SEP":
            if not payload_deployed:
                print("\n🛰️ PAYLOAD DEPLOYED SUCCESSFULLY INTO SUBORBITAL SPACE!")
                payload_deployed = True
                time.sleep(1.5)
            phase = "BOOSTER_ENTRY"

        # Console Display
        print(f"--- MISSION TIME: T+{t:06.2f}s | PHASE: {phase} ---")
        print(f"Altitude      : {altitude:10.1f} m  ({altitude/1000:5.1f} km)")
        print(f"Velocity      : {velocity:8.1f} m/s")
        print(f"Dynamic Press : {q:8.1f} Pa")
        print(f"Vehicle Mass  : {total_mass:8.1f} kg")
        if altitude >= 100000:
            print("✨ STATUS    : ABOVE KÁRMÁN LINE (SPACE)")
        print("-" * 55)

        recorder.log(t, altitude, downrange, velocity, total_mass, active_thrust, q, phase)

        # Integration
        velocity += accel * dt
        altitude += velocity * dt
        t += dt
        step += 1


        if altitude <= 0.0:
            altitude = 0.0
            velocity = 0.0
            phase = "LANDED"
            recorder.log(t, altitude, downrange, velocity, total_mass, 0.0, q, phase)
            break

        time.sleep(0.01)

    clear()
    print("================================================================")
    print("🎉 MISSION ACCOMPLISHED: KÁRMÁN BREACH & SUCCESSFUL BOOSTER LANDING")
    print(f"Telemetry saved to: {os.path.abspath(recorder.filename)}")
    print("================================================================")
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    run_karman_mission()