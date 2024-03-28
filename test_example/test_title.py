
import pytest
import report
report.Launch.start_launch()

class AAA:
    def __init__(self) -> None:
        pass

    @report.step()
    def aaa(self):
        pass

@pytest.fixture(autouse=False)
@report.step('new fixt0')
def new_fixt0(new_fixt2):
    pass


@report.step('Test 2 {0}')
def b(a: str):
    c(1)


@report.step()
def c(b: int):
    pass


@report.feature('Feature')
class RxPacketsThresholdsSystemTest:
    def test_rx_fpga_daphy_detection_decoding_v4(self):
        pass


@report.feature('Feature2')
class RxFpgaDaphyTest(RxPacketsThresholdsSystemTest): 
    pass
@report.feature('Feature2')
class RxFpgaDaphyTest2(RxPacketsThresholdsSystemTest): 
    pass

@report.story('FPGA DAPHY FIRST PACKET OS30 10Mhz')
class TestRxFpgaDaphy_OS30_10Mhz2(RxFpgaDaphyTest2):
    def test_b(self):
        with report.step('Context Manager'):
            pass
        b('a')
@report.story('FPGA DAPHY FIRST PACKET OS30 10Mhz')
class TestRxFpgaDaphy_OS30_10Mhz(RxFpgaDaphyTest):
    @pytest.fixture(autouse=True)
    @report.step('new fixt1 {new_fixt2}')
    def new_fixt1(self, new_fixt2):
        pass

    @pytest.fixture(autouse=False)
    @report.step('new fixt2')
    def new_fixt2(self):
        pass

    @pytest.fixture(autouse=False)
    @report.step('new fixt3')
    def new_fixt3(self):
        yield 1

    @report.step()
    async def ab(self):
        pass
    # @pytest.mark.xfail(reason='test')
    # @pytest.mark.skip(reason='test')
    @report.title('Test A')
    async def test_a(self, new_fixt3):
        report.log(message='Test Log')
        a = AAA()
        a.aaa()
        b('a')
        await self.ab()
        c(2)
        with open('./TestTxJitterMeasures.txt', 'rb') as f:
            attachment = f.read()

        with report.step('Test context manager'):
            pass

        report.add_launch_properties(key='test', nd_key='2ndtest')
        report.add_link_to_launch('Test', 'https://google.com')
        report.add_link_to_launch('Test 2', 'https://google.com')
        report.attachment(name='test', attachment=attachment, attachment_type=report.attachment_type.TEXT, level="DEBUG")
        report.dynamic.link('TEST TITLE', 'https://google.com')
        assert False