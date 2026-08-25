import src.data.xml_extraction as xmle
from tqdm import tqdm
from functools import partialmethod

tqdm.__init__ = partialmethod(tqdm.__init__, disable=True)


ns = "{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}"


def test_extract_labelled_xml():
    xml_path = "tests/0001_24567971014.xml"
    record = xmle.extract_labelled_xml(xml_path, ns)
    assert len(record) == 4
    assert record["card_xml"] == "tests/0001_24567971014.xml"
    assert record["title"] == ["KAUL-I-TAIYIB"]
    assert record["author"] == ["BARNI (Muhammad Ilyas), Maulana, M.A., LL.B."]
    assert record["shelfmark"] == ["14115. e. 72"]
