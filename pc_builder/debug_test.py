from core import CompatibilityChecker

# Test the extraction methods
cpu = 'Intel i5-12400 (LGA1700, 165mm cooler)'
mobo = 'MSI B660M (LGA1700, DDR4, 3200MHz, mATX)'
case = 'NZXT H510 (ATX, 360mm GPU clearance, 165mm CPU cooler clearance)'

print("CPU socket:", CompatibilityChecker._extract_socket(cpu))
print("Motherboard socket:", CompatibilityChecker._extract_socket(mobo))
print("Case form factor:", CompatibilityChecker._extract_form_factor(case))
print("Motherboard form factor:", CompatibilityChecker._extract_form_factor(mobo))

# Test compatibility
selections = {
    'CPU': cpu,
    'Motherboard': mobo,
    'RAM': 'Corsair Vengeance 16GB (DDR4, 3200MHz)',
    'GPU': 'NVIDIA RTX 4070 (280mm, 1x8-pin)',
    'PSU': 'Corsair RM750x (750W, 2x8-pin PCIe)',
    'Case': case
}

compatible, msg = CompatibilityChecker.check_compatibility(selections)
print("Compatible:", compatible)
print("Message:", msg)