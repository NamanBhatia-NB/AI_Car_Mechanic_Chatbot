from typing import Dict, Any, Optional
import re
from decimal import Decimal

# Standard uniform price for all automotive diagnostic and standard repair packages
STANDARD_FLAT_PRICE = Decimal('2499.00')

# Catalog of classic automotive failure patterns
RULE_CATALOG = [
    {
        'id': 'battery_dead_clicking',
        'keywords': ['rapid click', 'clicking sound', 'clicks but wont start', 'won\'t turn over', 'no crank', 'dim lights', 'jump start'],
        'primary_issue': 'Depleted Battery / Corroded Terminals or Faulty Starter Solenoid',
        'severity': 'moderate',
        'confidence_score': 0.92,
        'symptoms': [
            'Rapid clicking sound when turning the ignition key',
            'Engine does not crank or cranks extremely slowly',
            'Interior dome and dashboard lights dim significantly during crank attempt'
        ],
        'possible_causes': [
            '12V lead-acid car battery depleted (parasitic draw or end of lifespan)',
            'Heavy corrosion or loose connections on battery terminals',
            'Faulty alternator failing to recharge the battery while driving',
            'Starter motor solenoid contacts pitted or failed'
        ],
        'recommended_repairs': [
            'Perform a battery load test and terminal cleaning (Covered under ₹2,499 flat rate)',
            'Replace 12V battery if voltage is below 12.4V under load (Battery replacement at MRP)',
            'Inspect alternator charging output (should read 13.8V - 14.5V with engine running)'
        ],
        'cost_min': STANDARD_FLAT_PRICE,
        'cost_max': STANDARD_FLAT_PRICE,
        'diy_friendly': True,
        'summary': 'The rapid clicking sound is the starter solenoid engaging and immediately disengaging because the battery lacks sufficient cold cranking amps (CCA). Inspect terminals for white powdery corrosion and try jump-starting first.'
    },
    {
        'id': 'carburetor_clogged_fuel',
        'keywords': [
            'carburetor', 'carbeaurator', 'carebeaurator', 'carb', 'choke', 'carburetor not working',
            'fix carburetor', 'fix carebeaurator', 'carb clogged', 'float valve', 'fuel bowl', 'fuel delivery'
        ],
        'primary_issue': 'Carburetor Jet Clogging, Stuck Float Valve, or Air-Fuel Imbalance',
        'severity': 'moderate',
        'confidence_score': 0.91,
        'symptoms': [
            'Engine sputters, bogs down on throttle, or stalls at idle',
            'Strong smell of unburned raw gasoline or black smoke from tailpipe',
            'Hard starting when cold, requiring prolonged choke engagement'
        ],
        'possible_causes': [
            'Varnish or ethanol gum buildup blocking pilot and main metering jets',
            'Stuck carburetor float or worn needle valve causing fuel overflow / flooding',
            'Vacuum leak around carburetor baseplate mounting gasket',
            'Misadjusted idle mixture screw or faulty electric choke'
        ],
        'recommended_repairs': [
            'Carburetor teardown, ultrasonic jet cleaning, and rebuild (Covered under ₹2,499 flat rate)',
            'Replace float needle valve and bowl gasket (Gasket kit at MRP)',
            'Inspect intake manifold vacuum lines and adjust idle mixture screws'
        ],
        'cost_min': STANDARD_FLAT_PRICE,
        'cost_max': STANDARD_FLAT_PRICE,
        'diy_friendly': True,
        'summary': 'Carburetors meter fuel via vacuum through tiny brass orifices. Stale fuel or sediment quickly plugs these orifices, causing lean misfires or rich flooding. Ultrasonic cleaning and jet re-tuning restores smooth idle and throttle response.'
    },
    {
        'id': 'brake_pads_squeal_grind',
        'keywords': ['brake squeal', 'brakes squeaking', 'grinding brakes', 'brake noise', 'grind when stop', 'squeal when braking', 'brake pad'],
        'primary_issue': 'Worn Brake Pads & Rotor Scoring',
        'severity': 'moderate',
        'confidence_score': 0.90,
        'symptoms': [
            'High-pitched metallic screech or squeal when applying foot brake',
            'Harsh metallic grinding sensation through the brake pedal on hard stops',
            'Increased stopping distance'
        ],
        'possible_causes': [
            'Brake friction material worn down to the acoustic metal wear indicator tab (< 3mm)',
            'Brake pad backing plate grinding metal-on-metal directly into the brake rotor',
            'Stuck brake caliper slide pin causing uneven, premature pad wear'
        ],
        'recommended_repairs': [
            'Front/Rear brake inspection and pad replacement service (Covered under ₹2,499 flat rate)',
            'Brake rotor resurfacing or replacement (Rotors at MRP)',
            'Caliper slide pin lubrication and brake fluid flush'
        ],
        'cost_min': STANDARD_FLAT_PRICE,
        'cost_max': STANDARD_FLAT_PRICE,
        'diy_friendly': False,
        'summary': 'The acoustic wear tab is designed to screech to alert you before damaging the brake rotors. If metal grinding is already audible, the rotors will likely need replacement alongside the pads.'
    },
    {
        'id': 'engine_overheating_steam',
        'keywords': ['overheating', 'overheat', 'temp gauge in red', 'steam under hood', 'coolant leak', 'sweet smell', 'radiator boiling', 'antifreeze leaking'],
        'primary_issue': 'Cooling System Failure (Coolant Leak, Thermostat, or Water Pump)',
        'severity': 'critical',
        'confidence_score': 0.94,
        'symptoms': [
            'Engine temperature gauge pinned in the red / High Temp warning light on dash',
            'Visible steam or sweet-smelling white vapor billowing from under the hood',
            'Puddle of bright green, orange, or pink coolant beneath the vehicle'
        ],
        'possible_causes': [
            'Ruptured upper/lower radiator hose or cracked radiator plastic end-tank',
            'Thermostat stuck in the closed position, blocking coolant flow to the radiator',
            'Water pump bearing failure or impeller corrosion',
            'Blown cylinder head gasket allowing exhaust gases to over-pressurize cooling jacket'
        ],
        'recommended_repairs': [
            'Complete cooling system pressure test and diagnostic inspection (Covered under ₹2,499 flat rate)',
            'Thermostat and housing replacement with fresh coolant flush',
            'Inspect water pump and radiator integrity',
            'DO NOT continue driving; pull over immediately to prevent engine block warping'
        ],
        'cost_min': STANDARD_FLAT_PRICE,
        'cost_max': STANDARD_FLAT_PRICE,
        'diy_friendly': False,
        'summary': 'CRITICAL WARNING: Pull over and shut off the engine immediately. Modern aluminum cylinder heads will warp or crack within minutes of severe overheating, leading to expensive engine rebuilds.'
    },
    {
        'id': 'check_engine_flashing_misfire',
        'keywords': ['check engine flashing', 'engine light blinking', 'shuddering', 'engine shaking rough', 'loss of power', 'sputtering', 'p0300', 'p0301', 'p0302', 'p0303', 'p0304'],
        'primary_issue': 'Active Cylinder Misfire (Ignition Coil / Spark Plug Failure)',
        'severity': 'critical',
        'confidence_score': 0.91,
        'symptoms': [
            'Check Engine Light is actively FLASHING / BLINKING (not steady)',
            'Severe engine vibration, hesitating heavily under load or acceleration',
            'Unburned fuel smell from tailpipe'
        ],
        'possible_causes': [
            'Failed ignition coil on one or more cylinders',
            'Fouled, worn, or bridged spark plug gap',
            'Clogged or stuck-open electronic fuel injector',
            'Low cylinder compression due to sticking valve'
        ],
        'recommended_repairs': [
            'OBD-II computer diagnostics & live cylinder misfire scan (Covered under ₹2,499 flat rate)',
            'Replace ignition coil pack and set of spark plugs (Parts at MRP)',
            'Avoid heavy throttle driving to prevent unburned raw gasoline from damaging catalytic converter'
        ],
        'cost_min': STANDARD_FLAT_PRICE,
        'cost_max': STANDARD_FLAT_PRICE,
        'diy_friendly': True,
        'summary': 'A flashing Check Engine light indicates raw fuel is being dumped into the exhaust, which will rapidly destroy the catalytic converter. Immediate mechanic inspection is required.'
    },
    {
        'id': 'wheel_vibration_highway',
        'keywords': ['steering wheel shakes', 'shaking at 60', 'vibration at highway', 'wobble at 50', 'shaking at high speed', 'steering wobble'],
        'primary_issue': 'Front Wheel Imbalance or Tire Tread Separation',
        'severity': 'low',
        'confidence_score': 0.88,
        'symptoms': [
            'Steering wheel vibrates noticeably between 50 - 75 mph (80 - 120 km/h)',
            'Vibration disappears or reduces when driving at city speeds (< 35 mph)',
            'Tire tread cupping or uneven scalloping on inner shoulders'
        ],
        'possible_causes': [
            'Lost wheel balance weight from front rim',
            'Tire flat-spotted or internal steel belt slipped/separated',
            'Slightly bent wheel rim from pothole impact',
            'Worn tie rod end or lower ball joint'
        ],
        'recommended_repairs': [
            'Front suspension, steering linkage, and hub inspection (Covered under ₹2,499 flat rate)',
            'Four-wheel dynamic balancing and tire rotation',
            'Replace defective tire if radial runout exceeds manufacturer spec'
        ],
        'cost_min': STANDARD_FLAT_PRICE,
        'cost_max': STANDARD_FLAT_PRICE,
        'diy_friendly': False,
        'summary': 'A rhythmic vibration isolated to the steering wheel at highway speeds is the signature sign of front wheel imbalance. Have a tire shop balance all four wheels on a road-force balancer.'
    },
    {
        'id': 'ac_blowing_warm',
        'keywords': ['ac blowing warm', 'no cold air', 'ac not working', 'air conditioner warm', 'ac blowing hot', 'freon leak', 'hissing ac'],
        'primary_issue': 'Air Conditioning Refrigerant Leak or Compressor Clutch Inoperative',
        'severity': 'low',
        'confidence_score': 0.89,
        'symptoms': [
            'Cabin vents blow ambient or warm air despite AC button engaged and set to lowest temp',
            'AC compressor clutch does not click on or spin when AC is toggled',
            'Faint hissing noise audible from vents on startup'
        ],
        'possible_causes': [
            'Low refrigerant due to pinhole leak in condenser or O-ring seals',
            'AC compressor electromagnetic clutch coil burned out',
            'Blown AC compressor fuse or relay',
            'Failed cabin blend door actuator directing heater air instead of cold air'
        ],
        'recommended_repairs': [
            'Complete AC system leak test, pressure check, and diagnostics (Covered under ₹2,499 flat rate)',
            'Replace leaking AC condenser or service valve O-rings',
            'Recharge refrigerant with UV leak detection dye'
        ],
        'cost_min': STANDARD_FLAT_PRICE,
        'cost_max': STANDARD_FLAT_PRICE,
        'diy_friendly': False,
        'summary': 'Modern automotive AC systems have low-pressure safety switches that shut down the compressor when refrigerant levels drop. A leak check with UV dye is the proper diagnostic first step.'
    },
    {
        'id': 'spongy_brake_pedal',
        'keywords': ['spongy brake', 'brake pedal sinks to floor', 'soft brake pedal', 'no brake pressure', 'pedal goes down'],
        'primary_issue': 'Hydraulic Brake System Air Ingress or Master Cylinder Internal Bypass',
        'severity': 'critical',
        'confidence_score': 0.93,
        'symptoms': [
            'Brake pedal feels mushy or soft and travels unusually close to the floorboard',
            'Pedal slowly sinks toward the floor when held at a red traffic light',
            'Pumping the pedal several times temporarily restores firmness'
        ],
        'possible_causes': [
            'Air bubbles trapped inside hydraulic brake lines',
            'Brake master cylinder internal piston seals bypassing fluid',
            'External brake fluid leak from hard line or torn rubber flex hose',
            'Moisture-contaminated old brake fluid with degraded boiling point'
        ],
        'recommended_repairs': [
            'Complete hydraulic brake system bleed and leak inspection (Covered under ₹2,499 flat rate)',
            'Brake master cylinder replacement and pressure bleed',
            'Inspect calipers, wheel cylinders, and lines for hydraulic wet spots'
        ],
        'cost_min': STANDARD_FLAT_PRICE,
        'cost_max': STANDARD_FLAT_PRICE,
        'diy_friendly': False,
        'summary': 'CRITICAL SAFETY HAZARD: A sinking pedal means hydraulic pressure is bleeding off. Loss of braking ability can occur without warning. Have the vehicle inspected by a certified garage.'
    }
]


class RuleDiagnosisEngine:
    """Tier 2: Classic automotive knowledge base engine that resolves standard issues with $0.00 AI cost."""

    @classmethod
    def match_rule(cls, text: str) -> Optional[Dict[str, Any]]:
        """Scans user conversation text for established mechanical failure patterns."""
        clean = text.lower()
        best_match = None
        highest_hits = 0

        for rule in RULE_CATALOG:
            hits = 0
            for kw in rule['keywords']:
                if kw in clean:
                    hits += 1
            if hits > highest_hits:
                highest_hits = hits
                best_match = rule

        if highest_hits >= 1 and best_match:
            return best_match
        return None
