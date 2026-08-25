import os
import pickle
import pytest
from streamlit.testing.v1 import AppTest


@pytest.fixture()
def cards():
    return pickle.load(open("data\\processed\\chinese_matches.p", "rb"))


@pytest.fixture()
def app(cards):
    app = AppTest.from_file("streamlit_record_selection.py", default_timeout=30)
    app.session_state["testing"] = True
    app.session_state["readable_card_id"] = 1
    app.session_state["cards_df"] = cards
    return app


cards_df = pickle.load(open("data\\processed\\chinese_matches.p", "rb"))


# parameterised to check first 2 cards succeed - can change to all cards for a complete test
@pytest.mark.parametrize("card, title", zip([x for x in range(1, 6 + 1)], cards_df["title"]))
def test_select_cards(app, card, title, capsys):
    app.session_state["readable_card_id"] = card
    app.run()
    captured = capsys.readouterr()
    assert "Uncaught app exception" not in captured.err
    assert app.dataframe[0].value.shape == (195, 7)
    assert app.dataframe[0].value.loc[app.session_state["card_idx"], "title"] == title


def test_minimal_cataloguing_view(app):
    app.run()
    assert app.dataframe[0].value.shape == (195, 7)
    assert app.dataframe[0].value.loc[app.session_state["card_idx"], "title"] == "FENG LING DU"
    assert app.session_state["marc_grid_df"].shape == (35, 7)
    assert app.session_state["marc_grid_df"].loc[0, "0"].split(" ")[-1] == "https://id.oclc.org/worldcat/entity/E39PBJyGX9xGJhBxc6rtqhkkXd"

    app.toggle[0].set_value(False)
    app.run()
    assert app.session_state["marc_grid_df"].shape == (59, 7)
    assert app.session_state["marc_grid_df"].loc[1, "0"] == "ocm23921305"


def test_max_to_display(app):
    app.run()

    app.number_input[0].set_value(4)
    app.button[0].click()
    app.run()
    assert app.session_state["marc_grid_df"].shape == (34, 6)


def test_remove_record(app):
    app.run()

    app.multiselect[0].set_value([4])  # remove same record as test_max_to_display
    app.button[0].click()
    app.run()
    assert app.session_state["marc_grid_df"].shape == (35, 7)
    assert app.session_state["marc_grid_df"].columns[-1] == "5"


def test_cat_lang(app):
    app.run()
    assert app.session_state["filtered_df"].shape == (9, 12)

    app.multiselect[1].set_value([])  # remove same record as test_max_to_display
    app.button[0].click()
    app.run()
    assert app.session_state["filtered_df"].shape == (12, 12)


def test_pub_year(app):
    app.run()
    assert app.session_state["filtered_df"].shape == (9, 12)

    app.select_slider[0].set_value([1939, 1946])  # remove same record as test_max_to_display
    app.button[0].click()
    app.run()
    assert app.session_state["filtered_df"].shape == (7, 12)

    app.select_slider[0].set_value([1939, 1939])  # remove same record as test_max_to_display
    app.button[0].click()
    app.run()
    assert app.session_state["filtered_df"].shape == (5, 12)


def test_generic_filter(app):
    app.run()
    assert len(app.columns) == 24

    # setting just filter field shouldn't do anything
    app.columns[8].multiselect[0].set_value(["001"])
    app.button[0].click()
    assert app.session_state["marc_table_all_recs_df"].equals(app.session_state["marc_table_filtered_recs"])

    app.columns[8].multiselect[0].set_value(["001"])  #
    app.columns[9].text_input[0].set_value("ocm23921305")
    app.button[0].click()
    app.run()
    assert app.session_state["marc_table_filtered_recs"].shape == (65, 1)

    app.columns[8].multiselect[0].set_value(["001", "005"])  #
    app.columns[9].text_input[0].set_value("ocn; 3.1")
    app.button[0].click()
    app.run()
    assert app.session_state["marc_table_filtered_recs"].shape == (65, 2)

    app.columns[8].multiselect[0].set_value(["648"])  #
    app.columns[9].text_input[0].set_value("1900")
    app.button[0].click()
    app.run()
    assert app.session_state["marc_table_filtered_recs"].shape == (65, 4)

    # allow records that don't have a 648 field as well as matches to filter
    app.columns[8].multiselect[0].set_value(["648"])  #
    app.columns[9].text_input[0].set_value("1900")
    app.columns[11].checkbox[0].set_value(True)
    app.button[0].click()
    app.run()
    assert app.session_state["marc_table_filtered_recs"].shape == (65, 9)


def test_sort_records(app):
    app.run()
    assert app.session_state["marc_table_filtered_recs"].shape == (65, 9)
    assert app.session_state["marc_table_filtered_recs"].columns.to_list() == [0, 1, 2, 3, 4, 5, 8, 10, 11]

    app.columns[12].multiselect[0].set_value(["num_subject_access"])
    app.button[0].click()
    app.run()
    assert app.session_state["marc_table_filtered_recs"].columns.to_list() == [2, 5, 0, 3, 1, 4, 8, 10, 11]

    app.columns[12].multiselect[0].set_value(["num_rda"])  # all have 3 on the test card
    app.button[0].click()
    app.run()
    assert app.session_state["marc_table_filtered_recs"].columns.to_list() == [0, 1, 2, 3, 4, 5, 8, 10, 11]

    app.columns[12].multiselect[0].set_value(["num_linked"])
    app.button[0].click()
    app.run()
    assert app.session_state["marc_table_filtered_recs"].columns.to_list() == [2, 5, 1, 0, 4, 3, 8, 10, 11]

    app.columns[12].multiselect[0].set_value(["has_phys_desc"])  # all True for the test card
    app.button[0].click()
    app.run()
    assert app.session_state["marc_table_filtered_recs"].columns.to_list() == [0, 1, 2, 3, 4, 5, 8, 10, 11]

    app.columns[12].multiselect[0].set_value(["good_encoding_level"])  # all True for the test card
    app.button[0].click()
    app.run()
    assert app.session_state["marc_table_filtered_recs"].columns.to_list() == [0, 1, 2, 3, 4, 5, 8, 10, 11]

    app.columns[12].multiselect[0].set_value(["record_length"])
    app.button[0].click()
    app.run()
    assert app.session_state["marc_table_filtered_recs"].columns.to_list() == [2, 5, 0, 4, 3, 1, 11, 8, 10]


def test_marc_highlight(app):
    app.run()
    for col in app.session_state["ag"].grid_options["columnDefs"][2:]:
        assert "backgroundColor" in col["cellStyle"]

    app.columns[13].checkbox[0].set_value(False)  # uncheck 'Highlight common fields'
    app.button[0].click()
    app.run()
    if app.session_state["match_exists"]:
        match = app.session_state["existing_match"]
        col_idx = app.session_state["marc_grid_df"].columns.get_loc(str(match))
        assert "backgroundColor" in app.session_state["ag"].grid_options["columnDefs"].pop(col_idx)["cellStyle"]
        for col in app.session_state["ag"].grid_options["columnDefs"][2:]:
            assert "backgroundColor" not in col["cellStyle"]
    else:
        for col in app.session_state["ag"].grid_options["columnDefs"][2:]:
            assert "backgroundColor" not in col["cellStyle"]

    # force a test of not highlight
    app.session_state["readable_card_id"] = len(cards_df)  # last card hasn't been assigned a match
    app.run()
    for col in app.session_state["ag"].grid_options["columnDefs"][2:]:
        assert "backgroundColor" not in col["cellStyle"]


@pytest.fixture(scope="module")
def test_cards():
    return pickle.load(open("tests\\10_cards_test.p", "rb"))


def test_save_match(test_cards, app, tmp_path):
    subset = ["simple_id", "title", "author", "selected_match_ocn", "derivation_complete", "shelfmark", "lines"]
    assert test_cards.loc[:, subset].shape == (10, 7)
    assert test_cards.loc[:, subset]["selected_match_ocn"].dropna().shape == (5,)
    app.session_state["cards_df"] = test_cards
    app.session_state["save_file"] = tmp_path / "tmp_cards.p"
    app.run()

    assert app.session_state["match_exists"] == True
    assert app.dataframe[0].value.shape == (10, 7)
    assert app.dataframe[0].value.dtypes.equals(test_cards.loc[:, subset].dtypes)
    assert app.dataframe[0].value["selected_match_ocn"].iloc[0] == "23921305"  # sometimes gets cast to str
    assert app.dataframe[0].value.dropna().shape == (0, 7)

    app.columns[14].button[1].click()
    app.run()
    assert app.dataframe[0].value.iloc[0]["selected_match_ocn"] is None  # sometimes gets cast to str
    assert pickle.load(open(app.session_state["save_file"], "rb")).iloc[0]["selected_match_ocn"] is None

    app.columns[14].radio[0].set_value(0)
    app.columns[14].button[0].click()
    app.run()
    assert app.dataframe[0].value.iloc[0]["selected_match_ocn"] == "23921305"
    assert os.path.exists(app.session_state["save_file"])
    assert pickle.load(open(app.session_state["save_file"], "rb")).iloc[0]["selected_match_ocn"] == "ocm23921305"

    # test non-default card
    app.session_state["readable_card_id"] = 5
    app.columns[14].radio[0].set_value(0)
    app.columns[14].button[0].click()
    app.run()
    assert app.dataframe[0].value.iloc[4]["selected_match_ocn"] == "11283982"  # sometimes gets cast to str
    assert pickle.load(open(app.session_state["save_file"], "rb")).iloc[4]["selected_match_ocn"] == "ocm11283982"

    app.session_state["readable_card_id"] = 5
    app.columns[14].button[1].click()
    app.run()
    assert app.dataframe[0].value.iloc[4]["selected_match_ocn"] is None  # sometimes gets cast to str
    assert pickle.load(open(app.session_state["save_file"], "rb")).iloc[4]["selected_match_ocn"] is None


def test_save_and_clear(test_cards, app, tmp_path):
    subset = ["simple_id", "title", "author", "selected_match_ocn", "derivation_complete", "shelfmark", "lines"]
    assert test_cards.loc[:, subset].shape == (10, 7)
    assert test_cards.loc[:, subset]["selected_match_ocn"].dropna().shape == (5,)
    app.session_state["cards_df"] = test_cards
    app.session_state["save_file"] = tmp_path / "tmp_cards.p"
    app.run()
    assert app.dataframe[0].value.iloc[0]["selected_match_ocn"] == "23921305"

    app.session_state["readable_card_id"] = 6
    app.columns[14].radio[0].set_value(0)
    app.columns[14].button[0].click()
    app.run()

    assert app.dataframe[0].value.iloc[5]["selected_match_ocn"] == "953743623"
    app.columns[14].button[1].click()
    app.run()

    assert app.session_state["readable_card_id"] == 6
    assert app.dataframe[0].value.iloc[0]["selected_match_ocn"] == "23921305"
    assert app.dataframe[0].value.iloc[5]["selected_match_ocn"] is None
    assert pickle.load(open(app.session_state["save_file"], "rb")).iloc[5]["selected_match_ocn"] is None