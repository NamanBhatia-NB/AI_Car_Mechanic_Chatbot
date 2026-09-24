import re
from typing import Tuple, Optional, List

# Core automotive keywords and terminology
AUTOMOTIVE_KEYWORDS = {
    # Vehicle parts & systems
    'car', 'cars', 'truck', 'trucks', 'suv', 'suvs', 'vehicle', 'vehicles', 'auto', 'automobile',
    'engine', 'motor', 'transmission', 'gearbox', 'brakes', 'brake', 'rotor', 'rotors', 'pad', 'pads',
    'caliper', 'calipers', 'clutch', 'exhaust', 'muffler', 'catalytic', 'converter',
    'battery', 'alternator', 'starter', 'radiator', 'coolant', 'antifreeze', 'oil', 'filter',
    'spark', 'plug', 'plugs', 'cylinder', 'cylinders', 'piston', 'pistons', 'suspension',
    'strut', 'struts', 'shock', 'shocks', 'absorber', 'absorbers', 'tire', 'tires', 'wheel', 'wheels',
    'alignment', 'steering', 'power steering', 'rack and pinion', 'tie rod', 'ball joint',
    'dashboard', 'check engine', 'odometer', 'speedometer', 'fuel', 'gas', 'gasoline', 'diesel',
    'hybrid', 'ev', 'electric vehicle', 'fuse', 'fuses', 'headlight', 'taillight', 'windshield',
    'wiper', 'wipers', 'fluid', 'fluids', 'air conditioning', 'ac', 'heater', 'thermostat',
    'belt', 'belts', 'timing belt', 'serpentine', 'hose', 'hoses', 'gasket', 'head gasket',
    'manifold', 'turbo', 'supercharger', 'differential', 'axle', 'cv joint', 'tailpipe',
    
    # Common vehicle makes & models
    'toyota', 'honda', 'ford', 'chevrolet', 'chevy', 'nissan', 'bmw', 'mercedes', 'benz',
    'audi', 'volkswagen', 'vw', 'hyundai', 'kia', 'subaru', 'mazda', 'lexus', 'dodge',
    'jeep', 'ram', 'chrysler', 'tesla', 'volvo', 'porsche', 'land rover', 'acura', 'infiniti',
    'buick', 'cadillac', 'gmc', 'mitsubishi', 'mini', 'jaguar', 'fiat', 'genesis', 'lincoln',
    'maruti', 'suzuki', 'tata', 'mahindra', 'skoda', 'renault', 'peugeot',
    'civic', 'corolla', 'accord', 'camry', 'f150', 'f-150', 'mustang', 'silverado', 'elantra',
    'sonata', 'altima', 'sentra', 'rav4', 'crv', 'cr-v', 'prius', 'miata', 'wrangler',
    
    # Automotive symptoms & sounds
    'squeak', 'squeaking', 'squeal', 'squealing', 'grind', 'grinding', 'rattle', 'rattling',
    'knock', 'knocking', 'clunk', 'clunking', 'click', 'clicking', 'hiss', 'hissing', 'hum', 'humming',
    'shake', 'shaking', 'vibrate', 'vibration', 'wobble', 'wobbling', 'pull', 'pulling',
    'leak', 'leaking', 'leaks', 'smoke', 'smoking', 'steam', 'steaming', 'overheat', 'overheating',
    'stall', 'stalling', 'stalls', 'hesitate', 'hesitation', 'misfire', 'misfires', 'misfiring',
    'crank', 'cranking', 'no start', 'wont start', "won't start", 'dead', 'drained',
    'smell', 'odor', 'burning', 'spongy', 'stiff', 'jerking', 'slipping', 'rough idle', 'surge',
    'mileage', 'rpm', 'obd', 'obd2', 'obd-ii', 'code', 'dtc', 'p0', 'p1', 'p2',
    
    # Automotive service, maintenance & parts
    'service', 'maintenance', 'tune up', 'mechanic', 'repair', 'repairs', 'inspection',
    'warranty', 'recall', 'drive', 'driving', 'accelerat', 'accelerate', 'accelerating',
    'braking', 'turning', 'reverse', 'diagnos', 'diagnosis', 'diagnose', 'diagnostic',
    'fix', 'fixed', 'problem', 'issue', 'cost', 'estimate', 'quote', 'report',
    'book', 'booking', 'appointment', 'schedule', 'replace', 'inspect', 'technician',
    'garage', 'workshop', 'towing', 'tow', 'mile', 'miles', 'km', 'kms'
}

# Recognized valid slot-filling short answers (when technician asks condition or frequency)
VALID_SLOT_ANSWERS = {
    'cold start', 'morning', 'cold', 'hot', 'warm', 'braking', 'accelerating', 'acceleration',
    'highway', 'highway speeds', 'speed', 'idle', 'idling', 'turning', 'bumps', 'rough road',
    'constant', 'constantly', 'continuous', 'continuously', 'intermittent', 'sometimes',
    'always', 'yes', 'no', 'yeah', 'nope', 'flashing', 'solid', 'blinking', 'steady',
    'red', 'yellow', 'amber', 'under the hood', 'left', 'right', 'front', 'rear', 'back'
}

# Explicit off-topic regex patterns
OFF_TOPIC_PATTERNS = [
    r'\b(cake|recipe|cook|bake|cooking|baking|dinner|food|pizza|burger|pasta|ingredient|ingredients)\b',
    r'\b(diameter|circumference|distance to|planet|earth|mars|moon|sun|solar system|galaxy|universe)\b',
    r'\b(essay|poem|song|story|python code|javascript|programming|java|c\+\+|html|cover letter|homework)\b',
    r'\b(write|generate|compose|code)\s+(me\s+)?(an?\s+)?(essay|poem|song|story|code|script|article)\b',
    r'\b(capital of|president of|prime minister|who won|election|political|politics|government)\b',
    r'\b(solve this|calculus|integral|algebra|math equation|derive|proof)\b',
    r'\b(crypto|bitcoin|ethereum|stock trading|forex|investing|finance)\b',
    r'\b(meaning of life|philosophy of|tell me a joke|tell me a riddle)\b',
    r'\b(weather|forecast for|sports score|nba|nfl|fifa|cricket|football match)\b',
    r'\b(who is|what is the history of|tell me about)\s+(?!my car|the car|the vehicle|this engine|the brake|the transmission)\b',
]

GREETING_PATTERNS = [
    r'^(hi|hello|hey|greetings|good\s+(morning|afternoon|evening)|howdy|sup)(\s+(there|friend|marcus|mechanic|everyone))?[\s!.,?]*$'
]

FAREWELL_PATTERNS = [
    r'^(bye|goodbye|see\s+you|cya|thanks|thank\s+you|cheers)[\s!.,?]*$'
]


class GuardrailService:
    """Tier 0: Deterministic guardrail to reject non-automotive queries without LLM cost."""

    @classmethod
    def check_query(
        cls,
        text: str,
        has_media: bool = False,
        is_active_session: bool = False
    ) -> Tuple[bool, Optional[str], List[str], str]:
        """
        Strict automotive domain evaluation.
        Returns:
            (is_off_topic: bool, canned_reply: Optional[str], quick_replies: List[str], intent_type: str)
        """
        clean_text = text.strip().lower()
        if not clean_text and not has_media:
            return (
                False,
                "Hey there, I'm Marcus, Senior Automotive Technician. Tell me what issue your vehicle is having or upload a photo/audio clip of the symptom.",
                ["Engine won't start", "Squeaking brakes", "Check Engine Light on", "Engine overheating"],
                "empty"
            )

        # 1. Check for standard greetings
        for pattern in GREETING_PATTERNS:
            if re.match(pattern, clean_text):
                return (
                    False,
                    "Hello! I'm Marcus, your virtual Master Technician with 20+ years of garage experience. "
                    "What vehicle are you driving today (Year/Make/Model), and what mechanical symptom or sound are you noticing?",
                    ["My car won't start", "Brakes grinding/squeaking", "Check Engine light flashing", "Engine overheating"],
                    "greeting"
                )

        # 2. Check for farewell / thanks
        for pattern in FAREWELL_PATTERNS:
            if re.match(pattern, clean_text):
                return (
                    False,
                    "You're very welcome! Keep an eye on those gauges and stay safe on the road. "
                    "If any other lights or strange sounds pop up, feel free to reach out anytime.",
                    ["Book a mechanic", "Start a new diagnosis"],
                    "farewell"
                )

        # 3. If media is uploaded, allow it directly into automotive analysis
        if has_media:
            return (False, None, [], "automotive")

        # 4. Check explicit off-topic patterns FIRST (regardless of active session!)
        for pattern in OFF_TOPIC_PATTERNS:
            if re.search(pattern, clean_text):
                return (
                    True,
                    "I am Marcus, a dedicated automotive diagnostic technician. I can only assist with vehicle "
                    "troubleshooting, mechanical repairs, diagnostic trouble codes, and booking service appointments. "
                    "Please let me know if you need help with your car, truck, or SUV!",
                    ["Check my engine sound", "Diagnose brake noise", "Book a mechanic"],
                    "off_topic"
                )

        # 5. Extract words and check for automotive keywords
        words = set(re.findall(r'[a-z0-9\']+', clean_text))
        has_automotive_match = False

        if words.intersection(AUTOMOTIVE_KEYWORDS):
            has_automotive_match = True

        # Check vehicle year pattern (e.g. 1980-2027)
        if not has_automotive_match and re.search(r'\b(19[8-9]\d|20[0-2]\d)\b', clean_text):
            has_automotive_match = True

        # Check OBD-II codes (e.g. P0300, P0420, P0171)
        if not has_automotive_match and re.search(r'\b[pbcu][0-3][0-9a-f]{3}\b', clean_text):
            has_automotive_match = True

        # Check phrases
        if not has_automotive_match:
            for phrase in ['wont start', "won't start", 'check engine', 'power steering', 'ac warm', 'bad mileage', 'no start']:
                if phrase in clean_text:
                    has_automotive_match = True
                    break

        # 6. If in active session, check if query matches a valid slot answer (e.g. "braking", "morning", "yes", "no")
        if not has_automotive_match and is_active_session:
            # Check if any recognized slot-filling answer is in the user text
            if clean_text in VALID_SLOT_ANSWERS or any(ans in clean_text for ans in VALID_SLOT_ANSWERS):
                has_automotive_match = True

        # 7. If STILL no automotive match, reject as off-topic!
        if not has_automotive_match:
            return (
                True,
                "As a senior automobile technician, I specialize exclusively in car diagnostics, maintenance, "
                "and mechanical repairs. I didn't detect any automotive symptoms or vehicle details in your message. "
                "Could you describe what's going on under the hood, with your brakes, tires, or dashboard?",
                ["Car won't start", "Squeaking brakes", "Engine overheating", "Check Engine Light on"],
                "off_topic"
            )

        return (False, None, [], "automotive")
