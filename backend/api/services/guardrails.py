import re
from typing import Tuple, Optional, List

# Core automotive keywords and terminology
AUTOMOTIVE_KEYWORDS = {
    # Vehicle parts & systems
    'car', 'truck', 'suv', 'vehicle', 'auto', 'engine', 'motor', 'transmission', 'gearbox',
    'brakes', 'brake', 'rotor', 'pad', 'caliper', 'clutch', 'exhaust', 'muffler', 'catalytic',
    'battery', 'alternator', 'starter', 'radiator', 'coolant', 'antifreeze', 'oil', 'filter',
    'spark', 'plug', 'cylinder', 'piston', 'suspension', 'strut', 'shock', 'absorber',
    'tire', 'tires', 'wheel', 'wheels', 'alignment', 'steering', 'power steering',
    'dashboard', 'check engine', 'odometer', 'speedometer', 'fuel', 'gas', 'diesel', 'hybrid',
    'ev', 'electric vehicle', 'fuse', 'headlight', 'taillight', 'windshield', 'wiper', 'fluid',
    'air conditioning', 'ac', 'heater', 'thermostat', 'belt', 'timing belt', 'serpentine',
    'hose', 'gasket', 'manifold', 'turbo', 'supercharger', 'differential', 'axle', 'cv joint',
    
    # Common vehicle makes
    'toyota', 'honda', 'ford', 'chevrolet', 'chevy', 'nissan', 'bmw', 'mercedes', 'benz',
    'audi', 'volkswagen', 'vw', 'hyundai', 'kia', 'subaru', 'mazda', 'lexus', 'dodge',
    'jeep', 'ram', 'chrysler', 'tesla', 'volvo', 'porsche', 'land rover', 'acura', 'infiniti',
    'buick', 'cadillac', 'gmc', 'mitsubishi', 'mini', 'jaguar', 'fiat', 'genesis', 'lincoln',
    'maruti', 'suzuki', 'tata', 'mahindra', 'skoda', 'renault', 'peugeot',
    
    # Automotive symptoms, actions & service flow
    'squeak', 'squeal', 'grind', 'rattle', 'knock', 'clunk', 'click', 'hiss', 'hum',
    'shake', 'vibrate', 'shaking', 'wobble', 'pulling', 'leak', 'leaking', 'smoke', 'steam',
    'overheat', 'overheating', 'stall', 'stalling', 'hesitate', 'misfire', 'crank', 'cranking',
    'no start', 'won\'t start', 'dead', 'drained', 'smell', 'odor', 'burning', 'spongy',
    'stiff', 'jerking', 'slipping', 'rough idle', 'surge', 'mileage', 'rpm', 'obd', 'code',
    'dtc', 'p0', 'p1', 'service', 'maintenance', 'tune up', 'mechanic', 'repair', 'inspection',
    'warranty', 'recall', 'drive', 'driving', 'accelerat', 'braking', 'turning', 'reverse',
    'diagnos', 'diagnosis', 'diagnose', 'diagnostic', 'problem', 'issue', 'fix', 'fixed',
    'cost', 'estimate', 'quote', 'report', 'book', 'booking', 'appointment', 'schedule',
    'replace', 'inspect', 'technician'
}

# Explicit off-topic categories to reject instantly
OFF_TOPIC_PATTERNS = [
    r'\b(essay|poem|song|story|python code|javascript|programming|cover letter)\b',
    r'\b(write|generate|compose)\s+(me\s+)?(an?\s+)?(essay|poem|song|story|code|script|article)\b',
    r'\b(capital of|president of|prime minister|who won|election|political|politics)\b',
    r'\b(recipe for|how to cook|bake|ingredients for|dinner tonight)\b',
    r'\b(solve this math|calculus|integral|algebra|equation)\b',
    r'\b(crypto|bitcoin|ethereum|stock trading|forex)\b',
    r'\b(meaning of life|philosophy of|tell me a joke)\b',
    r'\b(what is the weather|forecast for|sports score|nba|nfl|fifa)\b',
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
        Evaluates user input.
        Returns:
            (is_off_topic, canned_reply, quick_replies, intent_type)
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

        # 4. Check explicit off-topic patterns
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

        # If the user is already in an active session answering questions (e.g. "it happens in the morning", "yes", "no")
        if is_active_session:
            return (False, None, [], "automotive")

        # 5. Check if query contains any automotive keywords or symptoms
        words = set(re.findall(r'[a-z0-9\']+', clean_text))
        has_automotive_match = False
        
        # Check single keywords
        if words.intersection(AUTOMOTIVE_KEYWORDS):
            has_automotive_match = True
            
        # Check common phrases
        if not has_automotive_match:
            for kw in ['wont start', "won't start", 'check engine', 'power steering', 'ac warm', 'bad mileage', 'diagnose', 'give me diagnosis']:
                if kw in clean_text:
                    has_automotive_match = True
                    break

        # Check vehicle year pattern (e.g. 1990-2027)
        if not has_automotive_match and re.search(r'\b(19\d{2}|20[0-2]\d)\b', clean_text):
            has_automotive_match = True

        # Check OBD-II codes (e.g. P0300, P0420, P0171)
        if not has_automotive_match and re.search(r'\b[pbcu][0-3][0-9a-f]{3}\b', clean_text):
            has_automotive_match = True

        # If too short and no automotive matches, polite guidance
        if not has_automotive_match and len(clean_text) > 12:
            return (
                True,
                "As a senior automobile technician, I specialize exclusively in car diagnostics, maintenance, "
                "and mechanical repairs. I didn't detect any automotive symptoms or vehicle details in your message. "
                "Could you describe what's going on under the hood, with your brakes, tires, or dashboard?",
                ["Car is making a grinding noise", "Check engine light came on", "Battery is dead", "Fluid leaking under car"],
                "off_topic"
            )

        return (False, None, [], "automotive")
