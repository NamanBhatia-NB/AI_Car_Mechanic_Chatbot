from typing import Dict, Any, Optional
import re
from decimal import Decimal

# Catalog of classic automotive failure patterns with realistic market pricing (INR)
RULE_CATALOG = [
    {
        'id': 'battery_dead_clicking',
        'keywords': [
            'not starting', 'car not starting', 'car won\'t start', 'car wont start',
            'won\'t start', 'wont start', 'doesn\'t start', 'does not start',
            'engine won\'t start', 'engine wont start', 'engine not starting',
            'my car is not starting', 'vehicle not starting', 'car dead', 'dead car',
            'no start', 'will not start', 'rapid click', 'clicking sound',
            'clicks but wont start', 'won\'t turn over', 'wont turn over',
            'no crank', 'wont crank', 'won\'t crank', 'dim lights', 'jump start',
            'battery dead', 'dead battery', 'battery is dead'
        ],
        'primary_issue': 'Starting System Failure (Depleted Battery / Corroded Terminals / Faulty Starter)',
        'severity': 'moderate',
        'confidence_score': 0.93,
        'symptoms': [
            'Engine will not crank or start when turning ignition key or pressing start button',
            'Rapid clicking sound, groaning sound, or complete silence from starter solenoid',
            'Interior dome and dashboard lights dim significantly during crank attempt'
        ],
        'possible_causes': [
            '12V lead-acid car battery depleted (parasitic draw or end of lifespan)',
            'Heavy corrosion or loose connections on battery terminals',
            'Faulty starter motor solenoid contacts pitted or failed',
            'Faulty alternator failing to recharge the battery while driving'
        ],
        'recommended_repairs': [
            'Battery terminal servicing and high-rate load test (₹499 - ₹799)',
            'On-site jump start and alternator charging rate check (₹699 - ₹999)',
            'New 12V automotive battery replacement if sulfated (₹3,500 - ₹5,800 depending on Ah rating)'
        ],
        'cost_min': Decimal('799.00'),
        'cost_max': Decimal('2199.00'),
        'diy_friendly': True,
        'summary': 'When a vehicle fails to start or crank, the starter solenoid cannot engage or hold due to low battery voltage or pitted contacts. Inspect terminals for white powdery corrosion and test with a jump start first.'
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
            'Carburetor teardown, ultrasonic jet cleaning, and needle seat service (₹1,299 - ₹1,899)',
            'Replace float needle valve and bowl gasket kit (₹450 - ₹950)',
            'Intake manifold vacuum leak check and idle air-fuel ratio re-tuning'
        ],
        'cost_min': Decimal('1299.00'),
        'cost_max': Decimal('2899.00'),
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
            'Front ceramic brake pad replacement and caliper slide pin lubrication (₹1,699 - ₹2,499)',
            'Brake rotor resurfacing or disc replacement if scored below minimum thickness (₹1,800 - ₹3,200)',
            'DOT-4 brake fluid level and moisture inspection'
        ],
        'cost_min': Decimal('1699.00'),
        'cost_max': Decimal('4499.00'),
        'diy_friendly': False,
        'summary': 'The acoustic wear tab is designed to screech to alert you before damaging the brake rotors. If metal grinding is already audible, the rotors will likely need replacement alongside the pads.'
    },
    {
        'id': 'engine_overheating_steam',
        'keywords': [
            'engine temperature gauge in red', 'temperature gauge in red', 'temp gauge in red',
            'gauge in red', 'overheating', 'overheat', 'steam under hood', 'coolant leak',
            'sweet smell', 'radiator boiling', 'antifreeze leaking', 'radiator leaking'
        ],
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
            'Cooling system pressure test, leak detection, and fresh coolant flush (₹1,499 - ₹2,499)',
            'Thermostat replacement and housing gasket renewal (₹1,800 - ₹3,200)',
            'Water pump and radiator core inspection / replacement (₹4,500 - ₹8,999)',
            'DO NOT continue driving; pull over immediately to prevent cylinder head warpage'
        ],
        'cost_min': Decimal('3499.00'),
        'cost_max': Decimal('8999.00'),
        'diy_friendly': False,
        'summary': 'CRITICAL WARNING: Pull over and shut off the engine immediately. Modern aluminum cylinder heads will warp or crack within minutes of severe overheating, leading to expensive engine rebuilds.'
    },
    {
        'id': 'check_engine_flashing_misfire',
        'keywords': [
            'check engine light is blinking', 'check engine flashing', 'engine light blinking',
            'check engine light', 'engine light is blinking', 'blinking engine light',
            'flashing check engine', 'check engine light on', 'engine light on',
            'misfire', 'cylinder misfire', 'shuddering', 'engine shaking rough',
            'loss of power', 'sputtering', 'p0300', 'p0301', 'p0302', 'p0303', 'p0304'
        ],
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
            'OBD-II live cylinder misfire diagnostic scan and live data logging (₹899 - ₹1,499)',
            'Replace defective ignition coil pack and platinum spark plugs (₹2,299 - ₹4,800)',
            'Fuel injector spray pattern and cylinder compression verification',
            'Avoid driving under load to protect catalytic converter from raw unburned fuel damage'
        ],
        'cost_min': Decimal('2299.00'),
        'cost_max': Decimal('5499.00'),
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
            'Four-wheel dynamic spin balancing and tire rotation (₹699 - ₹1,200)',
            'Inspect front tie rods, control arm bushings, and wheel bearings for axial play (₹999 - ₹1,899)',
            'Check tire tread for internal steel belt separation or rim runout'
        ],
        'cost_min': Decimal('699.00'),
        'cost_max': Decimal('1899.00'),
        'diy_friendly': False,
        'summary': 'A rhythmic vibration isolated to the steering wheel at highway speeds is the signature sign of front wheel imbalance. Have a tire shop balance all four wheels on a road-force balancer.'
    },
    {
        'id': 'ac_blowing_warm',
        'keywords': [
            'car ac is not cooling', 'ac is not cooling', 'ac not cooling', 'car ac not cooling',
            'ac blowing warm', 'no cold air', 'ac not working', 'car ac not working', 'air conditioner warm',
            'ac blowing hot', 'ac not cold', 'no cooling', 'cooling not working', 'freon leak',
            'hissing ac', 'air conditioning not cooling', 'car ac problem', 'ac issue'
        ],
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
            'AC system pressure test, UV dye leak check, and R134a/R1234yf recharge (₹1,799 - ₹2,799)',
            'AC condenser or service port Schrader valve seal replacement (₹1,500 - ₹3,200)',
            'Compressor magnetic clutch relay and blend door actuator inspection'
        ],
        'cost_min': Decimal('1799.00'),
        'cost_max': Decimal('4699.00'),
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
            'Four-corner pressurized hydraulic brake line bleeding and fluid flush (₹1,499 - ₹2,199)',
            'Brake master cylinder overhaul or replacement (₹2,800 - ₹4,999)',
            'Inspect calipers, wheel cylinders, and lines for hydraulic wet spots'
        ],
        'cost_min': Decimal('1999.00'),
        'cost_max': Decimal('4999.00'),
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
