"""
Removed any data processing prior to delivery of cards_df to simplify env for streamlit
Will need to prepare elsewhere then pull in as pickle or csv
"""
import os
import pickle
import platform

import pandas as pd
import streamlit as st
from PIL import Image
import s3fs

import cfg
from src.utils import streamlit_utils as st_utils
from src.docs import doc_strings as docs

st.set_page_config(layout="wide")
st.session_state["testing"] = st.session_state.get("testing", False)

if platform.system() == "Linux":  # community cloud runs linux
    LOCAL_DATA = False
elif platform.system() == "Windows":
    LOCAL_DATA = True  # edit if want to trial remote data locally

s3 = s3fs.S3FileSystem(anon=False)

st.title("Worldcat results for searches for catalogue card title/author")

with open("sidebar_docs.txt", encoding="utf-8") as f:
    sidebar_docs_txt = f.read()
with st.sidebar:
    st.markdown(sidebar_docs_txt)

if st.session_state["testing"]:
    cards_df = st.session_state["cards_df"]
    pass  # cards_df and save_file defined in tests
elif LOCAL_DATA:
    st.session_state["save_file"] = "data/processed/chinese_matches.p"
    cards_df = pickle.load(open(st.session_state["save_file"], "rb"))
    st.write("Loaded cards info from local")
else:
    st.session_state["save_file"] = 'cac-bucket/chinese_matches.p'
    cards_df = st_utils.load_s3(s3, st.session_state["save_file"])
    st.write("Loaded cards info from AWS")

number_of_cards_container = st.empty()
card_table_instructions = st.empty()
card_table_container = st.empty()
subset = ["simple_id", "title", "author", "selected_match_ocn", "derivation_complete", "shelfmark", "lines"]

card_selection = st_utils.update_card_table(df=cards_df, subset=subset, container=card_table_container)

nulls = len(cards_df) - len(cards_df.dropna(subset="worldcat_matches"))
number_of_cards_container.write(
    f"Showing {len(cards_df.dropna(subset='worldcat_matches'))} cards with Worldcat results."
    # f"out of of {len(cards_df)} total cards, omitting {nulls} without results."
)

card_table_instructions.write(docs.card_table_instructions)

if not card_selection["selection"]["rows"]:
    st.session_state["readable_card_id"] = st.session_state.get("readable_card_id", 1)
else:
    st.session_state["readable_card_id"] = int(card_selection["selection"]["rows"][0]) + 1

card_idx = cards_df.query("simple_id == @st.session_state['readable_card_id']").index.values[0]
st.session_state["card_idx"] = card_idx

st.session_state["existing_match"] = cards_df.loc[card_idx, "selected_match"]
st.session_state["match_exists"] = isinstance(st.session_state["existing_match"], int)

if st.session_state["match_exists"]:
    apparent_oclc_num = cards_df.loc[card_idx, "selected_match_ocn"]
    actual_oclc_num = cards_df.loc[card_idx, "worldcat_matches"][st.session_state["existing_match"]].get_fields("001")[0].data
    if apparent_oclc_num != actual_oclc_num:
        st.warning(docs.oclc_num_warning)

cards_df["author"] = cards_df["author"].apply(lambda x: x if x else "")

st.write("\n")
st.subheader("Select from Worldcat results")

card_jpg_path = os.path.join("data/raw/chinese/1016992", cards_df.loc[card_idx, "xml"][:-5] + ".jpg")

search_ti = cards_df.loc[card_idx, 'title'].replace(' ', '+')
search_au = cards_df.loc[card_idx, 'author'].replace(' ', '+')
search_term = f"https://www.worldcat.org/search?q=ti%3A{search_ti}+AND+au%3A{search_au}"

ic_left, ic_centred = st.columns([0.3, 0.7])
ic_centred.image(Image.open(card_jpg_path), use_column_width=True)
label_text = f"""You can check the [Worldcat search]({search_term}) for this card"""
ic_left.write(label_text)
sm = cards_df.loc[card_idx, 'shelfmark']
sm_correction = ic_left.text_input(label=f"The extracted shelfmark is {sm}. If incorrect change the value below and press enter.", value=sm)
if sm != sm_correction:
    ic_left.markdown(f":green[Shelfmark updated]")
    cards_df.loc[card_idx, 'shelfmark'] = sm_correction
    st_utils.update_card_table(df=cards_df, subset=subset, container=card_table_container)
    st_utils.push_to_storage(local=LOCAL_DATA, save_file=st.session_state["save_file"], df=cards_df, s3=s3)

filtered_records_empty = ic_left.empty()

minimal_cataloguing_view = ic_left.toggle("Minimal cataloguing view", value=True, help=docs.min_cat_help_text)

marc_table = st.empty()
match_df = pd.DataFrame({"record": list(cards_df.loc[card_idx, "worldcat_matches"])})
match_df = st_utils.create_filter_columns(match_df, cfg.LANG_DICT, search_au)
all_marc_fields = sorted(list(set(match_df["record"].apply(lambda x: [y.tag for y in x.get_fields()]).sum())))
all_languages = match_df["language"].unique()

# Filters form
with st.form("filters"):
    apply_col, max_to_display_col, removed_records_col = st.columns([0.1, 0.2, 0.7])

    apply_filters = apply_col.form_submit_button(label="Apply filters")

    max_to_display = int(
        max_to_display_col.number_input("Max records to display", min_value=1, value=5, help=docs.max_to_display_help)
    )

    # It is possible to remove a previously selected record from the comparison
    records_to_ignore = removed_records_col.multiselect(
        label="Select incorrect records you'd like to remove from the comparison",
        options=match_df.index
    )

    if "English" in all_languages:
        default_lang = "English"
    else:
        default_lang = None

    lang_select = st.multiselect(
        "Select Cataloguing Language (040 $b)",
        match_df["language"].unique(),
        format_func=lambda x: f"{x} ({len(match_df.query('language == @x'))} total)",
        default=default_lang
    )

    st.write("####")
    _, date_slider_col, _ = st.columns([0.05, 0.9, 0.05])
    pub_dates = match_df.query("publication_date > -9999")["publication_date"].sort_values().dropna().unique().astype(int)
    if len(pub_dates) == 0:
        pub_dates = [1900, 2000]
    elif len(pub_dates) == 1:
        pub_dates = [pub_dates[0] - 1, pub_dates[0], pub_dates[0] + 1]
    date_slider = date_slider_col.select_slider(
        label='Select publication year',
        options=pub_dates,
        value=(min(pub_dates), max(pub_dates)),
        help=(docs.date_select_help)
    )

    st.write("####")
    generic_field_col, generic_field_contains_col, _, include_recs_without_field_col = st.columns([0.26, 0.38, 0.033, 0.19], vertical_alignment="bottom")
    search_on_marc_fields = generic_field_col.multiselect(
        "Select MARC field",
        all_marc_fields,
        help="[LoC MARC fields](https://www.loc.gov/marc/bibliographic/)"
    )
    search_terms = generic_field_contains_col.text_input("MARC field contains", help=(docs.generic_field_search_help))

    search_terms = search_terms.split(";")
    if search_terms == [""]:  # clear if no search terms
        search_terms, search_on_marc_fields = [], []
    include_recs_without_field = include_recs_without_field_col.checkbox("Allow records without specified MARC fields")

    if len(search_on_marc_fields) != len(search_terms):
        st.markdown(
            (f":red[**Searching on {len(search_on_marc_fields)} MARC fields, "
             f"but {len(search_terms.split(';'))} search terms specified. "
             f"Please change number of searched on MARC fields or number of ';' seperated search terms**]")
        )

    # filter option columns defined below to display in the filters users can choose from
    filter_options = ["num_subject_access", "num_rda", "num_linked", "has_phys_desc", "good_encoding_level", "record_length"]

    sort_options_col, highlight_col = st.columns([0.65, 0.2], gap="large", vertical_alignment="center")
    sort_options = sort_options_col.multiselect(label=("Select how to sort matching records."), options=filter_options,
                                                format_func=st_utils.pretty_filter_option, help=(docs.sort_options_help))

    highlight_button = highlight_col.checkbox("Highlight common fields", value=True,
                                              help="Highlight field values that are common between two or more records.")


if not lang_select:
    lang_select = all_languages
filter_query = "language in @lang_select" \
               "& ((@date_slider[0] <= publication_date and publication_date <= @date_slider[1])" \
               "or publication_date == -9999)"
filtered_df = match_df.query(filter_query).copy()
st.session_state["filtered_df"] = filtered_df
sorted_filtered_df = filtered_df.sort_values(by=sort_options, ascending=False)

formatted_records, fmt_new_idx = [], []
for i in range(len(sorted_filtered_df)):
    res = sorted_filtered_df.iloc[i, 0].get_fields()
    ldr = sorted_filtered_df.iloc[i, 0].leader
    col = pd.DataFrame(
        index=pd.Index(["LDR"] + [x.tag for x in res], name="Field"),
        data=[ldr] + [x.__str__()[6:] for x in res],
        columns=[sorted_filtered_df.iloc[i].name]
    )
    formatted_records.append(st_utils.gen_unique_idx(col))
    # fmt_new_idx.append(st_utils.gen_sf_rpt_unique_idx(col))

marc_table_all_recs_df = pd.concat(formatted_records, axis=1).sort_index(key=st_utils.sort_fields_idx)
st.session_state["marc_table_all_recs_df"] = marc_table_all_recs_df  # for testing
# new_marc_table = pd.concat(fmt_new_idx, axis=1).sort_index()
# st_utils.simplify_6xx(new_marc_table)

marc_table_filtered_recs = st_utils.filter_on_generic_fields(marc_table_all_recs_df, search_on_marc_fields,
                                                             search_terms, include_recs_without_field)
st.session_state["marc_table_filtered_recs"] = marc_table_filtered_recs  # for testing
match_ids = marc_table_filtered_recs.columns.tolist()

record = "records"
if len(records_to_ignore) == 1: record = "record"
n_displayed = min([max_to_display, len(match_ids)])
filtered_records_text = f"""
[Max records to display](#filters) set to {max_to_display}. Displaying {n_displayed} of {len(match_ids)} filtered records.\n
{len(match_df)} total records.  
{len(match_df) - len(match_ids)} removed by filters.  
{len(records_to_ignore)} incorrect {record} removed by user.
"""
filtered_records_empty.write(filtered_records_text)

records_to_display = [x for x in match_ids if x not in records_to_ignore]
excluded_fields = ["063", "064", "068", "072", "078", "079", "250", "776"]
useful_fields = ~marc_table_all_recs_df.index.droplevel(1).isin(excluded_fields)
marc_grid_df = marc_table_all_recs_df.loc[useful_fields, records_to_display[:max_to_display]].dropna(how="all")

minimal_repeat_fields = [x for x in marc_grid_df.index.droplevel(1) if x[0] in ["3", "6"]]
minimal_fields = minimal_repeat_fields + ["100", "245", "260", "880"]  # 100, 245, 260, 300s, 600s, 880s
if minimal_cataloguing_view:
    marc_grid_df = marc_grid_df.loc[marc_grid_df.index.droplevel(1).isin(minimal_fields)]

marc_grid_df = marc_grid_df.reset_index().transform(lambda x: x.str.replace(r"\$\w", st_utils.new_line, regex=True))
marc_grid_df.columns = [str(x) for x in marc_grid_df.columns]

# for testing
st.session_state["marc_grid_df"] = marc_grid_df
st.session_state["ag"] = st_utils.update_marc_table(marc_table, marc_grid_df, highlight_button, st.session_state["existing_match"])

select_col, derive_col = st.columns([0.35, 0.35], gap="large")
with select_col:
    with st.form("record_selection"):
        closest_result_col, save_col = st.columns([0.6, 0.4])
        no_correct_text = "No correct results"
        selected_match = closest_result_col.radio(
            label="Which is the closest Worldcat result?",
            options=(records_to_display[:max_to_display] + [no_correct_text])
        )

        save_col.write("Saving will show the shelfmark and OCLC number for Record Manager. See sidebar for more info on Record Manager.")
        save_res = save_col.form_submit_button(label="Save selection")
        clear_res = save_col.form_submit_button(label="Clear selection")

        success_empty = st.empty()

        sm_field = "852"
        info_text = f"""
                    ➡️ Copy the OCLC Number to search in Record Manager    
                    ➡️ Copy the shelfmark to field {sm_field}  
                    ➡️ Copy the OCR text to a 500 field
                    """
        copy_instruction = st.empty()

        oclc_label_col, oclc_num_col = st.columns([0.5, 0.5])
        sm_label_col, sm_col = st.columns([0.5, 0.5])
        ocr_text_label_col, ocr_text_col = st.columns([0.5, 0.5])

        oclc_label_col.write("OCLC Number:")
        oclc_num_copy = oclc_num_col.empty()

        sm_label_col.write(f"Shelfmark ({sm_field} field):")
        sm_col.code(sm)

        ocr_text_label_col.write("OCR text (500 field):")
        oclc_text_copy = ocr_text_col.empty()

        if st.session_state["match_exists"]:
            oclc_num = cards_df.loc[card_idx, "selected_match_ocn"]
            copy_instruction.info(info_text)
            oclc_num_copy.code(oclc_num.strip('ocn').strip('ocm').strip('on'))
            oclc_text_copy.code("\n".join(cards_df.loc[card_idx, "lines"]))

        if save_res:
            if selected_match == no_correct_text:
                cards_df.loc[card_idx, ["selected_match", "selected_match_ocn"]] = "No match"
                st_utils.update_card_table(cards_df, subset, card_table_container)
                st_utils.push_to_storage(local=LOCAL_DATA, save_file=st.session_state["save_file"], df=cards_df, s3=s3)
                success_empty.success("Non-match recorded!", icon="✅")
            else:
                oclc_num = cards_df.loc[card_idx, "worldcat_matches"][selected_match].get_fields("001")[0].data
                cards_df.loc[card_idx, "selected_match"] = selected_match
                cards_df.loc[card_idx, "selected_match_ocn"] = oclc_num

                st_utils.update_card_table(cards_df, subset, card_table_container)
                st_utils.push_to_storage(local=LOCAL_DATA, save_file=st.session_state["save_file"], df=cards_df, s3=s3)
                st_utils.update_marc_table(marc_table, marc_grid_df, highlight_button, st.session_state["existing_match"])

                copy_instruction.info(info_text)
                oclc_num_copy.code(oclc_num.strip('ocn').strip('ocm').strip('on'))
                oclc_text_copy.code("\n".join(cards_df.loc[card_idx, "lines"]))

                success_empty.success("Selection saved!", icon="✅")

        if clear_res:
            cards_df.loc[card_idx, ["selected_match", "selected_match_ocn", "derivation_complete"]] = None
            st_utils.update_card_table(cards_df, subset, card_table_container)
            st_utils.push_to_storage(local=LOCAL_DATA, save_file=st.session_state["save_file"], df=cards_df, s3=s3)
            st_utils.update_marc_table(marc_table, marc_grid_df, highlight_button, existing_match=False)

            copy_instruction.write("")
            oclc_num_copy.code("")
            oclc_text_copy.code("")

            success_empty.success("Selection cleared!", icon="✅")

with derive_col:
    with st.form("derive_complete"):
        st.write(docs.derivation_complete)
        derivation_complete = st.form_submit_button(label="Derivation complete")
        if derivation_complete:
            cards_df.loc[card_idx, "derivation_complete"] = True
            st_utils.update_card_table(cards_df, subset, card_table_container)
            st_utils.push_to_storage(local=LOCAL_DATA, save_file=st.session_state["save_file"], df=cards_df, s3=s3)
            st.success("Derivation complete!", icon="✅")

        mark_uncomplete = st.form_submit_button(label="Undo derivation complete")
        if mark_uncomplete:
            cards_df.loc[card_idx, "derivation_complete"] = None
            st_utils.update_card_table(cards_df, subset, card_table_container)
            st_utils.push_to_storage(local=LOCAL_DATA, save_file=st.session_state["save_file"], df=cards_df, s3=s3)
            st.success("Derivation cleared!", icon="✅")
