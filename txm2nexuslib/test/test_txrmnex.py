from unittest import TestCase

from txm2nexuslib.txrmnex import XradiaFile

FILE_NAME = "/home/zreszela/workspace/mistral/inhouse/Eva/Sole/20160626/tomo1/1/20160626_S1_tomo1_1.txrm"
FILE_NAME = "/home/zreszela/workspace/mistral/inhouse/Eva/Sole/20160626/tomo1/1/1/20160626_S1_tomo1_0.0_-10113.1.xrm"
SAMPLE_ID = "SampleID"

class Test(TestCase):

    def setUp(self):
        self.file = XradiaFile(FILE_NAME)
        self.file.open()

    def tearDown(self):
        self.file.close()

    def test_sample_id(self):
        sample_id = self.file.get_sample_id()
        print sample_id

    def test_pixel_size(self):
        pixel_size = self.file.get_pixel_size()
        self.assertGreater(pixel_size, 0, "Pixel size is lower than 0")

    def test_xray_magnification(self):
        xray_magnification = self.file.get_xray_magnification()
        self.assertGreaterEqual(xray_magnification, 0,
                                "XRay magnification is lower than 0")

    def test_machine_currents(self):
        machine_currents = self.file.get_machine_currents()
        self.assertGreater(len(machine_currents), 0, "No machine currents")

    def test_energies(self):
        energy = self.file.get_energies()
        self.assertGreater(len(energy), 0, "No energy")
    
    def test_image_height(self):
        image_height = self.file.image_height
        self.assertGreater(image_height, 0, "Image height is lower than 0")

    def test_image_width(self):
        image_width = self.file.image_width
        self.assertGreater(image_width, 0, "Image width is lower than 0")

    def test_data_type(self):
        data_type = self.file.data_type
        self.assertIsInstance(data_type, str, "No data type")
    
    def test_exp_times(self):
        exp_times = self.file.get_exp_times()
        print exp_times
        self.assertGreater(len(exp_times), 0, "No exposure times")
    
    def test_det_zero(self):
        det_zero = self.file.det_zero
        self.assertGreaterEqual(det_zero, 0, "Detector zero is lower than 0")