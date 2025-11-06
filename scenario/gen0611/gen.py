#!/usr/bin/env python3
"""
SUMO Vietnamese Traffic Grid Network Generator - FIXED VERSION
Creates a 3x3 grid network with Vietnamese traffic characteristics
"""

import os
import subprocess
import random
import xml.etree.ElementTree as ET
from xml.dom import minidom

class VietnameseTrafficGenerator:
    def __init__(self, output_dir="vietnamese_traffic_3x3", difficulty="easy"):
        """
        Initialize Vietnamese Traffic Generator

        Args:
            output_dir: Directory to save generated files
            difficulty: Traffic difficulty level
                - "easy": 50% traffic (1350 vph) - RECOMMENDED for initial RL training
                - "medium": 65% traffic (1755 vph) - intermediate training
                - "hard": 80% traffic (2160 vph) - advanced training
                - "very_hard": 100% traffic (2700 vph) - stress testing
        """
        self.output_dir = output_dir
        self.grid_size = 3
        self.block_length = 200
        self.num_lanes = 2
        self.difficulty = difficulty

        self.vehicle_distribution = {
            'motorcycle': 0.75,
            'car': 0.20,
            'bus_truck': 0.05
        }

        # Base flow patterns (100% - very_hard difficulty)
        base_flows = {
            'west_to_east': 1200,
            'east_to_west': 600,
            'north_to_south': 400,
            'south_to_north': 500,
        }

        # Apply difficulty multiplier
        difficulty_multipliers = {
            'easy': 0.5,      # 50% - ideal for RL learning (22.5% utilization)
            'medium': 0.65,   # 65% - intermediate challenge (29% utilization)
            'hard': 0.8,      # 80% - advanced training (36% utilization)
            'very_hard': 1.0  # 100% - original high density (45% utilization)
        }

        multiplier = difficulty_multipliers.get(difficulty, 0.5)
        self.flow_patterns = {
            key: int(value * multiplier)
            for key, value in base_flows.items()
        }

        # Calculate total flow for reporting
        self.total_flow = sum(self.flow_patterns.values())
        self.utilization_pct = (self.total_flow / 6000) * 100  # 6000 vph theoretical max

        os.makedirs(self.output_dir, exist_ok=True)

    def generate_nodes(self):
        """Generate nodes for 3x3 grid with entry/exit nodes"""
        nodes_file = os.path.join(self.output_dir, "grid.nod.xml")

        root = ET.Element("nodes")

        # Internal intersection nodes (3x3 = 9 nodes)
        node_id = 0
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                node = ET.SubElement(root, "node")
                node.set("id", f"n{node_id}")
                node.set("x", str(col * self.block_length))
                node.set("y", str(row * self.block_length))
                node.set("type", "traffic_light")
                node_id += 1

        # Entry/exit nodes - North
        for col in range(self.grid_size):
            node = ET.SubElement(root, "node")
            node.set("id", f"n_north_{col}")
            node.set("x", str(col * self.block_length))
            node.set("y", str(self.grid_size * self.block_length))
            node.set("type", "priority")

        # Entry/exit nodes - South
        for col in range(self.grid_size):
            node = ET.SubElement(root, "node")
            node.set("id", f"n_south_{col}")
            node.set("x", str(col * self.block_length))
            node.set("y", str(-self.block_length))
            node.set("type", "priority")

        # Entry/exit nodes - East
        for row in range(self.grid_size):
            node = ET.SubElement(root, "node")
            node.set("id", f"n_east_{row}")
            node.set("x", str(self.grid_size * self.block_length))
            node.set("y", str(row * self.block_length))
            node.set("type", "priority")

        # Entry/exit nodes - West
        for row in range(self.grid_size):
            node = ET.SubElement(root, "node")
            node.set("id", f"n_west_{row}")
            node.set("x", str(-self.block_length))
            node.set("y", str(row * self.block_length))
            node.set("type", "priority")

        self._write_xml(root, nodes_file)
        print(f"✓ Generated nodes file: {nodes_file}")
        return nodes_file

    def generate_edges(self):
        """Generate edges connecting nodes"""
        edges_file = os.path.join(self.output_dir, "grid.edg.xml")

        root = ET.Element("edges")

        edge_id = 0

        # Horizontal edges
        for row in range(self.grid_size):
            for col in range(self.grid_size - 1):
                # West to East
                edge = ET.SubElement(root, "edge")
                edge.set("id", f"e{edge_id}")
                edge.set("from", f"n{row * self.grid_size + col}")
                edge.set("to", f"n{row * self.grid_size + col + 1}")
                edge.set("numLanes", str(self.num_lanes))
                edge.set("speed", "13.89")
                edge_id += 1

                # East to West
                edge = ET.SubElement(root, "edge")
                edge.set("id", f"e{edge_id}")
                edge.set("from", f"n{row * self.grid_size + col + 1}")
                edge.set("to", f"n{row * self.grid_size + col}")
                edge.set("numLanes", str(self.num_lanes))
                edge.set("speed", "13.89")
                edge_id += 1

        # Vertical edges
        for col in range(self.grid_size):
            for row in range(self.grid_size - 1):
                # South to North
                edge = ET.SubElement(root, "edge")
                edge.set("id", f"e{edge_id}")
                edge.set("from", f"n{row * self.grid_size + col}")
                edge.set("to", f"n{(row + 1) * self.grid_size + col}")
                edge.set("numLanes", str(self.num_lanes))
                edge.set("speed", "13.89")
                edge_id += 1

                # North to South
                edge = ET.SubElement(root, "edge")
                edge.set("id", f"e{edge_id}")
                edge.set("from", f"n{(row + 1) * self.grid_size + col}")
                edge.set("to", f"n{row * self.grid_size + col}")
                edge.set("numLanes", str(self.num_lanes))
                edge.set("speed", "13.89")
                edge_id += 1

        # Entry/Exit edges - North
        for col in range(self.grid_size):
            edge = ET.SubElement(root, "edge")
            edge.set("id", f"e{edge_id}")
            edge.set("from", f"n_north_{col}")
            edge.set("to", f"n{(self.grid_size - 1) * self.grid_size + col}")
            edge.set("numLanes", str(self.num_lanes))
            edge.set("speed", "13.89")
            edge_id += 1

            edge = ET.SubElement(root, "edge")
            edge.set("id", f"e{edge_id}")
            edge.set("from", f"n{(self.grid_size - 1) * self.grid_size + col}")
            edge.set("to", f"n_north_{col}")
            edge.set("numLanes", str(self.num_lanes))
            edge.set("speed", "13.89")
            edge_id += 1

        # Entry/Exit edges - South
        for col in range(self.grid_size):
            edge = ET.SubElement(root, "edge")
            edge.set("id", f"e{edge_id}")
            edge.set("from", f"n_south_{col}")
            edge.set("to", f"n{col}")
            edge.set("numLanes", str(self.num_lanes))
            edge.set("speed", "13.89")
            edge_id += 1

            edge = ET.SubElement(root, "edge")
            edge.set("id", f"e{edge_id}")
            edge.set("from", f"n{col}")
            edge.set("to", f"n_south_{col}")
            edge.set("numLanes", str(self.num_lanes))
            edge.set("speed", "13.89")
            edge_id += 1

        # Entry/Exit edges - East
        for row in range(self.grid_size):
            edge = ET.SubElement(root, "edge")
            edge.set("id", f"e{edge_id}")
            edge.set("from", f"n_east_{row}")
            edge.set("to", f"n{row * self.grid_size + (self.grid_size - 1)}")
            edge.set("numLanes", str(self.num_lanes))
            edge.set("speed", "13.89")
            edge_id += 1

            edge = ET.SubElement(root, "edge")
            edge.set("id", f"e{edge_id}")
            edge.set("from", f"n{row * self.grid_size + (self.grid_size - 1)}")
            edge.set("to", f"n_east_{row}")
            edge.set("numLanes", str(self.num_lanes))
            edge.set("speed", "13.89")
            edge_id += 1

        # Entry/Exit edges - West
        for row in range(self.grid_size):
            edge = ET.SubElement(root, "edge")
            edge.set("id", f"e{edge_id}")
            edge.set("from", f"n_west_{row}")
            edge.set("to", f"n{row * self.grid_size}")
            edge.set("numLanes", str(self.num_lanes))
            edge.set("speed", "13.89")
            edge_id += 1

            edge = ET.SubElement(root, "edge")
            edge.set("id", f"e{edge_id}")
            edge.set("from", f"n{row * self.grid_size}")
            edge.set("to", f"n_west_{row}")
            edge.set("numLanes", str(self.num_lanes))
            edge.set("speed", "13.89")
            edge_id += 1

        self._write_xml(root, edges_file)
        print(f"✓ Generated edges file: {edges_file}")
        return edges_file

    def generate_vehicle_types(self):
        """Define Vietnamese vehicle types"""
        vtypes_file = os.path.join(self.output_dir, "vtypes.add.xml")

        root = ET.Element("additional")

        # Motorcycle
        vtype = ET.SubElement(root, "vType")
        vtype.set("id", "motorcycle")
        vtype.set("vClass", "motorcycle")
        vtype.set("length", "2.0")
        vtype.set("width", "0.8")
        vtype.set("maxSpeed", "16.67")
        vtype.set("accel", "2.5")
        vtype.set("decel", "4.5")
        vtype.set("color", "yellow")

        # Car
        vtype = ET.SubElement(root, "vType")
        vtype.set("id", "car")
        vtype.set("vClass", "passenger")
        vtype.set("length", "4.5")
        vtype.set("width", "1.8")
        vtype.set("maxSpeed", "19.44")
        vtype.set("accel", "2.0")
        vtype.set("decel", "4.0")
        vtype.set("color", "blue")

        # Bus/Truck
        vtype = ET.SubElement(root, "vType")
        vtype.set("id", "bus_truck")
        vtype.set("vClass", "bus")
        vtype.set("length", "10.0")
        vtype.set("width", "2.5")
        vtype.set("maxSpeed", "13.89")
        vtype.set("accel", "1.0")
        vtype.set("decel", "3.0")
        vtype.set("color", "red")

        self._write_xml(root, vtypes_file)
        print(f"✓ Generated vehicle types file: {vtypes_file}")
        return vtypes_file

    def generate_traffic_light_programs(self):
        """Generate 6-phase traffic light programs with protected left turns"""
        tls_file = os.path.join(self.output_dir, "tls.add.xml")

        root = ET.Element("additional")

        # Generate traffic light program for each of the 9 intersections
        for node_id in range(9):
            tlLogic = ET.SubElement(root, "tlLogic")
            tlLogic.set("id", f"n{node_id}")
            tlLogic.set("type", "static")
            tlLogic.set("programID", "custom")
            tlLogic.set("offset", "0")

            # 6-phase program with proper yellow transitions
            # State indices: 0-3=EW-approach1, 4-7=NS-approach1, 8-11=EW-approach2, 12-15=NS-approach2
            # Each approach: [right, through-lane1, through-lane2, left]

            # Phase 1: East-West through + right (30s)
            phase = ET.SubElement(tlLogic, "phase")
            phase.set("duration", "30")
            phase.set("state", "GGGrrrrrGGGrrrrr")  # Indices 0-2 and 8-10 green (EW through+right)

            # Phase 2: East-West protected left turn (10s)
            phase = ET.SubElement(tlLogic, "phase")
            phase.set("duration", "10")
            phase.set("state", "rrrGrrrrrrrGrrrr")  # Indices 3 and 11 green (EW left turns)

            # Phase 3: East-West yellow (4s - increased for safety)
            phase = ET.SubElement(tlLogic, "phase")
            phase.set("duration", "4")
            phase.set("state", "yyyyrrrryyyyrrrr")  # Yellow for indices that were green in phases 1-2

            # Phase 3b: All-red clearance (2s - prevent collisions)
            phase = ET.SubElement(tlLogic, "phase")
            phase.set("duration", "2")
            phase.set("state", "rrrrrrrrrrrrrrrr")  # All red to clear intersection

            # Phase 4: North-South through + right (30s)
            phase = ET.SubElement(tlLogic, "phase")
            phase.set("duration", "30")
            phase.set("state", "rrrrGGGrrrrrGGGr")  # Indices 4-6 and 12-14 green (NS through+right)

            # Phase 5: North-South protected left turn (10s)
            phase = ET.SubElement(tlLogic, "phase")
            phase.set("duration", "10")
            phase.set("state", "rrrrrrrGrrrrrrrG")  # Indices 7 and 15 green (NS left turns)

            # Phase 6: North-South yellow (4s - increased for safety)
            phase = ET.SubElement(tlLogic, "phase")
            phase.set("duration", "4")
            phase.set("state", "rrrryyyyrrrryyyy")  # Yellow for indices that were green in phases 4-5

            # Phase 6b: All-red clearance (2s - prevent collisions)
            phase = ET.SubElement(tlLogic, "phase")
            phase.set("duration", "2")
            phase.set("state", "rrrrrrrrrrrrrrrr")  # All red to clear intersection

        # Add WAUT to switch to custom programs
        waut = ET.SubElement(root, "WAUT")
        waut.set("id", "use_custom")
        waut.set("startProg", "custom")
        waut.set("refTime", "0")

        for node_id in range(9):
            wautJunction = ET.SubElement(waut, "wautJunction")
            wautJunction.set("junctionID", f"n{node_id}")
            wautJunction.set("procedureOnChange", "0")
            wautJunction.set("wautID", "use_custom")

        self._write_xml(root, tls_file)
        print(f"✓ Generated traffic light programs file: {tls_file}")
        print(f"  - 6-phase programs with protected left turns")
        print(f"  - Phase durations: EW(30s) → EW-left(10s) → NS(30s) → NS-left(10s)")
        return tls_file

    def _get_edge_map(self):
        """Build edge ID mapping for route generation"""
        edge_map = {}
        edge_id = 0

        # Horizontal edges
        for row in range(self.grid_size):
            for col in range(self.grid_size - 1):
                edge_map[f"h_we_{row}_{col}"] = f"e{edge_id}"
                edge_id += 1
                edge_map[f"h_ew_{row}_{col}"] = f"e{edge_id}"
                edge_id += 1

        # Vertical edges
        for col in range(self.grid_size):
            for row in range(self.grid_size - 1):
                edge_map[f"v_sn_{col}_{row}"] = f"e{edge_id}"
                edge_id += 1
                edge_map[f"v_ns_{col}_{row}"] = f"e{edge_id}"
                edge_id += 1

        # Entry/Exit edges
        for col in range(self.grid_size):
            edge_map[f"entry_north_{col}"] = f"e{edge_id}"
            edge_id += 1
            edge_map[f"exit_north_{col}"] = f"e{edge_id}"
            edge_id += 1

        for col in range(self.grid_size):
            edge_map[f"entry_south_{col}"] = f"e{edge_id}"
            edge_id += 1
            edge_map[f"exit_south_{col}"] = f"e{edge_id}"
            edge_id += 1

        for row in range(self.grid_size):
            edge_map[f"entry_east_{row}"] = f"e{edge_id}"
            edge_id += 1
            edge_map[f"exit_east_{row}"] = f"e{edge_id}"
            edge_id += 1

        for row in range(self.grid_size):
            edge_map[f"entry_west_{row}"] = f"e{edge_id}"
            edge_id += 1
            edge_map[f"exit_west_{row}"] = f"e{edge_id}"
            edge_id += 1

        return edge_map

    def generate_routes(self):
        """Generate explicit edge-based routes with turning movements"""
        routes_file = os.path.join(self.output_dir, "routes.rou.xml")

        root = ET.Element("routes")

        # Include vehicle types
        include = ET.SubElement(root, "include")
        include.set("href", "vtypes.add.xml")

        edge_map = self._get_edge_map()
        flow_id = 0
        route_count = 0

        # West to East flows (HEAVY)
        print("\nGenerating West→East routes...")
        for row in range(self.grid_size):
            straight_edges = [
                edge_map[f"entry_west_{row}"],
                edge_map[f"h_we_{row}_0"],
                edge_map[f"h_we_{row}_1"],
                edge_map[f"exit_east_{row}"]
            ]

            turn_north_edges = None
            if row < self.grid_size - 1:
                turn_north_edges = [
                    edge_map[f"entry_west_{row}"],
                    edge_map[f"h_we_{row}_0"],
                    edge_map[f"v_sn_1_{row}"],
                    edge_map[f"h_we_{row+1}_1"],
                    edge_map[f"exit_east_{row+1}"]
                ]

            turn_south_edges = None
            if row > 0:
                turn_south_edges = [
                    edge_map[f"entry_west_{row}"],
                    edge_map[f"h_we_{row}_0"],
                    edge_map[f"v_ns_1_{row-1}"],
                    edge_map[f"h_we_{row-1}_1"],
                    edge_map[f"exit_east_{row-1}"]
                ]

            flow_id = self._add_flows(root, flow_id, straight_edges, turn_north_edges,
                                     turn_south_edges, self.flow_patterns['west_to_east'])
            route_count += (2 if turn_north_edges or turn_south_edges else 1) + (1 if turn_south_edges and turn_north_edges else 0)

        # East to West flows (MODERATE)
        print("Generating East→West routes...")
        for row in range(self.grid_size):
            straight_edges = [
                edge_map[f"entry_east_{row}"],
                edge_map[f"h_ew_{row}_1"],
                edge_map[f"h_ew_{row}_0"],
                edge_map[f"exit_west_{row}"]
            ]

            turn_north_edges = None
            if row < self.grid_size - 1:
                turn_north_edges = [
                    edge_map[f"entry_east_{row}"],
                    edge_map[f"h_ew_{row}_1"],
                    edge_map[f"v_sn_1_{row}"],
                    edge_map[f"h_ew_{row+1}_0"],
                    edge_map[f"exit_west_{row+1}"]
                ]

            turn_south_edges = None
            if row > 0:
                turn_south_edges = [
                    edge_map[f"entry_east_{row}"],
                    edge_map[f"h_ew_{row}_1"],
                    edge_map[f"v_ns_1_{row-1}"],
                    edge_map[f"h_ew_{row-1}_0"],
                    edge_map[f"exit_west_{row-1}"]
                ]

            flow_id = self._add_flows(root, flow_id, straight_edges, turn_north_edges,
                                     turn_south_edges, self.flow_patterns['east_to_west'])
            route_count += (2 if turn_north_edges or turn_south_edges else 1) + (1 if turn_south_edges and turn_north_edges else 0)

        # North to South flows (LIGHT)
        print("Generating North→South routes...")
        for col in range(self.grid_size):
            straight_edges = [
                edge_map[f"entry_north_{col}"],
                edge_map[f"v_ns_{col}_1"],
                edge_map[f"v_ns_{col}_0"],
                edge_map[f"exit_south_{col}"]
            ]

            turn_east_edges = None
            if col < self.grid_size - 1:
                turn_east_edges = [
                    edge_map[f"entry_north_{col}"],
                    edge_map[f"v_ns_{col}_1"],
                    edge_map[f"h_we_1_{col}"],
                    edge_map[f"v_ns_{col+1}_0"],
                    edge_map[f"exit_south_{col+1}"]
                ]

            turn_west_edges = None
            if col > 0:
                turn_west_edges = [
                    edge_map[f"entry_north_{col}"],
                    edge_map[f"v_ns_{col}_1"],
                    edge_map[f"h_ew_1_{col-1}"],
                    edge_map[f"v_ns_{col-1}_0"],
                    edge_map[f"exit_south_{col-1}"]
                ]

            flow_id = self._add_flows(root, flow_id, straight_edges, turn_east_edges,
                                     turn_west_edges, self.flow_patterns['north_to_south'])
            route_count += (2 if turn_east_edges or turn_west_edges else 1) + (1 if turn_west_edges and turn_east_edges else 0)

        # South to North flows (LIGHT-MODERATE)
        print("Generating South→North routes...")
        for col in range(self.grid_size):
            straight_edges = [
                edge_map[f"entry_south_{col}"],
                edge_map[f"v_sn_{col}_0"],
                edge_map[f"v_sn_{col}_1"],
                edge_map[f"exit_north_{col}"]
            ]

            turn_east_edges = None
            if col < self.grid_size - 1:
                turn_east_edges = [
                    edge_map[f"entry_south_{col}"],
                    edge_map[f"v_sn_{col}_0"],
                    edge_map[f"h_we_1_{col}"],
                    edge_map[f"v_sn_{col+1}_1"],
                    edge_map[f"exit_north_{col+1}"]
                ]

            turn_west_edges = None
            if col > 0:
                turn_west_edges = [
                    edge_map[f"entry_south_{col}"],
                    edge_map[f"v_sn_{col}_0"],
                    edge_map[f"h_ew_1_{col-1}"],
                    edge_map[f"v_sn_{col-1}_1"],
                    edge_map[f"exit_north_{col-1}"]
                ]

            flow_id = self._add_flows(root, flow_id, straight_edges, turn_east_edges,
                                     turn_west_edges, self.flow_patterns['south_to_north'])
            route_count += (2 if turn_east_edges or turn_west_edges else 1) + (1 if turn_west_edges and turn_east_edges else 0)

        self._write_xml(root, routes_file)
        print(f"✓ Generated routes file: {routes_file}")
        print(f"  - Total route variants: ~{route_count}")
        print(f"  - Total flows created: {flow_id}")
        print(f"  - Route distribution: 70% straight, 30% turns")
        print(f"  - All routes: 4-5 edges (max 6-8 edges requirement met)")
        return routes_file

    def _add_flows(self, root, flow_id, straight_edges, turn_edges_1, turn_edges_2, veh_per_hour):
        """Add flows with route distribution for each vehicle type"""

        motorcycle_vph = int(veh_per_hour * self.vehicle_distribution['motorcycle'])
        car_vph = int(veh_per_hour * self.vehicle_distribution['car'])
        bus_truck_vph = int(veh_per_hour * self.vehicle_distribution['bus_truck'])

        # Determine probabilities
        if turn_edges_1 is None and turn_edges_2 is None:
            probs = [1.0, 0.0, 0.0]
        elif turn_edges_1 is None:
            probs = [0.7, 0.0, 0.3]
        elif turn_edges_2 is None:
            probs = [0.7, 0.3, 0.0]
        else:
            probs = [0.7, 0.15, 0.15]

        # Motorcycle flow
        if motorcycle_vph > 0:
            flow = ET.SubElement(root, "flow")
            flow.set("id", f"flow_{flow_id}")
            flow.set("type", "motorcycle")
            flow.set("begin", "0")
            flow.set("end", "3600")
            flow.set("vehsPerHour", str(motorcycle_vph))
            flow.set("departLane", "best")
            flow.set("departSpeed", "max")

            routeDist = ET.SubElement(flow, "routeDistribution")
            route = ET.SubElement(routeDist, "route")
            route.set("edges", " ".join(straight_edges))
            route.set("probability", str(probs[0]))

            if turn_edges_1:
                route = ET.SubElement(routeDist, "route")
                route.set("edges", " ".join(turn_edges_1))
                route.set("probability", str(probs[1]))

            if turn_edges_2:
                route = ET.SubElement(routeDist, "route")
                route.set("edges", " ".join(turn_edges_2))
                route.set("probability", str(probs[2]))

            flow_id += 1

        # Car flow
        if car_vph > 0:
            flow = ET.SubElement(root, "flow")
            flow.set("id", f"flow_{flow_id}")
            flow.set("type", "car")
            flow.set("begin", "0")
            flow.set("end", "3600")
            flow.set("vehsPerHour", str(car_vph))
            flow.set("departLane", "best")
            flow.set("departSpeed", "max")

            routeDist = ET.SubElement(flow, "routeDistribution")
            route = ET.SubElement(routeDist, "route")
            route.set("edges", " ".join(straight_edges))
            route.set("probability", str(probs[0]))

            if turn_edges_1:
                route = ET.SubElement(routeDist, "route")
                route.set("edges", " ".join(turn_edges_1))
                route.set("probability", str(probs[1]))

            if turn_edges_2:
                route = ET.SubElement(routeDist, "route")
                route.set("edges", " ".join(turn_edges_2))
                route.set("probability", str(probs[2]))

            flow_id += 1

        # Bus/Truck flow
        if bus_truck_vph > 0:
            flow = ET.SubElement(root, "flow")
            flow.set("id", f"flow_{flow_id}")
            flow.set("type", "bus_truck")
            flow.set("begin", "0")
            flow.set("end", "3600")
            flow.set("vehsPerHour", str(bus_truck_vph))
            flow.set("departLane", "best")
            flow.set("departSpeed", "max")

            routeDist = ET.SubElement(flow, "routeDistribution")
            route = ET.SubElement(routeDist, "route")
            route.set("edges", " ".join(straight_edges))
            route.set("probability", str(probs[0]))

            if turn_edges_1:
                route = ET.SubElement(routeDist, "route")
                route.set("edges", " ".join(turn_edges_1))
                route.set("probability", str(probs[1]))

            if turn_edges_2:
                route = ET.SubElement(routeDist, "route")
                route.set("edges", " ".join(turn_edges_2))
                route.set("probability", str(probs[2]))

            flow_id += 1

        return flow_id

    def generate_sumo_config(self, net_file):
        """Generate SUMO configuration file"""
        config_file = os.path.join(self.output_dir, "simulation.sumocfg")

        root = ET.Element("configuration")

        # Input section
        input_section = ET.SubElement(root, "input")
        net = ET.SubElement(input_section, "net-file")
        net.set("value", os.path.basename(net_file))
        route = ET.SubElement(input_section, "route-files")
        route.set("value", "routes.rou.xml")
        additional = ET.SubElement(input_section, "additional-files")
        additional.set("value", "tls.add.xml")

        # Time section
        time_section = ET.SubElement(root, "time")
        begin = ET.SubElement(time_section, "begin")
        begin.set("value", "0")
        end = ET.SubElement(time_section, "end")
        end.set("value", "3600")

        # Processing section
        proc_section = ET.SubElement(root, "processing")
        time_to_teleport = ET.SubElement(proc_section, "time-to-teleport")
        time_to_teleport.set("value", "-1")

        # Output section
        output_section = ET.SubElement(root, "output")
        tripinfo = ET.SubElement(output_section, "tripinfo-output")
        tripinfo.set("value", "tripinfo.xml")

        # Report section
        report_section = ET.SubElement(root, "report")
        verbose = ET.SubElement(report_section, "verbose")
        verbose.set("value", "true")
        no_warnings = ET.SubElement(report_section, "no-warnings")
        no_warnings.set("value", "false")

        self._write_xml(root, config_file)
        print(f"✓ Generated SUMO config file: {config_file}")
        return config_file

    def build_network(self, nodes_file, edges_file):
        """Build SUMO network from nodes and edges"""
        net_file = os.path.join(self.output_dir, "grid.net.xml")

        cmd = [
            "netconvert",
            "--node-files", nodes_file,
            "--edge-files", edges_file,
            "--output-file", net_file,
            "--no-turnarounds", "true",
            "--junctions.join", "true",
            "--tls.guess", "true",
            "--tls.default-type", "static"
        ]

        print("\n⚙ Building network with netconvert...")
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"✓ Generated network file: {net_file}")
            print(f"  - Turnarounds disabled to prevent vehicle cycling")
        except subprocess.CalledProcessError as e:
            print(f"✗ Error building network:")
            print(e.stderr)
            raise

        return net_file

    def _write_xml(self, root, filename):
        """Write XML to file with pretty formatting"""
        xml_str = ET.tostring(root, encoding='unicode')
        dom = minidom.parseString(xml_str)
        with open(filename, 'w') as f:
            f.write(dom.toprettyxml(indent="  "))

    def generate(self):
        """Generate complete SUMO scenario"""
        print("=" * 60)
        print("Vietnamese Traffic 3x3 Grid Generator")
        print("=" * 60)
        print(f"\nOutput directory: {self.output_dir}")
        print(f"Grid size: {self.grid_size}x{self.grid_size}")
        print(f"Block length: {self.block_length}m")
        print(f"Lanes per direction: {self.num_lanes}")
        print(f"\nVehicle distribution (Vietnamese traffic):")
        print(f"  - Motorcycles: {self.vehicle_distribution['motorcycle']*100:.0f}%")
        print(f"  - Cars: {self.vehicle_distribution['car']*100:.0f}%")
        print(f"  - Buses/Trucks: {self.vehicle_distribution['bus_truck']*100:.0f}%")

        print(f"\nTraffic difficulty: {self.difficulty.upper()}")
        print(f"  - Total flow: {self.total_flow} veh/hour")
        print(f"  - Network utilization: {self.utilization_pct:.1f}%")
        print(f"  - West→East: {self.flow_patterns['west_to_east']} vph")
        print(f"  - East→West: {self.flow_patterns['east_to_west']} vph")
        print(f"  - North→South: {self.flow_patterns['north_to_south']} vph")
        print(f"  - South→North: {self.flow_patterns['south_to_north']} vph")
        print("\n" + "-" * 60)

        print("\n[1/7] Generating nodes...")
        nodes_file = self.generate_nodes()

        print("\n[2/7] Generating edges...")
        edges_file = self.generate_edges()

        print("\n[3/7] Building network...")
        net_file = self.build_network(nodes_file, edges_file)

        print("\n[4/7] Generating vehicle types...")
        vtypes_file = self.generate_vehicle_types()

        print("\n[5/7] Generating traffic light programs...")
        tls_file = self.generate_traffic_light_programs()

        print("\n[6/7] Generating routes with flows...")
        routes_file = self.generate_routes()

        print("\n[7/7] Generating SUMO configuration...")
        config_file = self.generate_sumo_config(net_file)

        print("\n" + "=" * 60)
        print("✓ Generation complete!")
        print("=" * 60)
        print(f"\nKey improvements:")
        print(f"  ✓ Vehicles perform realistic turning movements (70/30 split)")
        print(f"  ✓ 8-phase signals with protected left turns + clearance")
        print(f"  ✓ No vehicle cycling (turnarounds disabled)")
        print(f"  ✓ Optimized for RL training ({self.difficulty} difficulty)")
        print(f"\nTraffic configuration:")
        print(f"  - Difficulty: {self.difficulty.upper()}")
        print(f"  - Total flow: {self.total_flow} veh/hour")
        print(f"  - Network utilization: {self.utilization_pct:.1f}%")
        if self.utilization_pct < 25:
            print(f"  - ✅ Ideal for RL training (plenty of room for optimization)")
        elif self.utilization_pct < 30:
            print(f"  - ✅ Good for RL training (clear optimization opportunities)")
        elif self.utilization_pct < 40:
            print(f"  - ⚠️  Challenging (limited optimization headroom)")
        else:
            print(f"  - ⚠️  Very challenging (may saturate quickly)")
        print(f"\nTo run the simulation:")
        print(f"  sumo-gui -c {config_file}")
        print(f"\nOr in command line mode:")
        print(f"  sumo -c {config_file}")
        print("\n" + "=" * 60)

        return config_file


def main():
    # Change difficulty here: "easy", "medium", "hard", or "very_hard"
    # "easy" is RECOMMENDED for initial RL training
    generator = VietnameseTrafficGenerator(
        output_dir="vietnamese_traffic_3x3",
        difficulty="easy"  # 50% traffic - ideal for learning
    )
    config_file = generator.generate()

    print("\n💡 Tips for RL traffic signal optimization:")
    print("  1. Start with 'easy' difficulty - agent learns faster")
    print("  2. Use TraCI to control traffic lights in real-time")
    print("  3. Monitor: queue lengths, wait times, throughput")
    print("  4. Reward: +throughput, -wait_time, -queue_length")
    print("  5. Once agent masters 'easy', try 'medium' then 'hard'")
    print("\n  To change difficulty, edit main() in gen.py:")
    print("    difficulty='easy'     # 1350 vph (22.5% util) - RECOMMENDED")
    print("    difficulty='medium'   # 1755 vph (29.3% util)")
    print("    difficulty='hard'     # 2160 vph (36.0% util)")
    print("    difficulty='very_hard' # 2700 vph (45.0% util)")


if __name__ == "__main__":
    main()
