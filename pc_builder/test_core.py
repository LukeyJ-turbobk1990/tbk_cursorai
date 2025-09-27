import unittest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock

# Import the core classes from core.py
from core import (
    ConfigManager, ComponentValidator, CompatibilityChecker, 
    EmailService, BuildSubmission, Component, COMPONENT_CATEGORIES,
    NAMING_EXAMPLES, CASE_COMPATIBILITY
)

class TestConfigManager(unittest.TestCase):
    """Test ConfigManager functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        # Clean up any test files
        if os.path.exists('config.json'):
            os.remove('config.json')
    
    def test_load_config_new_file(self):
        """Test loading config when file doesn't exist"""
        config = ConfigManager.load_config()
        self.assertIn('email', config)
        self.assertIn('components', config)
        self.assertEqual(config['email'], 'your@email.com')
        for cat in COMPONENT_CATEGORIES:
            self.assertIn(cat, config['components'])
    
    def test_load_config_existing_file(self):
        """Test loading config from existing file"""
        test_config = {
            'email': 'test@example.com',
            'components': {cat: [] for cat in COMPONENT_CATEGORIES}
        }
        with open('config.json', 'w') as f:
            json.dump(test_config, f)
        
        config = ConfigManager.load_config()
        self.assertEqual(config['email'], 'test@example.com')
    
    def test_save_config(self):
        """Test saving config"""
        test_config = {
            'email': 'test@example.com',
            'components': {cat: [] for cat in COMPONENT_CATEGORIES}
        }
        ConfigManager.save_config(test_config)
        
        with open('config.json', 'r') as f:
            saved_config = json.load(f)
        
        self.assertEqual(saved_config['email'], 'test@example.com')

class TestComponentValidator(unittest.TestCase):
    """Test ComponentValidator functionality"""
    
    def test_validate_cpu_valid(self):
        """Test CPU validation with valid name"""
        name = "Intel i5-12400 (LGA1700, 165mm cooler)"
        result = ComponentValidator.validate_component_name(name, 'CPU')
        self.assertIsNone(result)
    
    def test_validate_cpu_invalid(self):
        """Test CPU validation with invalid name"""
        name = "Intel i5-12400"
        result = ComponentValidator.validate_component_name(name, 'CPU')
        self.assertIsNotNone(result)
        self.assertIn("socket type", result)
    
    def test_validate_motherboard_valid(self):
        """Test Motherboard validation with valid name"""
        name = "MSI B660M (LGA1700, DDR4, 3200MHz, mATX)"
        result = ComponentValidator.validate_component_name(name, 'Motherboard')
        self.assertIsNone(result)
    
    def test_validate_motherboard_invalid(self):
        """Test Motherboard validation with invalid name"""
        name = "MSI B660M"
        result = ComponentValidator.validate_component_name(name, 'Motherboard')
        self.assertIsNotNone(result)
        self.assertIn("form factor", result)
    
    def test_validate_ram_valid(self):
        """Test RAM validation with valid name"""
        name = "Corsair Vengeance 16GB (DDR4, 3200MHz)"
        result = ComponentValidator.validate_component_name(name, 'RAM')
        self.assertIsNone(result)
    
    def test_validate_gpu_valid(self):
        """Test GPU validation with valid name"""
        name = "NVIDIA RTX 4070 (280mm, 1x8-pin)"
        result = ComponentValidator.validate_component_name(name, 'GPU')
        self.assertIsNone(result)
    
    def test_validate_psu_valid(self):
        """Test PSU validation with valid name"""
        name = "Corsair RM750x (750W, 2x8-pin PCIe)"
        result = ComponentValidator.validate_component_name(name, 'PSU')
        self.assertIsNone(result)
    
    def test_validate_case_valid(self):
        """Test Case validation with valid name"""
        name = "NZXT H510 (ATX, 360mm GPU clearance, 165mm CPU cooler clearance)"
        result = ComponentValidator.validate_component_name(name, 'Case')
        self.assertIsNone(result)

class TestCompatibilityChecker(unittest.TestCase):
    """Test CompatibilityChecker functionality"""
    
    def test_socket_compatibility_valid(self):
        """Test valid socket compatibility"""
        selections = {
            'CPU': 'Intel i5-12400 (LGA1700, 165mm cooler)',
            'Motherboard': 'MSI B660M (LGA1700, DDR4, 3200MHz, mATX)',
            'RAM': 'Corsair Vengeance 16GB (DDR4, 3200MHz)',
            'GPU': 'NVIDIA RTX 4070 (280mm, 1x8-pin)',
            'PSU': 'Corsair RM750x (750W, 2x8-pin PCIe)',
            'Case': 'NZXT H510 (ATX, 360mm GPU clearance, 165mm CPU cooler clearance)'
        }
        compatible, msg = CompatibilityChecker.check_compatibility(selections)
        self.assertTrue(compatible)
        self.assertEqual(msg, '')
    
    def test_socket_compatibility_invalid(self):
        """Test invalid socket compatibility"""
        selections = {
            'CPU': 'Intel i5-12400 (LGA1700, 165mm cooler)',
            'Motherboard': 'ASUS B550 (AM4, DDR4, 3600MHz, ATX)',
            'RAM': 'Corsair Vengeance 16GB (DDR4, 3200MHz)',
            'GPU': 'NVIDIA RTX 4070 (280mm, 1x8-pin)',
            'PSU': 'Corsair RM750x (750W, 2x8-pin PCIe)',
            'Case': 'NZXT H510 (ATX, 360mm GPU clearance, 165mm CPU cooler clearance)'
        }
        compatible, msg = CompatibilityChecker.check_compatibility(selections)
        self.assertFalse(compatible)
        self.assertIn('socket', msg)
    
    def test_case_form_factor_compatibility(self):
        """Test case and motherboard form factor compatibility"""
        selections = {
            'CPU': 'Intel i5-12400 (LGA1700, 165mm cooler)',
            'Motherboard': 'MSI B660M (LGA1700, DDR4, 3200MHz, mATX)',
            'RAM': 'Corsair Vengeance 16GB (DDR4, 3200MHz)',
            'GPU': 'NVIDIA RTX 4070 (280mm, 1x8-pin)',
            'PSU': 'Corsair RM750x (750W, 2x8-pin PCIe)',
            'Case': 'Cooler Master NR200 (mini-ITX, 330mm GPU, 155mm cooler)'
        }
        compatible, msg = CompatibilityChecker.check_compatibility(selections)
        self.assertFalse(compatible)
        self.assertIn('Case', msg)
    
    def test_ram_compatibility_valid(self):
        """Test valid RAM compatibility"""
        selections = {
            'CPU': 'Intel i5-12400 (LGA1700, 165mm cooler)',
            'Motherboard': 'MSI B660M (LGA1700, DDR4, 3200MHz, mATX)',
            'RAM': 'Corsair Vengeance 16GB (DDR4, 3200MHz)',
            'GPU': 'NVIDIA RTX 4070 (280mm, 1x8-pin)',
            'PSU': 'Corsair RM750x (750W, 2x8-pin PCIe)',
            'Case': 'NZXT H510 (ATX, 360mm GPU clearance, 165mm CPU cooler clearance)'
        }
        compatible, msg = CompatibilityChecker.check_compatibility(selections)
        self.assertTrue(compatible)
    
    def test_ram_compatibility_invalid_type(self):
        """Test invalid RAM type compatibility"""
        selections = {
            'CPU': 'Intel i5-12400 (LGA1700, 165mm cooler)',
            'Motherboard': 'MSI B660M (LGA1700, DDR4, 3200MHz, mATX)',
            'RAM': 'Corsair Vengeance 16GB (DDR5, 6000MHz)',
            'GPU': 'NVIDIA RTX 4070 (280mm, 1x8-pin)',
            'PSU': 'Corsair RM750x (750W, 2x8-pin PCIe)',
            'Case': 'NZXT H510 (ATX, 360mm GPU clearance, 165mm CPU cooler clearance)'
        }
        compatible, msg = CompatibilityChecker.check_compatibility(selections)
        self.assertFalse(compatible)
        self.assertIn('RAM type', msg)
    
    def test_psu_wattage_insufficient(self):
        """Test insufficient PSU wattage"""
        selections = {
            'CPU': 'Intel i9-13900K (LGA1700, 170mm cooler)',
            'Motherboard': 'MSI B660M (LGA1700, DDR4, 3200MHz, mATX)',
            'RAM': 'Corsair Vengeance 16GB (DDR4, 3200MHz)',
            'GPU': 'NVIDIA RTX 4090 (304mm, 1x16-pin)',
            'PSU': 'EVGA 450W (450W, 1x8-pin PCIe)',
            'Case': 'NZXT H510 (ATX, 360mm GPU clearance, 165mm CPU cooler clearance)'
        }
        compatible, msg = CompatibilityChecker.check_compatibility(selections)
        self.assertFalse(compatible)
        self.assertIn('insufficient', msg)
    
    def test_gpu_length_exceeds_case(self):
        """Test GPU length exceeding case clearance"""
        selections = {
            'CPU': 'Intel i5-12400 (LGA1700, 165mm cooler)',
            'Motherboard': 'MSI B660M (LGA1700, DDR4, 3200MHz, mATX)',
            'RAM': 'Corsair Vengeance 16GB (DDR4, 3200MHz)',
            'GPU': 'NVIDIA RTX 4090 (400mm, 1x16-pin)',
            'PSU': 'Corsair RM750x (750W, 2x8-pin PCIe)',
            'Case': 'NZXT H510 (ATX, 360mm GPU clearance, 165mm CPU cooler clearance)'
        }
        compatible, msg = CompatibilityChecker.check_compatibility(selections)
        self.assertFalse(compatible)
        self.assertIn('GPU length', msg)

class TestEmailService(unittest.TestCase):
    """Test EmailService functionality"""
    
    def test_build_submission_creation(self):
        """Test BuildSubmission dataclass"""
        build = BuildSubmission(
            components={'CPU': 'Intel i5-12400 (LGA1700, 165mm cooler)'},
            total_price='Total: $299.99',
            user_email='test@example.com'
        )
        self.assertEqual(build.user_email, 'test@example.com')
        self.assertIn('CPU', build.components)
    
    @patch('core.smtplib.SMTP')
    def test_send_build_submission_success(self, mock_smtp):
        """Test successful email sending"""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        build = BuildSubmission(
            components={'CPU': 'Intel i5-12400 (LGA1700, 165mm cooler)'},
            total_price='Total: $299.99',
            user_email='test@example.com'
        )
        
        result = EmailService.send_build_submission(build, 'admin@example.com')
        self.assertTrue(result)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called_once()
    
    @patch('core.smtplib.SMTP')
    def test_send_build_submission_failure(self, mock_smtp):
        """Test failed email sending"""
        mock_smtp.side_effect = Exception("Connection failed")
        
        build = BuildSubmission(
            components={'CPU': 'Intel i5-12400 (LGA1700, 165mm cooler)'},
            total_price='Total: $299.99',
            user_email='test@example.com'
        )
        
        result = EmailService.send_build_submission(build, 'admin@example.com')
        self.assertFalse(result)

class TestConstants(unittest.TestCase):
    """Test application constants"""
    
    def test_component_categories(self):
        """Test component categories are properly defined"""
        expected_categories = ['CPU', 'Motherboard', 'RAM', 'GPU', 'PSU', 'Case']
        self.assertEqual(COMPONENT_CATEGORIES, expected_categories)
    
    def test_naming_examples(self):
        """Test naming examples are available for all categories"""
        for category in COMPONENT_CATEGORIES:
            self.assertIn(category, NAMING_EXAMPLES)
            self.assertIsInstance(NAMING_EXAMPLES[category], str)
            self.assertGreater(len(NAMING_EXAMPLES[category]), 0)
    
    def test_case_compatibility_matrix(self):
        """Test case compatibility matrix"""
        self.assertIn('ATX', CASE_COMPATIBILITY)
        self.assertIn('mATX', CASE_COMPATIBILITY)
        self.assertIn('mini-ITX', CASE_COMPATIBILITY)
        
        # Test that ATX can fit smaller form factors
        self.assertIn('mATX', CASE_COMPATIBILITY['ATX'])
        self.assertIn('mini-ITX', CASE_COMPATIBILITY['ATX'])

class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def test_config_manager_integration(self):
        """Test ConfigManager integration with file system"""
        # Test full cycle: save and load
        test_config = {
            'email': 'integration@test.com',
            'components': {cat: [] for cat in COMPONENT_CATEGORIES}
        }
        
        ConfigManager.save_config(test_config)
        loaded_config = ConfigManager.load_config()
        
        self.assertEqual(loaded_config['email'], 'integration@test.com')
        for cat in COMPONENT_CATEGORIES:
            self.assertIn(cat, loaded_config['components'])
    
    def test_component_validation_integration(self):
        """Test component validation with real examples"""
        test_cases = [
            ('CPU', 'Intel i5-12400 (LGA1700, 165mm cooler)', True),
            ('CPU', 'Intel i5-12400', False),
            ('Motherboard', 'MSI B660M (LGA1700, DDR4, 3200MHz, mATX)', True),
            ('Motherboard', 'MSI B660M', False),
            ('RAM', 'Corsair Vengeance 16GB (DDR4, 3200MHz)', True),
            ('RAM', 'Corsair Vengeance 16GB', False),
        ]
        
        for category, name, should_be_valid in test_cases:
            result = ComponentValidator.validate_component_name(name, category)
            if should_be_valid:
                self.assertIsNone(result, f"Validation failed for {category}: {name}")
            else:
                self.assertIsNotNone(result, f"Validation should have failed for {category}: {name}")

if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)