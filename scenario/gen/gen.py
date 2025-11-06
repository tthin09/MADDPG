#!/usr/bin/env python3
"""
SUMO Vietnamese Traffic Grid Network Generator
Creates a 3x3 grid network with Vietnamese traffic characteristics
- Asymmetric flows (e.g., heavier west-to-east flow)
- Three vehicle types: small (motorcycle), medium (car), large (truck/bus)
- Distribution matching Vietnamese traffic (~75% motorcycles, ~20% cars, ~5% large vehicles)
"""

import os
import subprocess
import random
import xml.etree.ElementTree as ET
from xml.dom import minidom

class VietnameseTrafficGenerator:
    def __init__(self, output_dir="vietnamese_traffic_3x3"):
        self.output_dir = output_dir
        self.grid_size = 3  # 3x3 grid
        self.block_length = 200  # meters between intersections
        self.num_lanes = 2  # lanes per direction
        
        # Vietnamese traffic distribution
        self.vehicle_distribution = {
            'motorcycle': 0.75,  # 75% motorcycles
            'car': 0.20,          # 20% cars
            'bus_truck': 0.05     # 5% buses/trucks
        }
        
        # Asymmetric flow patterns (vehicles per hour)
        # West-to-East flow is heavier (simulating main traffic corridor)
        self.flow_patterns = {
            'west_to_east': 1200,    # Heavy flow
            'east_to_west': 600,     # Moderate flow
            'north_to_south': 400,   # Light flow
            'south_to_north': 500,   # Light-moderate flow
        }
        
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_nodes(self):
        """Generate nodes for 3x3 grid with entry/exit nodes"""
        nodes_file = os.path.join(self.output_dir, "grid.nod.xml")
        
        root = ET.Element("nodes")
        
        # Generate internal intersection nodes (3x3 = 9 nodes)
        node_id = 0
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                node = ET.SubElement(root, "node")
                node.set("id", f"n{node_id}")
                node.set("x", str(col * self.block_length))
                node.set("y", str(row * self.block_length))
                node.set("type", "traffic_light")
                node_id += 1
        
        # Generate entry/exit nodes around the perimeter
        # North side (top)
        for col in range(self.grid_size):
            node = ET.SubElement(root, "node")
            node.set("id", f"n_north_{col}")
            node.set("x", str(col * self.block_length))
            node.set("y", str(self.grid_size * self.block_length))
            node.set("type", "priority")
        
        # South side (bottom)
        for col in range(self.grid_size):
            node = ET.SubElement(root, "node")
            node.set("id", f"n_south_{col}")
            node.set("x", str(col * self.block_length))
            node.set("y", str(-self.block_length))
            node.set("type", "priority")
        
        # East side (right)
        for row in range(self.grid_size):
            node = ET.SubElement(root, "node")
            node.set("id", f"n_east_{row}")
            node.set("x", str(self.grid_size * self.block_length))
            node.set("y", str(row * self.block_length))
            node.set("type", "priority")
        
        # West side (left)
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
        
        # Horizontal edges (west-east and east-west)
        for row in range(self.grid_size):
            for col in range(self.grid_size - 1):
                # West to East
                edge = ET.SubElement(root, "edge")
                edge.set("id", f"e{edge_id}")
                edge.set("from", f"n{row * self.grid_size + col}")
                edge.set("to", f"n{row * self.grid_size + col + 1}")
                edge.set("numLanes", str(self.num_lanes))
                edge.set("speed", "13.89")  # 50 km/h
                edge_id += 1
                
                # East to West
                edge = ET.SubElement(root, "edge")
                edge.set("id", f"e{edge_id}")
                edge.set("from", f"n{row * self.grid_size + col + 1}")
                edge.set("to", f"n{row * self.grid_size + col}")
                edge.set("numLanes", str(self.num_lanes))
                edge.set("speed", "13.89")
                edge_id += 1
        
        # Vertical edges (north-south and south-north)
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
            # Entry from north
            edge = ET.SubElement(root, "edge")
            edge.set("id", f"e{edge_id}")
            edge.set("from", f"n_north_{col}")
            edge.set("to", f"n{(self.grid_size - 1) * self.grid_size + col}")
            edge.set("numLanes", str(self.num_lanes))
            edge.set("speed", "13.89")
            edge_id += 1
            
            # Exit to north
            edge = ET.SubElement(root, "edge")
            edge.set("id", f"e{edge_id}")
            edge.set("from", f"n{(self.grid_size - 1) * self.grid_size + col}")
            edge.set("to", f"n_north_{col}")
            edge.set("numLanes", str(self.num_lanes))
            edge.set("speed", "13.89")
            edge_id += 1
        
        # Entry/Exit edges - South
        for col in range(self.grid_size):
            # Entry from south
            edge = ET.SubElement(root, "edge")
            edge.set("id", f"e{edge_id}")
            edge.set("from", f"n_south_{col}")
            edge.set("to", f"n{col}")
            edge.set("numLanes", str(self.num_lanes))
            edge.set("speed", "13.89")
            edge_id += 1
            
            # Exit to south
            edge = ET.SubElement(root, "edge")
            edge.set("id", f"e{edge_id}")
            edge.set("from", f"n{col}")
            edge.set("to", f"n_south_{col}")
            edge.set("numLanes", str(self.num_lanes))
            edge.set("speed", "13.89")
            edge_id += 1
        
        # Entry/Exit edges - East
        for row in range(self.grid_size):
            # Entry from east
            edge = ET.SubElement(root, "edge")
            edge.set("id", f"e{edge_id}")
            edge.set("from", f"n_east_{row}")
            edge.set("to", f"n{row * self.grid_size + (self.grid_size - 1)}")
            edge.set("numLanes", str(self.num_lanes))
            edge.set("speed", "13.89")
            edge_id += 1
            
            # Exit to east
            edge = ET.SubElement(root, "edge")
            edge.set("id", f"e{edge_id}")
            edge.set("from", f"n{row * self.grid_size + (self.grid_size - 1)}")
            edge.set("to", f"n_east_{row}")
            edge.set("numLanes", str(self.num_lanes))
            edge.set("speed", "13.89")
            edge_id += 1
        
        # Entry/Exit edges - West
        for row in range(self.grid_size):
            # Entry from west
            edge = ET.SubElement(root, "edge")
            edge.set("id", f"e{edge_id}")
            edge.set("from", f"n_west_{row}")
            edge.set("to", f"n{row * self.grid_size}")
            edge.set("numLanes", str(self.num_lanes))
            edge.set("speed", "13.89")
            edge_id += 1
            
            # Exit to west
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
        
        # Motorcycle - small, agile
        vtype = ET.SubElement(root, "vType")
        vtype.set("id", "motorcycle")
        vtype.set("vClass", "motorcycle")
        vtype.set("length", "2.0")
        vtype.set("width", "0.8")
        vtype.set("maxSpeed", "16.67")  # 60 km/h
        vtype.set("accel", "2.5")
        vtype.set("decel", "4.5")
        vtype.set("color", "yellow")
        
        # Car - medium size
        vtype = ET.SubElement(root, "vType")
        vtype.set("id", "car")
        vtype.set("vClass", "passenger")
        vtype.set("length", "4.5")
        vtype.set("width", "1.8")
        vtype.set("maxSpeed", "19.44")  # 70 km/h
        vtype.set("accel", "2.0")
        vtype.set("decel", "4.0")
        vtype.set("color", "blue")
        
        # Bus/Truck - large
        vtype = ET.SubElement(root, "vType")
        vtype.set("id", "bus_truck")
        vtype.set("vClass", "bus")
        vtype.set("length", "10.0")
        vtype.set("width", "2.5")
        vtype.set("maxSpeed", "13.89")  # 50 km/h
        vtype.set("accel", "1.0")
        vtype.set("decel", "3.0")
        vtype.set("color", "red")
        
        self._write_xml(root, vtypes_file)
        print(f"✓ Generated vehicle types file: {vtypes_file}")
        return vtypes_file
    
    def generate_routes(self):
        """Generate route flows with asymmetric patterns"""
        routes_file = os.path.join(self.output_dir, "routes.rou.xml")
        
        root = ET.Element("routes")
        
        # Include vehicle types
        include = ET.SubElement(root, "include")
        include.set("href", "vtypes.add.xml")
        
        flow_id = 0
        
        # West to East flows (HEAVY - main corridor)
        for row in range(self.grid_size):
            flow_id = self._add_flow_with_distribution(
                root, flow_id, 
                f"n_west_{row}", f"n_east_{row}",
                self.flow_patterns['west_to_east']
            )
        
        # East to West flows (MODERATE)
        for row in range(self.grid_size):
            flow_id = self._add_flow_with_distribution(
                root, flow_id, 
                f"n_east_{row}", f"n_west_{row}",
                self.flow_patterns['east_to_west']
            )
        
        # North to South flows (LIGHT)
        for col in range(self.grid_size):
            flow_id = self._add_flow_with_distribution(
                root, flow_id, 
                f"n_north_{col}", f"n_south_{col}",
                self.flow_patterns['north_to_south']
            )
        
        # South to North flows (LIGHT-MODERATE)
        for col in range(self.grid_size):
            flow_id = self._add_flow_with_distribution(
                root, flow_id, 
                f"n_south_{col}", f"n_north_{col}",
                self.flow_patterns['south_to_north']
            )
        
        self._write_xml(root, routes_file)
        print(f"✓ Generated routes file: {routes_file}")
        print(f"  - Total flows created: {flow_id}")
        print(f"  - Flow pattern (veh/hour):")
        print(f"    * West→East: {self.flow_patterns['west_to_east']} (Heavy)")
        print(f"    * East→West: {self.flow_patterns['east_to_west']} (Moderate)")
        print(f"    * North→South: {self.flow_patterns['north_to_south']} (Light)")
        print(f"    * South→North: {self.flow_patterns['south_to_north']} (Light-Moderate)")
        return routes_file
    
    def _add_flow_with_distribution(self, root, flow_id, from_node, to_node, veh_per_hour):
        """Add flows for each vehicle type according to Vietnamese distribution"""
        
        # Calculate vehicles per hour for each type
        motorcycle_vph = int(veh_per_hour * self.vehicle_distribution['motorcycle'])
        car_vph = int(veh_per_hour * self.vehicle_distribution['car'])
        bus_truck_vph = int(veh_per_hour * self.vehicle_distribution['bus_truck'])
        
        # Motorcycle flow
        if motorcycle_vph > 0:
            flow = ET.SubElement(root, "flow")
            flow.set("id", f"flow_{flow_id}")
            flow.set("type", "motorcycle")
            flow.set("fromJunction", from_node)
            flow.set("toJunction", to_node)
            flow.set("begin", "0")
            flow.set("end", "3600")
            flow.set("vehsPerHour", str(motorcycle_vph))
            flow.set("departLane", "best")
            flow.set("departSpeed", "max")
            flow_id += 1
        
        # Car flow
        if car_vph > 0:
            flow = ET.SubElement(root, "flow")
            flow.set("id", f"flow_{flow_id}")
            flow.set("type", "car")
            flow.set("fromJunction", from_node)
            flow.set("toJunction", to_node)
            flow.set("begin", "0")
            flow.set("end", "3600")
            flow.set("vehsPerHour", str(car_vph))
            flow.set("departLane", "best")
            flow.set("departSpeed", "max")
            flow_id += 1
        
        # Bus/Truck flow
        if bus_truck_vph > 0:
            flow = ET.SubElement(root, "flow")
            flow.set("id", f"flow_{flow_id}")
            flow.set("type", "bus_truck")
            flow.set("fromJunction", from_node)
            flow.set("toJunction", to_node)
            flow.set("begin", "0")
            flow.set("end", "3600")
            flow.set("vehsPerHour", str(bus_truck_vph))
            flow.set("departLane", "best")
            flow.set("departSpeed", "max")
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

        # Routing section - enable junction-based routing
        routing_section = ET.SubElement(root, "routing")
        junction_taz = ET.SubElement(routing_section, "junction-taz")
        junction_taz.set("value", "true")

        # Output section - tripinfo and statistics
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
            "--no-turnarounds", "false",
            "--junctions.join", "true",
            "--tls.guess", "true"
        ]
        
        print("\n⚙ Building network with netconvert...")
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"✓ Generated network file: {net_file}")
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
        print("\n" + "-" * 60)
        
        # Step 1: Generate nodes
        print("\n[1/6] Generating nodes...")
        nodes_file = self.generate_nodes()
        
        # Step 2: Generate edges
        print("\n[2/6] Generating edges...")
        edges_file = self.generate_edges()
        
        # Step 3: Build network
        print("\n[3/6] Building network...")
        net_file = self.build_network(nodes_file, edges_file)
        
        # Step 4: Generate vehicle types
        print("\n[4/6] Generating vehicle types...")
        vtypes_file = self.generate_vehicle_types()
        
        # Step 5: Generate routes
        print("\n[5/6] Generating routes with flows...")
        routes_file = self.generate_routes()
        
        # Step 6: Generate config
        print("\n[6/6] Generating SUMO configuration...")
        config_file = self.generate_sumo_config(net_file)
        
        print("\n" + "=" * 60)
        print("✓ Generation complete!")
        print("=" * 60)
        print(f"\nTo run the simulation:")
        print(f"  sumo-gui -c {config_file}")
        print(f"\nOr in command line mode:")
        print(f"  sumo -c {config_file}")
        print("\n" + "=" * 60)
        
        return config_file


def main():
    """Main function to generate the Vietnamese traffic scenario"""
    
    # You can customize these parameters
    generator = VietnameseTrafficGenerator(
        output_dir="vietnamese_traffic_3x3"
    )
    
    # Optionally adjust flow patterns for different scenarios
    # Example: Make west-east even heavier
    # generator.flow_patterns['west_to_east'] = 1500
    
    # Generate the scenario
    config_file = generator.generate()
    
    print("\n💡 Tips for AI traffic signal optimization:")
    print("  1. Use TraCI to control traffic lights in real-time")
    print("  2. Monitor queue lengths and waiting times")
    print("  3. The asymmetric flow provides clear optimization challenges")
    print("  4. West-East corridor has 2x traffic vs East-West")
    print("  5. North-South has lighter traffic than East-West")
    print("\nFor TraCI control, see SUMO documentation:")
    print("  https://sumo.dlr.de/docs/TraCI.html")
    

if __name__ == "__main__":
    main()
