from typing import Dict, Any, Optional
import re
from decimal import Decimal

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
            'Perform a battery load test and terminal cleaning ($20 - $40)',
            'Replace 12V battery if voltage is below 12.4V under load ($140 - $220)',
            'Inspect alternator charging output (should read 13.8V - 14.5V with engine running)'
        ],
        'cost_min': Decimal('120.00'),
        'cost_max': Decimal('260.00'),
        'diy_friendly': True,
        'summary': 'The rapid clicking sound is the starter solenoid engaging and immediately disengaging because the battery lacks sufficient cold cranking amps (CCA). Inspect terminals for white powdery corrosion and try jump-starting first.'
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
            'Front/Rear ceramic brake pad replacement ($150 - $250 per axle)',
            'Brake rotor resurfacing or replacement ($120 - $240 per pair)',
            'Caliper slide pin lubrication and brake fluid flush ($80 - $120)'
        ],
        'cost_min': Decimal('180.00'),
        'cost_max': Decimal('420.00'),
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
            'Cooling system pressure test to isolate the exact leak source ($60 - $90)',
            'Thermostat and housing replacement with fresh coolant flush ($180 - $320)',
            'Water pump replacement ($350 - $650)',
            'DO NOT continue driving; pull over immediately to prevent engine block warping'
        ],
        'cost_min': Decimal('160.00'),
        'cost_max': Decimal('750.00'),
        'diy_friendly': False,
        'summary': 'CRITICAL WARNING: Pull over and shut off the engine immediately. Modern aluminum cylinder heads will warp or crack within minutes of severe overheating, leading to multi-thousand-dollar engine rebuilds.'
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
            'OBD-II computer scan to pull specific DTC code (P0300 - P0308) ($0 at parts store / $60 pro)',
            'Replace ignition coil pack and set of iridium spark plugs ($180 - $380)',
            'Avoid heavy throttle driving to prevent unburned raw gasoline from melting the catalytic converter'
        ],
        'cost_min': Decimal('150.00'),
        'cost_max': Decimal('450.00'),
        'diy_friendly': True,
        'summary': 'A flashing Check Engine light indicates raw fuel is being dumped into the exhaust, which will rapidly destroy the catalytic converter ($1,200+ replacement). Immediate mechanic inspection is required.'
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
            'Four-wheel computer dynamic balancing ($50 - $90)',
            'Tire rotation and front-end alignment check ($80 - $140)',
            'Replace defective tire if radial runout exceeds spec ($120 - $220)'
        ],
        'cost_min': Decimal('60.00'),
        'cost_max': Decimal('180.00'),
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
            'Low R134a / R1234yf refrigerant due to pinhole leak in condenser or O-ring seals',
            'AC compressor electromagnetic clutch coil burned out',
            'Blown AC compressor fuse or relay',
            'Failed cabin blend door actuator directing heater air instead of cold air'
        ],
        'recommended_repairs': [
            'AC system vacuum test and refrigerant recharge with UV leak detection dye ($140 - $220)',
            'Replace leaking AC condenser or Schrader service valve ($250 - $550)',
            'Replace AC compressor assembly ($600 - $1,100)'
        ],
        'cost_min': Decimal('140.00'),
        'cost_max': Decimal('550.00'),
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
            'External brake fluid leak from rusted hard line or torn rubber flex hose',
            'Moisture-contaminated old brake fluid with degraded boiling point'
        ],
        'recommended_repairs': [
            'Four-wheel pressure brake bleed and fresh DOT 3/DOT 4 fluid flush ($110 - $170)',
            'Brake master cylinder replacement and bench bleed ($280 - $480)',
            'Inspect calipers, wheel cylinders, and lines for hydraulic wet spots'
        ],
        'cost_min': Decimal('120.00'),
        'cost_max': Decimal('480.00'),
        'diy_friendly': False,
        'summary': 'CRITICAL SAFETY HAZARD: A sinking pedal means hydraulic pressure is bleeding off. Loss of braking ability can occur without warning. Have the vehicle towed to a certified garage.'
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
