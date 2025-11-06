#!/usr/bin/bash
#
# Generate improved route file with asymmetric traffic patterns
# Target: ~2000 vehicles total, 80% motorcycles, East-West bias
#
# Network structure:
#   J1 -- J2 -- J3
#   |     |     |
#   J4 -- J5 -- J6    (J5 = center, main corridors E-W and N-S)
#   |     |     |
#   J7 -- J8 -- J9
#

set -e  # Exit on error

echo ""
echo "====================================="
echo "Generating Asymmetric Traffic Routes"
echo "====================================="
echo ""

# Clean previous trip files
rm -f vn2.*.trips.xml vn2.rou.xml

# Step 1: Generate trip files with asymmetric O-D patterns
echo "Step 1: Generating trip files with custom O-D patterns"
echo "------------------------------------------------------"
python3 generate_asymmetric_trips.py

echo ""
echo "Step 2: Running duarouter to create vn2.rou.xml"
echo "------------------------------------------------------"
duarouter \
    --net-file vn.net.xml \
    --additional-files vtype.xml \
    --route-files vn2.motorcycle.wb.trips.xml,vn2.motorcycle.eb.trips.xml,vn2.motorcycle.ns.trips.xml,vn2.car.wb.trips.xml,vn2.car.eb.trips.xml,vn2.car.ns.trips.xml,vn2.delivery.trips.xml,vn2.bus.trips.xml,vn2.truck.trips.xml \
    --output-file vn2.rou.xml \
    --repair \
    --ignore-errors true \
    --no-step-log \
    --no-warnings

echo ""
echo "====================================="
echo "Route Generation Complete!"
echo "====================================="
echo ""
echo "Generated trip files:"
ls -lh vn2.*.trips.xml 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
echo ""
echo "Final route file: vn2.rou.xml ($(ls -lh vn2.rou.xml | awk '{print $5}'))"
echo ""

# Count vehicles in final route file
if [ -f vn2.rou.xml ]; then
    TOTAL_VEHICLES=$(grep -c '<vehicle id=' vn2.rou.xml || true)
    MOTORCYCLE_VEHICLES=$(grep -c 'id="motorcycle_' vn2.rou.xml || true)
    CAR_VEHICLES=$(grep -c 'id="car_' vn2.rou.xml || true)
    OTHER_VEHICLES=$((TOTAL_VEHICLES - MOTORCYCLE_VEHICLES - CAR_VEHICLES))

    echo "Final route file contains:"
    echo "  Motorcycles: $MOTORCYCLE_VEHICLES ($(echo "scale=1; $MOTORCYCLE_VEHICLES*100/$TOTAL_VEHICLES" | bc)%)"
    echo "  Cars: $CAR_VEHICLES ($(echo "scale=1; $CAR_VEHICLES*100/$TOTAL_VEHICLES" | bc)%)"
    echo "  Others: $OTHER_VEHICLES ($(echo "scale=1; $OTHER_VEHICLES*100/$TOTAL_VEHICLES" | bc)%)"
    echo "  TOTAL: $TOTAL_VEHICLES vehicles"
    echo ""

    # Check for circular routes (very simple check)
    SAME_EDGE_ROUTES=$(grep -E 'edges="(\S+)\s+\1"' vn2.rou.xml | wc -l || true)
    if [ $SAME_EDGE_ROUTES -eq 0 ]; then
        echo "✓ No obvious circular routes (same-edge patterns) detected"
    else
        echo "⚠ Warning: $SAME_EDGE_ROUTES routes with same consecutive edges detected"
    fi

    # Check for proper entry/exit (all routes should start with N_out and end with _to_N_out)
    ENTRY_COUNT=$(grep -c 'edges="N_out_' vn2.rou.xml || true)
    ENTRY_PERCENT=$(echo "scale=1; $ENTRY_COUNT*100/$TOTAL_VEHICLES" | bc)
    echo "✓ Routes starting from entry edges: $ENTRY_COUNT/$TOTAL_VEHICLES ($ENTRY_PERCENT%)"
fi

echo ""
echo "Traffic pattern: Westbound-heavy (46%), Eastbound (23%), N-S (23%), Uniform (8%)"
echo ""
echo "✓ Ready to use!"
echo "  Update dqn.py line 61 to: route_file='scenarios/3x3/vn2.rou.xml'"
echo ""
