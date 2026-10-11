import os
import sys
import time
import math
import csv

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

#====================== TELEMETRY FLIGHT RECORDER ====================
class FlightRecorder:
    def __init__(self, filename="multistage_telemetry.csv"):
        self.filename = filename
        self.records = []
        self.headers = [
            "time_s", "altitude_m", "velocity_mps", "accel_mps2",
            "mass_kg", "thrust_N", "q_pa", "drag_force_N", "active_stage"
        ] 
        with open(self.filename, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(self.headers)

    def log(self, t, alt, vel, acc, mass, thrust, q, drag, stage_name):
        row = [
            round(t, 2), round(alt, 2), round(vel, 2), round(acc, 2),
            round(mass, 2), round(thrust, 2), round(q, 2), round(drag, 2),
            stage_name
        ]
        self.records.append(row)
        with open(self.filename, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)

#===================== AERODYNAMICS & ATMOSPHERE ENGINE ====================
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

#======================== FLIGHT RECORDER SUMMARY =========================
def print_flight_summary(recorder, dt):
    if not recorder.records:
        return
    peak_alt = max(r[1] for r in recorder.records)
    peak_vel = max(r[2] for r in recorder.records)
    peak_acc = max(r[3] for r in recorder.records)
    
    print("\n" + "=" * 60)
    print("📊 MULTI-STAGE FLIGHT TELEMETRY SUMMARY")
    print("=" * 60)
    print(f"Max Altitude Reached      : {peak_alt:8.1f} m")
    print(f"Max Velocity              : {peak_vel:8.1f} m/s")
    print(f"Peak Acceleration         : {peak_acc:8.2f} m/s^2 ({peak_acc/9.81:.1f} G)")
    print(f"Telemetry saved to        : {os.path.abspath(recorder.filename)}")
    print("=" * 60)

#====================== VEHICLE STAGE CLASS ===================
class RocketStage:
    def __init__(self, name, dry_mass, fuel_mass, max_thrust, burn_rate, cross_section_area):
        self.name = name
        self.dry_mass = dry_mass
        self.fuel_mass = fuel_mass
        self.max_thrust = max_thrust
        self.burn_rate = burn_rate # kg/s
        self.area = cross_section_area

#=========================== SIMULATION RUNNER ===========================
def run_multistage_simulation():
    clear()
    print("================================================================")
    print("LEVEL 3 (PHASE 4): TWO-STAGE ROCKET DYNAMICS")
    print("================================================================")
    print("Configuring Vehicle Stacks:")
    print("  • Stage 1 (Booster) : Dry 35kg | Fuel 80kg | Thrust 2200N")
    print("  • Stage 1 (Upper) : Dry 15kg | Fuel 40kg | Thrust 900N")
    print("=======================================================")
    input("\nPress Enter to initiate countdown...")

    recorder = FlightRecorder("multistage_telemetry.csv")

    stage1 = RocketStage("Stage-1 (Booster)", dry_mass=35.0, fuel_mass=80.0, max_thrust=2200.0, burn_rate=7.0, cross_section_area=0.0707)
    stage2 = RocketStage("Stage-2 (Upper)", dry_mass=15.0, fuel_mass=40.0, max_thrust=900.0, burn_rate=3.0, cross_section_area=0.0500)

    current_stage = stage1
    staging_timer = 0.0

    altitude = 0.0
    velocity = 0.0
    gravity = 9.81
    dt = 0.1
    step = 0

    while True:
        clear()

        if current_stage == stage1:
            total_mass = stage1.dry_mass + stage1.fuel_mass + stage2.dry_mass + stage2.fuel_mass
            active_area = stage1.area
        elif current_stage == "COAST":
            total_mass = stage2.dry_mass + stage2.fuel_mass
            active_area = stage2.area
        else:
            total_mass = stage2.dry_mass + stage2.fuel_mass
            active_area = stage2.area

        twr = (current_stage.max_thrust / (total_mass * gravity)) if isinstance(current_stage, RocketStage) and current_stage.fuel_mass > 0 else 0.0

        rho = AtmosphereModel.air_density(altitude)
        mach = abs(velocity) / AtmosphereModel.SPEED_OF_SOUND
        cd = AtmosphereModel.drag_coefficient(mach)
        q = 0.5 * rho * (velocity ** 2)
        drag_force = 0.5 * rho * velocity * abs(velocity) * cd * active_area

        stage_label = current_stage.name if isinstance(current_stage, RocketStage) else current_stage
        print(f"--- T+{step * dt:05.1f}s | ACTIVE STACK:  {stage_label} ---")
        print(f"Altitude      : {altitude:6.1f} m")
        print(f"Velocity      : {velocity:6.1f} m/s (Mach {mach:4.2f})")
        print(f"Toatal Mass   : {total_mass:6.1f} kg | TWR: {twr:4.2f}")
        print(f"Dyn Pressure q: {q:6.1f} Pa  | Drag: {drag_force:6.1f} N")
        print("-" * 55)

        current_thrust = 0.0
        if isinstance(current_stage, RocketStage):
            if current_stage.fuel_mass > 0:
                burned = current_stage.burn_rate * dt
                current_stage.fuel_mass = max(0.0, current_stage.fuel_mass - burned)
                current_thrust = current_stage.max_thrust
            else:
                if current_stage == stage1:
                    print("\n  STAGE 1 DEPLETED: Initiating staging seperation...")
                    current_stage = "COAST"
                    staging_timer = 1.5
                else:
                    current_thrust = 0.0
        elif current_stage == "COAST":
            staging_timer -= dt
            print(f"\n  Interstage coast clearance... [{staging_timer:3.1f}s remaining]") 
            if staging_timer <= 0:
                print("  STAGE 2 IGNITION!")
                current_stage = stage2

        if current_stage == "COAST":
            current_thrust = 0.0

        net_force = current_thrust - (total_mass * gravity) - drag_force
        accel = net_force / total_mass

        if altitude <= 0.0 and accel< 0:
            accel = 0.0
            velocity = 0.0
            altitude = 0.0

        recorder.log(step * dt, altitude, velocity, accel, total_mass, current_thrust, q, drag_force, stage_label)

        velocity += accel * dt
        altitude += velocity * dt
        step +=1

        if velocity < 0 and altitude > 100:
            clear()
            print("===========================================================")
            print(" MULTI-STAGE FLIGHT COMPLETE: APOGEE REACHED")
            print(f"Apogee Altitude: {altitude:.1f} m")
            print("===========================================================")
            print_flight_summary(recorder, dt)
            return
        
        time.sleep(0.02)

if __name__ == "__main__":
    run_multistage_simulation()
