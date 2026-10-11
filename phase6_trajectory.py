import os
import sys
import time 
import math
import csv

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

# ==================== TELEMETRY FLIGHT RECORDER ====================
class FlightRecorder:
    def __init__(self, filename="phase6_telemetry.csv"):
        self.filename = filename
        self.records = []
        self.headers = [
            "time_s", "altitude_m", "downrange_m", "velocity_x_mps", "velocity_y_mps",
            "total_velocity_mps", "flight_path_angle_deg", "mass_kg", "thrust_N", "q_pa", "stage"
        ]
        with open(self.filename, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(self.headers)

    def log(self, t, alt, downrange, vx, vy, v_total, fpa, mass, thrust, q, stage_name):
        row = [
            round(t, 2), round(alt, 2), round(downrange, 2), round(vx, 2), round(vy, 2),
            round(v_total, 2), round(fpa, 2), round(mass, 2), round(thrust, 2), round(q, 2), stage_name
        ]
        self.records.append(row)
        with open(self.filename, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)

# ========================= ATMOSPHERE ENGINE ===================
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
    def drag_coefficient(cls, mach: float) -> float:
        base_cd = 0.35
        if mach < 0.8:
            return base_cd
        elif 0.8 <= mach <= 1.2:
            return base_cd + 0.45 * math.sin(math.pi * (mach - 0.8) / 0.4)
        else:
            return base_cd + 0.25 / (mach ** 0.5)

# ===================== VEHICLE STAGE CLASS ======================
class RocketStage:
    def __init__(self, name, dry_mass, fuel_mass, max_thrust, burn_rate, cross_section_area):
        self.name = name
        self.dry_mass = dry_mass
        self.fuel_mass = fuel_mass
        self.max_thrust = max_thrust
        self.burn_rate = burn_rate
        self.area = cross_section_area

# ==================== FLIGHT SUMMARY PRINTER ====================
def print_flight_summary(recorder, dt):
    if not recorder.records:
        return
    peak_alt = max(r[1] for r in recorder.records)
    max_downrange = max(r[2] for r in recorder.records)
    peak_vel = max(r[5] for r in recorder.records)
    
    print("\n" + "=" * 65)
    print("📊 PHASE 6 TRAJECTORY TELEMETRY SUMMARY")
    print("=" * 65)
    print(f"Max Altitude (Apogee)    : {peak_alt:8.1f} m")
    print(f"Total Downrange Distance : {max_downrange:8.1f} m")
    print(f"Max Velocity             : {peak_vel:8.1f} m/s")
    print(f"Telemetry saved to       : {os.path.abspath(recorder.filename)}")
    print("=" * 65)

# ====================== SIMULATION RUNNER ======================
def run_phase6_simulation():
    clear()
    print("================================================================")
    print(" LEVEL 5 (PHASE 6): GRAVITY TURN WITH INITIAL TILT PERTURBATION")
    print("================================================================")
    print("Vehicle Stack Configuration:")
    print("  • Stage 1 (Booster) : Dry 35kg | Fuel 80kg | Thrust 2200N")
    print("  • Stage 2 (Upper)   : Dry 15kg | Fuel 40kg | Thrust  900N")
    print("Flight Profile: Initial 5° tilt kick -> Natural Gravity Turn -> Apogee")
    print("================================================================")
    input("\nPress Enter to initiate Phase 6 launch sequence...")

    recorder = FlightRecorder("phase6_telemetry.csv")

    stage1 = RocketStage("Stage-1 (Booster)", dry_mass=35.0, fuel_mass=80.0, max_thrust=2200.0, burn_rate=7.0, cross_section_area=0.0707)
    stage2 = RocketStage("Stage-2 (Upper)", dry_mass=15.0, fuel_mass=40.0, max_thrust=900.0, burn_rate=3.0, cross_section_area=0.0500)

    current_stage = stage1
    staging_timer = 0.0

    # 2D Kinematic States
    x = 0.0
    y = 0.0
    vx = 0.0
    vy = 0.0

    gravity = 9.81
    dt = 0.1
    step = 0

    while True:
        clear()

        # Mass and active area calculations
        if current_stage == stage1:
            total_mass = stage1.dry_mass + stage1.fuel_mass + stage2.dry_mass + stage2.fuel_mass
            active_area = stage1.area
        elif current_stage == "COAST":
            total_mass = stage2.dry_mass + stage2.fuel_mass
            active_area = stage2.area
        else:
            total_mass = stage2.dry_mass + stage2.fuel_mass
            active_area = stage2.area

        v_total = math.sqrt(vx**2 + vy**2)

        # Flight Path Angle (gamma) relative to horizontal
        if v_total > 0.01:
            fpa_rad = math.asin(max(-1.0, min(1.0, vy / v_total)))
            fpa_deg = math.degrees(fpa_rad)
        else:
            fpa_rad = math.radians(90.0)
            fpa_deg = 90.0

        # Pitch-over maneuver program with initial launch perturbation
        if y < 25.0:
            # Initial 5-degree tilt kick off the pad to seed horizontal velocity (vx)
            pitch_rad = math.radians(85.0)
        else:
            # Natural gravity turn tracking the flight path angle vector
            pitch_rad = fpa_rad

        twr = (current_stage.max_thrust / (total_mass * gravity)) if isinstance(current_stage, RocketStage) and current_stage.fuel_mass > 0 else 0.0

        # Atmosphere & Aerodynamic Drag (2D Components)
        rho = AtmosphereModel.air_density(y)
        mach = v_total / AtmosphereModel.SPEED_OF_SOUND
        cd = AtmosphereModel.drag_coefficient(mach)
        q = 0.5 * rho * (v_total ** 2)

        drag_total = 0.5 * rho * v_total * cd * active_area
        drag_x = -drag_total * (vx / v_total) if v_total > 0 else 0.0
        drag_y = -drag_total * (vy / v_total) if v_total > 0 else 0.0

        # Propulsion (2D Force Decomposition)
        current_thrust = 0.0
        if isinstance(current_stage, RocketStage):
            if current_stage.fuel_mass > 0:
                burned = current_stage.burn_rate * dt
                current_stage.fuel_mass = max(0.0, current_stage.fuel_mass - burned)
                current_thrust = current_stage.max_thrust
            else:
                if current_stage == stage1:
                    print("\n🔥 STAGE 1 DEPLETED: Initiating staging separation...")
                    current_stage = "COAST"
                    staging_timer = 1.5
                else:
                    current_thrust = 0.0
        elif current_stage == "COAST":
            staging_timer -= dt
            print(f"\n⚙️ Interstage coast clearance... [{staging_timer:3.1f}s remaining]")
            if staging_timer <= 0:
                print("🚀 STAGE 2 IGNITION!")
                current_stage = stage2

        if current_stage == "COAST":
            current_thrust = 0.0

        thrust_x = current_thrust * math.cos(pitch_rad)
        thrust_y = current_thrust * math.sin(pitch_rad)

        # Net Accelerations
        ax = (thrust_x + drag_x) / total_mass
        ay = (thrust_y - (total_mass * gravity) + drag_y) / total_mass

        # Pad clamping before liftoff
        if y <= 0.0 and ay < 0:
            ay = 0.0
            vy = 0.0
            y = 0.0

        stage_label = current_stage.name if isinstance(current_stage, RocketStage) else current_stage

        print(f"--- T+{step * dt:05.1f}s | STACK: {stage_label} ---")
        print(f"Altitude (Y)   : {y:6.1f} m  | Downrange (X): {x:6.1f} m")
        print(f"Velocity Vector: {v_total:6.1f} m/s (Mach {mach:4.2f})")
        print(f"Flight Angle   : {fpa_deg:5.1f}°   | Pitch Angle  : {math.degrees(pitch_rad):5.1f}°")
        print(f"Total Mass     : {total_mass:6.1f} kg | TWR          : {twr:4.2f}")
        print(f"Dynamic Press q: {q:6.1f} Pa  | Drag Force   : {drag_total:6.1f} N")
        print("-" * 60)

        recorder.log(step * dt, y, x, vx, vy, v_total, fpa_deg, total_mass, current_thrust, q, stage_label)

        # Euler Integration
        vx += ax * dt
        vy += ay * dt
        x += vx * dt 
        y += vy * dt
        step += 1

        # Apogee detection
        if vy < 0 and y > 100:
            clear()
            print("================================================================")
            print("🏆 PHASE 6 TRAJECTORY SIMULATION COMPLETE: APOGEE REACHED")
            print(f"Peak Altitude (Apogee) : {y:.1f} m")
            print(f"Downrange Distance     : {x:.1f} m")
            print("================================================================")
            print_flight_summary(recorder, dt)
            return

        time.sleep(0.02)

if __name__ == "__main__":
    run_phase6_simulation()