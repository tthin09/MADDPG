#!/usr/bin/env python3
"""
Generate realistic Vietnamese rush hour traffic for 3x3 grid network.
- 4,200 vehicles (realistic peak hour congestion)
- Time-varying demand (rush hour build-up, peak, taper)
- Platoon effects (traffic waves)
- 80% motorcycles, directional asymmetry
"""

import random
import math
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Network entry edges (from external nodes into network)
ENTRY_EDGES = {
    'east': ['N_out_6_to_J6', 'N_out_3e_to_J3', 'N_out_9s_to_J9'],
    'west': ['N_out_4_to_J4', 'N_out_1w_to_J1', 'N_out_7s_to_J7'],
    'north': ['N_out_1_to_J1', 'N_out_2_to_J2', 'N_out_3_to_J3'],
    'south': ['N_out_7_to_J7', 'N_out_8_to_J8', 'N_out_9_to_J9']
}

# Network exit edges (from network to external nodes)
EXIT_EDGES = {
    'east': ['J6_to_N_out_6', 'J3_to_N_out_3e', 'J9_to_N_out_9s', 'J9_to_N_out_9'],
    'west': ['J4_to_N_out_4', 'J1_to_N_out_1w', 'J7_to_N_out_7s', 'J7_to_N_out_7'],
    'north': ['J1_to_N_out_1', 'J2_to_N_out_2', 'J3_to_N_out_3'],
    'south': ['J7_to_N_out_7', 'J8_to_N_out_8', 'J9_to_N_out_9']
}


def rush_hour_demand_multiplier(time_seconds):
    """
    Calculate demand multiplier based on time of day (rush hour pattern).

    Simulates Vietnamese rush hour (evening commute):
    - 0-900s (0-15min): Build-up phase (60% → 100%)
    - 900-2700s (15-45min): Peak rush hour (100%)
    - 2700-3600s (45-60min): Taper off (100% → 40%)

    Args:
        time_seconds: Time in simulation (0-3600)

    Returns:
        Demand multiplier (0.4 to 1.0)
    """
    if time_seconds < 900:
        # Build-up: linear ramp from 0.6 to 1.0
        return 0.6 + 0.4 * (time_seconds / 900)
    elif time_seconds < 2700:
        # Peak rush hour: constant maximum
        return 1.0
    else:
        # Taper off: linear decline from 1.0 to 0.4
        return 1.0 - 0.6 * ((time_seconds - 2700) / 900)


def create_trips_with_rush_hour(from_edges, to_edges, count, vtype, prefix,
                                  simulation_time=3600, platoon_size=3, seed=42):
    """
    Generate trips with rush hour demand pattern and platoon effects.

    Args:
        from_edges: List of origin edges
        to_edges: List of destination edges
        count: Total number of trips to generate
        vtype: Vehicle type ID
        prefix: Trip ID prefix
        simulation_time: Total simulation time (seconds)
        platoon_size: Average number of vehicles per platoon (creates waves)
        seed: Random seed for reproducibility

    Returns:
        List of trip dictionaries
    """
    random.seed(seed)
    trips = []

    # Calculate base interval assuming uniform distribution
    base_interval = simulation_time / count

    current_time = 0
    vehicle_count = 0

    while vehicle_count < count and current_time < simulation_time:
        # Get demand multiplier for current time
        demand_mult = rush_hour_demand_multiplier(current_time)

        # Adjusted interval based on demand (higher demand = shorter interval)
        adjusted_interval = base_interval / demand_mult

        # Add platoon effect: group vehicles in small clusters
        # Randomly decide if this is start of a platoon
        if random.random() < 0.3:  # 30% chance of platoon
            # Generate platoon of 2-5 vehicles close together
            platoon_count = min(
                random.randint(2, platoon_size + 2),
                count - vehicle_count
            )

            for p in range(platoon_count):
                if vehicle_count >= count:
                    break

                # Vehicles in platoon depart within 1-3 seconds of each other
                platoon_offset = p * random.uniform(1.0, 3.0)
                depart = current_time + platoon_offset

                if depart >= simulation_time:
                    break

                # Random O-D selection
                from_edge = random.choice(from_edges)
                to_edge = random.choice(to_edges)

                # Ensure not same edge
                while from_edge == to_edge:
                    to_edge = random.choice(to_edges)

                trips.append({
                    'id': f"{prefix}{vehicle_count}",
                    'depart': f"{depart:.2f}",
                    'from': from_edge,
                    'to': to_edge,
                    'type': vtype
                })

                vehicle_count += 1

            # Jump ahead after platoon
            current_time += adjusted_interval
        else:
            # Single vehicle (not in platoon)
            # Add some variance (±20%)
            variance = adjusted_interval * 0.2
            depart = current_time + random.uniform(-variance, variance)
            depart = max(0.0, min(depart, simulation_time - 1))

            # Random O-D selection
            from_edge = random.choice(from_edges)
            to_edge = random.choice(to_edges)

            # Ensure not same edge
            while from_edge == to_edge:
                to_edge = random.choice(to_edges)

            trips.append({
                'id': f"{prefix}{vehicle_count}",
                'depart': f"{depart:.2f}",
                'from': from_edge,
                'to': to_edge,
                'type': vtype
            })

            vehicle_count += 1
            current_time += adjusted_interval

    return trips[:count]  # Ensure exactly 'count' trips


def write_trips_xml(trips, filename):
    """Write trips to XML file in SUMO format."""
    root = ET.Element('routes')
    root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    root.set('xsi:noNamespaceSchemaLocation', 'http://sumo.dlr.de/xsd/routes_file.xsd')

    # Sort by departure time
    trips_sorted = sorted(trips, key=lambda t: float(t['depart']))

    for trip in trips_sorted:
        trip_elem = ET.SubElement(root, 'trip')
        trip_elem.set('id', trip['id'])
        trip_elem.set('depart', trip['depart'])
        trip_elem.set('from', trip['from'])
        trip_elem.set('to', trip['to'])
        trip_elem.set('type', trip['type'])
        trip_elem.set('departLane', 'best')
        trip_elem.set('departSpeed', 'max')

    # Pretty print
    xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="    ")

    with open(filename, 'w') as f:
        f.write(xml_str)

    print(f"  Generated {len(trips)} trips -> {filename}")


def main():
    print("="*60)
    print("Generating REALISTIC Vietnamese Rush Hour Traffic")
    print("="*60)
    print()
    print("Features:")
    print("  • 4,200 vehicles (115% increase for realistic congestion)")
    print("  • Time-varying demand (rush hour pattern)")
    print("  • Platoon effects (traffic waves)")
    print("  • 80% motorcycles, heavy westbound flow")
    print()

    SIMULATION_TIME = 3600  # 1 hour

    # ========================================================================
    # MOTORCYCLES (80% of traffic, ~3400 total)
    # ========================================================================
    print("Generating MOTORCYCLES (80% of traffic):")
    print("-" * 60)

    print("1. Motorcycles - WESTBOUND HEAVY (East→West)")
    motorcycle_wb = create_trips_with_rush_hour(
        from_edges=ENTRY_EDGES['east'],
        to_edges=EXIT_EDGES['west'],
        count=2000,  # Heavy westbound rush (2.5x increase)
        vtype='motorcycle',
        prefix='motorcycle_wb_',
        simulation_time=SIMULATION_TIME,
        platoon_size=4,  # Motorcycles travel in larger groups
        seed=42
    )
    write_trips_xml(motorcycle_wb, 'vn2.motorcycle.wb.trips.xml')

    print("2. Motorcycles - EASTBOUND MEDIUM (West→East)")
    motorcycle_eb = create_trips_with_rush_hour(
        from_edges=ENTRY_EDGES['west'],
        to_edges=EXIT_EDGES['east'],
        count=800,  # Medium eastbound counter-flow (2x increase)
        vtype='motorcycle',
        prefix='motorcycle_eb_',
        simulation_time=SIMULATION_TIME,
        platoon_size=3,
        seed=43
    )
    write_trips_xml(motorcycle_eb, 'vn2.motorcycle.eb.trips.xml')

    print("3. Motorcycles - NORTH-SOUTH (Bidirectional)")
    motorcycle_ns = create_trips_with_rush_hour(
        from_edges=ENTRY_EDGES['north'] + ENTRY_EDGES['south'],
        to_edges=EXIT_EDGES['north'] + EXIT_EDGES['south'],
        count=600,  # Light N-S cross-traffic (1.5x increase)
        vtype='motorcycle',
        prefix='motorcycle_ns_',
        simulation_time=SIMULATION_TIME,
        platoon_size=3,
        seed=44
    )
    write_trips_xml(motorcycle_ns, 'vn2.motorcycle.ns.trips.xml')

    # ========================================================================
    # CARS (15% of traffic, ~570 total)
    # ========================================================================
    print("\nGenerating CARS (15% of traffic):")
    print("-" * 60)

    print("4. Cars - WESTBOUND HEAVY (East→West)")
    car_wb = create_trips_with_rush_hour(
        from_edges=ENTRY_EDGES['east'],
        to_edges=EXIT_EDGES['west'],
        count=300,  # Heavy westbound (2.5x increase)
        vtype='car',
        prefix='car_wb_',
        simulation_time=SIMULATION_TIME,
        platoon_size=2,  # Cars in smaller groups
        seed=45
    )
    write_trips_xml(car_wb, 'vn2.car.wb.trips.xml')

    print("5. Cars - EASTBOUND MEDIUM (West→East)")
    car_eb = create_trips_with_rush_hour(
        from_edges=ENTRY_EDGES['west'],
        to_edges=EXIT_EDGES['east'],
        count=150,  # Medium eastbound (2.5x increase)
        vtype='car',
        prefix='car_eb_',
        simulation_time=SIMULATION_TIME,
        platoon_size=2,
        seed=46
    )
    write_trips_xml(car_eb, 'vn2.car.eb.trips.xml')

    print("6. Cars - NORTH-SOUTH (Bidirectional)")
    car_ns = create_trips_with_rush_hour(
        from_edges=ENTRY_EDGES['north'] + ENTRY_EDGES['south'],
        to_edges=EXIT_EDGES['north'] + EXIT_EDGES['south'],
        count=120,  # Cross-traffic (2x increase)
        vtype='car',
        prefix='car_ns_',
        simulation_time=SIMULATION_TIME,
        platoon_size=2,
        seed=47
    )
    write_trips_xml(car_ns, 'vn2.car.ns.trips.xml')

    # ========================================================================
    # COMMERCIAL VEHICLES (5% of traffic, ~230 total)
    # ========================================================================
    print("\nGenerating COMMERCIAL VEHICLES (5% of traffic):")
    print("-" * 60)

    # All fringe edges combined for uniform distribution
    all_entry = ENTRY_EDGES['east'] + ENTRY_EDGES['west'] + ENTRY_EDGES['north'] + ENTRY_EDGES['south']
    all_exit = EXIT_EDGES['east'] + EXIT_EDGES['west'] + EXIT_EDGES['north'] + EXIT_EDGES['south']

    print("7. Delivery vehicles (uniform)")
    delivery = create_trips_with_rush_hour(
        from_edges=all_entry,
        to_edges=all_exit,
        count=100,  # More deliveries during rush hour
        vtype='delivery',
        prefix='delivery_',
        simulation_time=SIMULATION_TIME,
        platoon_size=1,  # Usually travel alone
        seed=48
    )
    write_trips_xml(delivery, 'vn2.delivery.trips.xml')

    print("8. Buses (uniform)")
    bus = create_trips_with_rush_hour(
        from_edges=all_entry,
        to_edges=all_exit,
        count=80,  # More buses during peak (reduces capacity!)
        vtype='bus',
        prefix='bus_',
        simulation_time=SIMULATION_TIME,
        platoon_size=1,
        seed=49
    )
    write_trips_xml(bus, 'vn2.bus.trips.xml')

    print("9. Trucks (uniform)")
    truck = create_trips_with_rush_hour(
        from_edges=all_entry,
        to_edges=all_exit,
        count=50,  # Trucks add capacity constraints
        vtype='truck',
        prefix='truck_',
        simulation_time=SIMULATION_TIME,
        platoon_size=1,
        seed=50
    )
    write_trips_xml(truck, 'vn2.truck.trips.xml')

    # ========================================================================
    # SUMMARY
    # ========================================================================
    motorcycle_total = 2000 + 800 + 600
    car_total = 300 + 150 + 120
    commercial_total = 100 + 80 + 50
    total_vehicles = motorcycle_total + car_total + commercial_total

    print()
    print("="*60)
    print("Trip Generation Complete!")
    print("="*60)
    print()
    print(f"Total vehicles: {total_vehicles} (+115% from original 1,950)")
    print(f"  Motorcycles: {motorcycle_total} ({100*motorcycle_total/total_vehicles:.1f}%)")
    print(f"  Cars: {car_total} ({100*car_total/total_vehicles:.1f}%)")
    print(f"  Commercial: {commercial_total} ({100*commercial_total/total_vehicles:.1f}%)")
    print()
    print("Directional bias (motorcycles + cars):")
    wb_total = 2000 + 300
    eb_total = 800 + 150
    ns_total = 600 + 120
    print(f"  Westbound: {wb_total} vehicles ({100*wb_total/(motorcycle_total+car_total):.1f}%) ← HEAVY RUSH")
    print(f"  Eastbound: {eb_total} vehicles ({100*eb_total/(motorcycle_total+car_total):.1f}%)")
    print(f"  North-South: {ns_total} vehicles ({100*ns_total/(motorcycle_total+car_total):.1f}%)")
    print(f"  Uniform: {commercial_total} vehicles ({100*commercial_total/total_vehicles:.1f}%)")
    print()
    print("Traffic pattern:")
    print("  • 0-15min (0-900s): Build-up phase (60-100% demand)")
    print("  • 15-45min (900-2700s): Peak rush hour (100% demand)")
    print("  • 45-60min (2700-3600s): Taper off (100-40% demand)")
    print()
    print("Expected behavior:")
    print("  • Network capacity utilization: 70-85%")
    print("  • Significant congestion but solvable")
    print("  • RL agent MUST learn coordination")
    print()
    print("Next step: Run duarouter to create vn2.rou.xml")


if __name__ == '__main__':
    main()
