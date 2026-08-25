import pickle
import re
from typing import Dict, List, Union

from matplotlib import colormaps
import numpy as np
import pandas as pd
import streamlit as st
from st_aggrid import GridOptionsBuilder, JsCode, AgGrid
import s3fs
from pymarc import Record


@st.cache_data
def load_s3(_s3: s3fs.S3FileSystem, s3_path: str):
    with _s3.open(s3_path, 'rb') as f:
        df = pickle.load(f)
    return df


def get_pub_date(record: Record) -> int:
    # Look for a date in first 260$c, if absent include in search anyway
    f260 = record.get_fields("260")
    c_subfields = []
    for x in f260:
        c_subfields.extend(x.get_subfields("c"))
    re_260c = re.compile(r"[0-9]{4}")
    if c_subfields:
        match = re_260c.search(c_subfields[0])
        if match:
            return int(match.group())
        else:
            return -9999
    else:
        return -9999


def get_008_date(record: Record) -> str:
    """
    Slice the date from the correct chunk of the 008 field based on the 6th character ("Type of Date")
    @param record: pymarc.Record
    @return: str
    """
    f008 = record.get_fields("008")[0].data
    date_type = f008[6]
    date_map = {
        's': slice(7, 11), 'r': slice(7, 11), 'q': slice(7, 15), 'n': slice(0, 0), 'm': slice(7, 15),
        'c': slice(7, 15), 't': slice(7, 11), 'd': slice(7, 15), 'e': slice(7, 11), 'i': slice(7, 15)
    }
    return f008[date_map[date_type]]


def pretty_filter_option(option: str) -> str:
    """
    Convert backend filter string to frontend label
    @param option: str
    @return: str
    """
    display_dict = {
        "num_subject_access": "Number of subject access fields",
        "num_rda": "Number of RDA fields",
        "num_linked": "Number of linked fields",
        "has_phys_desc": "Has a physical description",
        "good_encoding_level": "Encoding level not 3/5/7",
        "record_length": "Number of fields in record"
    }
    return display_dict[option]


def gen_unique_idx(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate a unique index from one that contains repeated fields
    @param df: pd.DataFrame
    @return: pd.DataFrame
    """
    out_df = df.copy()
    out_df["Repeat Field ID"] = ""
    dup_idx = out_df.index[out_df.index.duplicated()].unique()
    unhandled_fields = [x for x in dup_idx if x not in ["650", "880"]]
    if "650" in dup_idx:
        str_add = out_df.loc["650", out_df.columns[0]].copy()
        str_add = [" " + str(x) for x in range(len(str_add))]
        out_df.loc["650", "Repeat Field ID"] = out_df.loc["650", out_df.columns[0]].str.split(" ").transform(
            lambda x: x[0]) + str_add
    if "880" in dup_idx:
        str_add = out_df.loc["880", out_df.columns[0]].copy()
        str_add = [" " + str(x) for x in range(len(str_add))]
        out_df.loc["880", "Repeat Field ID"] = out_df.loc["880", out_df.columns[0]].str.split("/").transform(
            lambda x: x[0]) + str_add
    for dup in unhandled_fields:
        out_df.loc[dup, "Repeat Field ID"] = [str(x) for x in range(len(out_df.loc[dup]))]

    return out_df.set_index("Repeat Field ID", append=True)


def add_subfield_rpt(df, field, split_chr, split_idx):
    repeat_id = [str(x) for x in range(len(df.loc[field:field]))]
    if repeat_id == ["0"]:  # TODO not assinging the subfield correctly for fields with only one repeat
        df.loc[field, "Subfield":"Subfield"] = df.loc[field, df.columns[0]:df.columns[0]].str.split(split_chr).transform(lambda x: x[split_idx])
    else:
        df.loc[field, "Subfield":"Subfield"] = df.loc[field, df.columns[0]].str.split(split_chr).transform(lambda x: x[split_idx])
    df.loc[field, "Rpt":"Rpt"] = repeat_id


def gen_sf_rpt_unique_idx(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate a unique index from one that contains repeated fields
    @param df: pd.DataFrame
    @return: pd.DataFrame
    """
    out_df = df.copy()
    out_df["Subfield"] = ""
    out_df["Rpt"] = ""
    dup_idx = out_df.index[out_df.index.duplicated()].unique()
    unhandled_fields = [x for x in dup_idx if x not in ["500", "650", "880"]]

    for field, split_chr, split_idx in zip(["500", "650", "880"], ["$", "$", "$"], [0, 0, 1]):
        if field in out_df.index:
            add_subfield_rpt(out_df, field, split_chr, split_idx)
    for dup in unhandled_fields:
        out_df.loc[dup, "Rpt"] = [str(x) for x in range(len(out_df.loc[dup]))]

    return out_df.set_index(["Subfield", "Rpt"], append=True)


def sort_fields_idx(index: pd.Index) -> pd.Index:
    """
    Specific keys to sort indices containing MARC fields
    @param index: pd.Index
    @return: pd.Index
    """
    if index.name == "Field":
        key = [0 if x == "LDR" else int(x) for x in index]
        return pd.Index(key)
    elif index.name == "Repeat Field ID":
        key = [x.split("$")[1] if "$" in x else x for x in index]
        return pd.Index(key)


def sort_sf_rpt_fields_idx(index):
    if index.name == "Field":
        key = [0 if x == "LDR" else int(x) for x in index]
        return pd.Index(key)
    elif index.name == "Subfield":
        key = [x.split("$")[1] if "$" in x else x for x in index]
        return pd.Index(key)
    elif index.name == "Rpt":
        return index


def simplify_6xx(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pandas magic
    Arbitrarily assinging repeat_id vals to repeat fields in records means common field values are not matched to each other
    Get round this by reindexing on an index of all unique values for a subfield
    Set the values for the reindexed subfield to the newly reindexed one.
    If there has been reordering this leaves rows of NA at the end of the subfield that can be dropped
    """
    if df.shape[1] == 1:
        return df
    elif "650" not in df.index:
        return df

    tidy_df = df.copy()
    subfields = tidy_df.loc["650"].index.get_level_values(0).unique()
    for sf in subfields:
        sf_orig = tidy_df.loc[("650", sf), :]
        sf_unique_vals = pd.Series(sf_orig.values.flatten()).dropna().unique()
        if len(sf_orig) < len(sf_unique_vals):
            continue
        sf_unique_df = pd.DataFrame(data=sf_unique_vals, columns=pd.Index(["unique_vals"]))
        for x in sf_orig.columns:
            sf_unique_df = sf_unique_df.merge(sf_orig[x], how="left", left_on="unique_vals", right_on=x)
        replacement_df = sf_unique_df.set_index(sf_orig.index[:len(sf_unique_df)]).reindex(sf_orig.index).drop(
            columns="unique_vals")
        replacement_df["Field"] = "650"
        replacement_df["Subfield"] = sf
        replacement_df = replacement_df.set_index(["Field", "Subfield"], append=True).reorder_levels([1, 2, 0])
        if not replacement_df.reset_index(drop=True).equals(sf_orig.reset_index(drop=True)):
            tidy_df.loc[("650", sf), :] = replacement_df
        else:  # No overlapping terms so flatten naively
            sf_orig_blank_idx = sf_orig.reset_index(drop=True)
            blank_idx_df = sf_orig.reset_index().drop(columns=sf_orig.columns)
            for x in sf_orig_blank_idx.columns:
                blank_idx_df = blank_idx_df.join(sf_orig_blank_idx[x].dropna().reset_index(drop=True))
            blank_idx_df["Field"] = "650"
            blank_idx_df["Subfield"] = sf
            replacement_df = blank_idx_df.set_index(["Field", "Subfield", "Rpt"])
            tidy_df.loc[("650", sf), :] = replacement_df
    return tidy_df


def filter_on_generic_fields(
        marc_df: pd.DataFrame,
        fields: Union[None, List[str]],
        terms: Union[None, List[str]],
        include_recs_without_field: bool
) -> pd.DataFrame:
    """
    Input the marc_table_df with all records
    sum all repeat columns and transpose to make searching easier
    Search each column in fields for the corresponding term in terms
    Return a df with only records that match the search terms
    @param marc_df:
    @param fields:
    @param terms:
    @param include_recs_without_field: bool
    @return: pd.DataFrame
    """
    if not fields or not terms:
        return marc_df

    t_df = marc_df.groupby(level=0).sum().T
    terms = [x.strip() for x in terms]
    filter_df = pd.concat([t_df[field].str.contains(term) for field, term in zip(fields, terms)], axis=1)
    if include_recs_without_field:
        df_filter = filter_df.all(axis=1)
    else:
        df_filter = filter_df.where(lambda x: ~x.isna(), False).all(axis=1)
    return marc_df.T[df_filter].T


def create_filter_columns(record_df: pd.DataFrame, lang_dict: Dict[str, str], search_au: str) -> pd.DataFrame:
    """
    Add cols to the dataframe of records (not the MARC df) that allow filtering and searching on certain params
    Cols params added are:
    has_title: has a 245 field
    has_author: has a 100 field
    cataloguing language: 040$b
    num_subject_access: # subject access fields (see field IDs below)
    num_rda: # RDA fields (see field IDs below)
    num_linked: # 880 fields
    has_phys_desc: has a 300 field
    good_encoding_level: 17th char in leader not one of 3, 5, 7
    record_length: total fields in record
    publication_date:
    @param record_df: pd.DataFrame
    @param lang_dict: Dict[str,str]
    @param search_au: str
    @return: pd.DataFrame
    """
    # title/author
    record_df["has_title"] = record_df["record"].apply(lambda x: bool(x.get_fields("245")))
    record_df["has_author"] = record_df["record"].apply(lambda x: bool(x.get_fields("100", "110", "111", "130")))
    au_exists = bool(search_au)
    record_df = record_df.query("has_title == True and (has_author == True or not @au_exists)")

    # lang
    re_040b = re.compile(r"\$b[a-z]+\$")
    record_df["language_040$b"] = record_df["record"].apply(
        lambda x: re_040b.search(x.get_fields("040")[0].__str__()).group())
    record_df["language"] = record_df["language_040$b"].str[2:-1].map(lang_dict["codes"])

    # subject access/RDA
    subject_access_fields = ["600", "610", "611", "630", "647", "648", "650", "651", "653", "654", "655", "656", "657",
                             "658", "662", "688"]
    rda_fields = ["264", "336", "337", "338", "344", "345", "346", "347"]
    record_df["num_subject_access"] = record_df["record"].apply(lambda x: len(x.get_fields(*subject_access_fields)))
    record_df["num_rda"] = record_df["record"].apply(lambda x: len(x.get_fields(*rda_fields)))

    # other
    record_df["num_linked"] = record_df["record"].apply(lambda x: len(x.get_fields("880")))
    record_df["has_phys_desc"] = record_df["record"].apply(lambda x: bool(x.get_fields("300")))
    record_df["good_encoding_level"] = record_df["record"].apply(lambda x: x.leader[17] not in [3, 5, 7])
    record_df["record_length"] = record_df["record"].apply(lambda x: len(x.get_fields()))
    record_df["publication_date"] = record_df["record"].apply(lambda x: get_pub_date(x))

    return record_df


def gen_gmap(row: pd.Series) -> pd.Series:
    """
    Map a row of values to a row of colours
    Colours are single numbers corresponding to (0, 0, X) in RGB (i.e. shades of blue)
    Values that appear repeatedly are coloured
    Unique values are marked as -10 and ignored when styling the dataframe (remain uncoloured)
    @param row: pd.Series (row of df)
    @return:
    """
    counts = row.value_counts()
    to_highlight = counts[counts > 1]
    no_highlight = counts[counts == 1]
    colour_vals = np.linspace(0, 1, len(to_highlight) + 2)[1:-1]
    mapping = {k: v for k, v in zip(to_highlight.index, colour_vals)}
    for val in no_highlight.index:
        mapping[val] = None
    return row.map(mapping, na_action='ignore')


def new_line(s):
    """
    Add line break before group and 1 trailing spaces
    @param s: re.group
    @return: str
    """
    return f"\n{s.group()} "


def gen_js(colour_mapping: Dict[str, str] = None) -> Union[Dict[str, str], JsCode]:
    """
    Generate a string that can be parsed by AG-Grid as a JS fn
    @param colour_mapping: Dict[str, str]
    @return: Dict[str, str]|streamlit-aggrid.JsCode
    """

    if not colour_mapping:
        return {'wordBreak': 'normal', 'whiteSpace': 'pre'}

    elif len(colour_mapping) == 1:
        for val, colour in colour_mapping.items():
            js_str = f"""
            function(params) {{
                 if (params.value === '{val}') {{
                    return {{'backgroundColor': '{colour}', 'wordBreak': 'normal', 'whiteSpace': 'pre'}}
                 }} else {{ 
                    return {{'wordBreak': 'normal', 'whiteSpace': 'pre'}}
                 }}
                }} 
            """
            return JsCode(js_str)

    elif len(colour_mapping) > 1:
        vals, colours = list(colour_mapping.keys()), list(colour_mapping.values())
        vals = [v.encode("unicode-escape").decode("utf-8") for v in vals]
        elif_conditions = []
        for v, c in zip(vals[1:], colours[1:]):
            js_str_part = f"""
            else if (params.value === '{v}') {{
            return {{'backgroundColor': '{c}', 'wordBreak': 'normal', 'whiteSpace': 'pre'}}
            }} """
            elif_conditions.append(js_str_part)

        js_str = f"""
        function(params) {{
             if (params.value === '{vals[0]}') {{
                return {{'backgroundColor': '{colours[0]}', 'wordBreak': 'normal', 'whiteSpace': 'pre'}}
             }} {"".join(elif_conditions)} else {{ 
                return {{'wordBreak': 'normal', 'whiteSpace': 'pre'}}
             }}
            }} 
        """
        return JsCode(js_str)


def to_hex_colour(blue_val):
    """
    Use mpl "Blues" colourmap to convert [0,1] to hex blues
    @param blue_val:
    @return:
    """
    if blue_val > 1:
        blue_val = 1
    cmap = colormaps["Blues"]
    r, g, b, a = cmap(blue_val, bytes=True)
    r_hex, g_hex, b_hex = hex(r)[2:], hex(g)[2:], hex(b)[2:]
    return f"#{r_hex}{g_hex}{b_hex}"


def gen_grid_options(df: pd.DataFrame, highlight_common_vals: bool, existing_match: int) -> Dict[str, str]:
    """
    Generate a dict to pass to gridOptions when calling AgGrid
    Makes AgGrid aware of line breaks using cellStyle
    Pins left two columns as index cols
    Applies highlighting for common values across rows using gmap and a custom JS function
    Highlights existing match using cellStyle
    Equivalent to previous style_marc_df fn
    @param df: pd.DataFrame
    @param highlight_common_vals: bool
    @param existing_match: int
    @return: Dict[str, str]
    """
    grid_builder = GridOptionsBuilder.from_dataframe(df)

    grid_builder.configure_columns(
        df.columns[2:], **{"cellStyle": {'wordBreak': 'normal', 'whiteSpace': 'pre'}, "autoHeight": True})
    grid_options = grid_builder.build()

    grid_options['columnDefs'][0]["pinned"] = 'left'
    grid_options['columnDefs'][1]["pinned"] = 'left'

    if highlight_common_vals:
        gmap = df.iloc[:, 2:].apply(gen_gmap, axis=1)
        gmap[1::3] += 0.03
        gmap[2::3] += 0.06

        for i, col_id in enumerate(gmap.columns):
            colour_mapping = {
                value: to_hex_colour(colour) for value, colour
                in zip(df[col_id].values, gmap[col_id].values)
                if colour and colour > -10
            }
            cell_style = gen_js(colour_mapping)
            grid_options['columnDefs'][i + 2].update({'cellStyle': cell_style})

    if isinstance(existing_match, int) and str(existing_match) in df.columns:
        col_idx = df.columns.get_loc(str(existing_match))
        grid_options['columnDefs'][col_idx].update(
            {"cellStyle": {'wordBreak': 'normal', 'whiteSpace': 'pre', "backgroundColor": "#2FD033A0"}}
        )

    return grid_options


def update_marc_table(table, df, highlight_button, existing_match):
    """
    Update the MARC table following
    @param table:
    @param df:
    @param highlight_button:
    @param existing_match:
    @return:
    """
    grid_options = gen_grid_options(
        df=df, highlight_common_vals=highlight_button, existing_match=existing_match
    )

    with table:
        ag = AgGrid(
            data=df,
            gridOptions=grid_options,
            allow_unsafe_jscode=True
        )
    return ag


def update_card_table(df: pd.DataFrame, subset: List[str], container: st.container) -> st.dataframe:
    """
    Update the card table at the top of the app
    This covers initial loading and updating once a record has been matched
    @param df: pd.DataFrame
    @param subset: List[str]
    @param container: st.container
    @return: st.dataframe
    """
    display_df = df.copy()
    display_df["selected_match_ocn"] = display_df["selected_match_ocn"].str.strip("ocn"
                                                                      ).str.strip("ocm"
                                                                      ).str.strip("on")
    existing_matches = display_df.dropna(subset="selected_match_ocn")
    oclc_matches = existing_matches.query("selected_match_ocn != 'No match'").index.values
    no_matches = existing_matches.query("selected_match_ocn == 'No match'").index.values
    select_event = container.dataframe(
        display_df.loc[:, subset].style.highlight_between(
            subset=pd.IndexSlice[oclc_matches, :], color='#d6f5d6'
        ).highlight_between(subset=pd.IndexSlice[no_matches, :], color='#edcd8c'),
        column_config={
            "card_id": "ID", "title": "Title", "author": "Author", "selected_match_ocn": "Selected OCLC #",
            "derivation_complete": "Derivation complete", "shelfmark": "Shelfmark", "lines": "OCR"
        },
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )

    return select_event


def push_to_storage(local: bool, save_file: str, df: pd.DataFrame, s3: s3fs.S3FileSystem) -> None:
    """
    Wrapper for updating and refreshing the cards_df and pushing data back to s3
    @param local: bool
    @param save_file: str
    @param df: pd.DataFrame
    @param s3: s3fs.S3FileSystem
    @return: None
    """
    if local:
        pickle.dump(df, open(save_file, "wb"))
    else:
        with s3.open(save_file, 'wb') as f:
            pickle.dump(df, f)
            st.cache_data.clear()  # Needed if pulling from S3

    return None
