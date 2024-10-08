import re



def set_kilogram(kg):
    """Retorna el valor en kilogramos (sin conversión necesaria)."""
    return kg

def grams_to_kilogram(g):
    """Convierte gramos a kilogramos."""
    return g / 1000

def milligrams_to_kilogram(mg):
    """Convierte miligramos a kilogramos."""
    return mg / 1_000_000

def pound_to_kilogram(lb):
    """Convierte libras a kilogramos."""
    return lb * 0.453592

def ounce_to_kilogram(oz):
    """Convierte onzas a kilogramos."""
    return oz * 0.0283495

def convert_weight(value, unit):
    """Convierte el valor dado a kilogramos basado en la unidad especificada."""
    weight_data = {
        "kilogramos": set_kilogram,
        "kilogramo": set_kilogram,
        "kilograms": set_kilogram,
        "kilos": set_kilogram,
        "kilo": set_kilogram,
        "kgs": set_kilogram,
        "kg": set_kilogram,
        "gramos": grams_to_kilogram,
        "gramo": grams_to_kilogram,
        "grams": grams_to_kilogram,
        "grms": grams_to_kilogram,
        "gm": grams_to_kilogram,
        "gms": grams_to_kilogram,
        "g": grams_to_kilogram,
        "miligramos": milligrams_to_kilogram,
        "miligramo": milligrams_to_kilogram,
        "mg": milligrams_to_kilogram,
        "mgs": milligrams_to_kilogram,
        "libras": pound_to_kilogram,
        "libra": pound_to_kilogram,
        "lbs": pound_to_kilogram,
        "lb": pound_to_kilogram,
        "pounds": pound_to_kilogram,
        "pound": pound_to_kilogram,
        "onzas": ounce_to_kilogram,
        "onza": ounce_to_kilogram,
        "oz": ounce_to_kilogram,
        "ounces": ounce_to_kilogram,
        "ounce": ounce_to_kilogram
    }

    if unit in weight_data:
        return weight_data[unit](value)
    else:
        raise ValueError(f"Unidad no reconocida: {unit}")

def parse_weight(weight_string):
    """Extrae el peso de la cadena y lo convierte a kilogramos."""
    match = re.search(r"([\d.]+) (kilogramos|kilogramo|kilograms|kilos|kilo|kgs|kg|gramos|gramo|grams|grms|gm|gms|g|miligramos|miligramo|mg|mgs|libras|libra|lbs|lb|pounds|pound|onzas|onza|oz|ounces|ounce)", weight_string, re.IGNORECASE)

    if match:
        value = float(match.group(1))
        unit = match.group(2).lower()

        # Convertir a kilogramos
        weight_kg = convert_weight(value, unit)
        
        # Si el peso es menor a 1 kg, se asigna 1 kg
        if weight_kg < 1:
            weight_kg = 1.0

        return round(weight_kg, 3)
    else:
        raise ValueError("Formato de peso no válido.")






def inch_to_centimeter(inches):
    """Convierte pulgadas a centímetros."""
    return inches * 2.54

def feet_to_centimeter(feet):
    """Convierte pies a centímetros."""
    return feet * 30.48

def get_centimeter(cm):
    """Retorna centímetros (sin conversión necesaria)."""
    return cm

def convert_length(value, unit):
    """Convierte el valor dado a centímetros basado en la unidad especificada."""
    length_unit_data = {
        "pulgadas": inch_to_centimeter,
        "pulgada": inch_to_centimeter,
        "inches": inch_to_centimeter,
        "inch": inch_to_centimeter,
        "in": inch_to_centimeter,
        "pies": feet_to_centimeter,
        "pie": feet_to_centimeter,
        "feet": feet_to_centimeter,
        "ft": feet_to_centimeter,
        "centímetros": get_centimeter,
        "centimetros": get_centimeter,
        "cm": get_centimeter
    }

    if unit in length_unit_data:
        return length_unit_data[unit](value)
    else:
        raise ValueError(f"Unidad no reconocida: {unit}")

def parse_dimensions(dimension_string):
    """Extrae las dimensiones de la cadena y las convierte a centímetros."""
    # Reemplaza comas por puntos
    
    dimension_string = dimension_string.replace(',', '.')

    # Regex para capturar las dimensiones en varios formatos
    match = re.search(
        r"(\d+\.?\d*)\s*[xX*]\s*(\d+\.?\d*)\s*[xX*]?\s*(\d+\.?\d*)?\s*(pulgadas|inches|inch|in|pies|pie|feet|ft|centímetros|centimetros|cm)|"
        r"(\d+\.?\d*)\"l\.\s*x\s*(\d+\.?\d*)\"an\.\s*(?:x\s*(\d+\.?\d*)\"al\.\s*)?(pulgadas|inches|inch|in|pies|pie|feet|ft|centímetros|centimetros|cm)?|"
        r"(\d+\.?\d*)\"?\s*prof\.\s*[xX]\s*(\d+\.?\d*)\"?\s*an\.\s*[xX]\s*(\d+\.?\d*)\"?\s*al\.\s*(pulgadas|inches|inch|in|centímetros|centimetros|cm)?|"
        r"(\d+\.?\d*)\"L\s*[xX]\s*(\d+\.?\d*)\"W\s*(pulgadas|inches|inch|in|centímetros|centimetros|cm)?", 
        dimension_string
    )
    
    if match:
        if match.group(1):  # Primer formato
            length = float(match.group(1))
            width = float(match.group(2))
            height = float(match.group(3)) if match.group(3) else width 
            unit = match.group(4)
        elif match.group(5):  # Segundo formato
            length = float(match.group(5))
            width = float(match.group(6))
            height = float(match.group(7)) if match.group(7) else width  
            unit = match.group(8) if match.group(8) else 'pulgadas'  # Asumir pulgadas si no se especifica unidad
        elif match.group(9):  # formato (con prof., an., al.)
            length = float(match.group(9))
            width = float(match.group(10))
            height = float(match.group(11)) if match.group(11) else width
            unit = match.group(12) if match.group(12) else 'pulgadas'
        else:  # formato '6.5"L x 7.5"W'
            length = float(match.group(13))
            width = float(match.group(14))
            height = width  
            unit = match.group(15) if match.group(15) else 'pulgadas'  

        # Convertir a centímetros según la unidad proporcionada
        length_cm = convert_length(length, unit)
        width_cm = convert_length(width, unit)
        height_cm = convert_length(height, unit)

        return round(length_cm, 3), round(width_cm, 3), round(height_cm, 3)
    else:
        raise ValueError("Formato de dimensiones no válido.")

    #     # Convertir a centímetros
    #     length_cm = convert_length(length, unit)
    #     width_cm = convert_length(width, unit)
    #     height_cm = convert_length(height, unit)

    #     return round(length_cm, 3), round(width_cm, 3), round(height_cm, 3)
    # else:
    #     raise ValueError("Formato de dimensiones no válido.")

def convertir_dimensiones(dimensiones: str) -> tuple:
    """
    Convierte un string de dimensiones en formato "x,xx Unidad" 
    a un tuple con ancho, alto y largo en centímetros.
    
    Args:
        dimensiones (str): Las dimensiones en el formato "x,xx Unidad".
        
    Returns:
        tuple: Un tuple con ancho, alto y largo en centímetros.
    """
    # Extraer el valor numérico del string y la unidad
    partes = dimensiones.split()
    valor = partes[0].replace(',', '.')
    unidad = partes[1] if len(partes) > 1 else ''

    # Convertir el valor a float
    alto_unidad = float(valor)
    
    # Definir ancho y largo
    ancho_unidad = 1.0
    largo_unidad = alto_unidad
    
    # Convertir a centímetros
    length_cm = convert_length(largo_unidad, unidad.lower())
    width_cm = convert_length(ancho_unidad, unidad.lower())
    height_cm = convert_length(alto_unidad, unidad.lower())

    return round(length_cm, 3), round(width_cm, 3), round(height_cm, 3)



def validar_dimensiones(dimension_string: str) -> tuple:

    try:
        return parse_dimensions(dimension_string)
    except ValueError:
        return convertir_dimensiones(dimension_string)