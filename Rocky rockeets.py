import os
import sys
import time

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def configure_stage():
    clear()
    print("---------------------------------------------")
    print("🚀 Level 1: Overcoming the Rocket Equation")
    print("---------------------------------------------")
    print("Mission Target: Reach an apogee of 500.0 m")
    print("Vehicle Profile (Low-Altitude Test Core):")
    print("  • Dry Mass (Avionics, Fairing, Tanks): 50.0 kg")
    print("  • Max Engine Thrust: 1200.0 N")
    print("  • Mass Flow Rate: 5.0 kg/s at 100% throttle")
    print("  • Standard Gravity (g): 9.81 m/s²")
    print("---------------------------------------------")
    print("TWR Constraint:")
    print("Lift-off requires TWR > 1.0 (Total Mass < 122.3 kg).")
    print("Excess fuel will burn on the pad until the vehicle")
    print("becomes light enough to generate positive net thrust.")
    print("=============================================")

    dry_mass = 50.0
    while True:
        try:
            val = input("\nEnter fuel load in kg [10.0 - 200.0]: ").strip()
            fuel = float(val)
            if 10.0 <= fuel <= 200.0:
                return dry_mass, fuel
            print("Please enter a value between 10.0 and 200.0 kg.")
        except ValueError:
            print("Invalid input. Enter a numeric value.")

def play_launch(dry_mass, fuel_mass):
    altitude = 0.0
    velocity = 0.0
    gravity = 9.81
    max_thrust = 1200.0
    burn_rate_full = 5.0
    dt = 0.5
    step = 0

    initial_mass = dry_mass + fuel_mass
    initial_twr = max_thrust / (initial_mass * gravity)

    print("\n--- PRE-LAUNCH TELEMETRY ---")
    print(f"Total Wet Mass : {initial_mass:6.1f} kg")
    print(f"Liftoff TWR    : {initial_twr:6.2f} "
          f"{'(TWR > 1.0: Lift-off capable)' if initial_twr > 1.0 else '(WARNING: TWR <= 1.0, Rocket will burn on pad until light enough)'}")
    input("\nPress Enter to begin ignition sequence...")

    while True:
        clear()
        total_mass = dry_mass + fuel_mass
        twr = (max_thrust / (total_mass * gravity)) if (fuel_mass > 0 and total_mass > 0) else 0.0

        print(f"--- T+{step * dt:04.1f}s TELEMETRY ---")
        print(f"Altitude   : {altitude:6.1f} m  [Target: 500.0 m]")
        print(f"Velocity   : {velocity:6.1f} m/s ({'ASCENDING' if velocity >= 0 else 'DESCENDING'})")
        print(f"Propellant : {fuel_mass:6.1f} kg | Total Mass: {total_mass:6.1f} kg")
        print(f"Engine TWR : {twr:5.2f}")
        print("-" * 44)

        track_height = 10
        pos = min(track_height - 1, max(0, int((altitude / 500.0) * track_height)))
        for i in range(track_height - 1, -1, -1):
            if i == pos:
                print("   |    [🚀] (Booster Core)")
            else:
                print("   |")
        print("===+============================== (PAD 39A)")

        # Throttle control
        if fuel_mass <= 0:
            throttle = 0.0
            print("\n⚠️ MECO: Main Engine Cut-Off (Propellant Exhausted). Coasting...")
            time.sleep(0.4)
        else:
            while True:
                cmd = input("\nEnter throttle % [0-100] (Default 100, 'q' to abort): ").strip()
                if cmd == "":
                    throttle = 100.0
                    break
                if cmd.lower() == "q":
                    print("\nMission aborted by Flight Control.")
                    return
                try:
                    throttle = float(cmd)
                    if 0.0 <= throttle <= 100.0:
                        break
                    print("Throttle must be within 0.0 to 100.0.")
                except ValueError:
                    print("Invalid input. Enter a numeric value.")

        # Physics integration
        requested_burn = (throttle / 100.0) * burn_rate_full * dt
        actual_burn = min(fuel_mass, requested_burn)
        fuel_mass -= actual_burn
        
